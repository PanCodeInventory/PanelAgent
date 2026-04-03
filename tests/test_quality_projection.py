"""TDD tests for QualityProjector — incremental antibody-level projections.

Tests written FIRST, before implementation. Every test should initially FAIL,
then pass once the projector is implemented correctly.
"""

from datetime import datetime, timezone

import pytest

from backend.app.schemas.quality_registry import (
    EntityKey,
    FeedbackKey,
    QualityIssueCreate,
)
from backend.app.services.quality_projection import ProjectionRecord, QualityProjector
from backend.app.services.quality_registry_store import QualityRegistryStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_create(**kwargs) -> QualityIssueCreate:
    defaults = dict(
        issue_text="Staining intensity low",
        reported_by="alice",
        species="Human",
        marker="CD3",
        fluorochrome="FITC",
        brand="BioLegend",
        clone=None,
    )
    defaults.update(kwargs)
    return QualityIssueCreate(**defaults)


def _make_entity(**kwargs) -> EntityKey:
    defaults = dict(
        species="Human",
        marker="CD3",
        clone="OKT3",
        brand="BioLegend",
        catalog="317326",
        lot=None,
    )
    defaults.update(kwargs)
    return EntityKey.from_antibody(**defaults)


# ---------------------------------------------------------------------------
# 1. Projection created on issue save
# ---------------------------------------------------------------------------


class TestProjectionOnSave:
    def test_projection_created_on_issue_save(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)
        issue = store.create_issue(_make_create())

        proj = projector.update_projection(issue.id)

        assert proj is not None
        assert proj.issue_count == 1
        assert len(proj.latest_issues) == 1


# ---------------------------------------------------------------------------
# 2. Projection updated on bind
# ---------------------------------------------------------------------------


class TestProjectionOnBind:
    def test_projection_updated_on_bind(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)
        issue = store.create_issue(_make_create())
        projector.update_projection(issue.id)

        entity = _make_entity()
        store.bind_entity(issue.id, entity, confirmed_by="reviewer1")
        proj = projector.update_projection(issue.id)

        assert proj is not None
        assert proj.entity_key == entity
        assert proj.issue_count == 1


# ---------------------------------------------------------------------------
# 3. Issue count increments
# ---------------------------------------------------------------------------


class TestIssueCountIncrements:
    def test_projection_issue_count_increments(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        i1 = store.create_issue(_make_create(issue_text="Low signal"))
        projector.update_projection(i1.id)
        i2 = store.create_issue(_make_create(issue_text="High background"))
        projector.update_projection(i2.id)
        i3 = store.create_issue(_make_create(issue_text="Lot variation"))
        projector.update_projection(i3.id)

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        proj = projector.get_projection(feedback_key=fb_key)

        assert proj is not None
        assert proj.issue_count == 3


# ---------------------------------------------------------------------------
# 4. Deduplication of identical issues
# ---------------------------------------------------------------------------


class TestDedupIdentical:
    def test_projection_dedup_identical_issues(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        store.create_issue(_make_create(issue_text="  Low signal  "))
        i1 = store.create_issue(_make_create(issue_text="low signal"))
        # Different casing and whitespace should collapse
        i3 = store.create_issue(_make_create(issue_text="DIFFERENT issue"))
        projector.update_projection(i1.id)
        # Update with last issue to trigger recompute
        projector.update_projection(i3.id)

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        proj = projector.get_projection(feedback_key=fb_key)

        assert proj is not None
        assert proj.issue_count == 2  # 2 unique after dedup
        assert proj.dedup_count == 1  # 1 was collapsed


# ---------------------------------------------------------------------------
# 5. Dedup keeps earliest
# ---------------------------------------------------------------------------


class TestDedupKeepsEarliest:
    def test_projection_dedup_keeps_earliest(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        i1 = store.create_issue(_make_create(issue_text="Same problem"))
        i2 = store.create_issue(_make_create(issue_text="  same problem  "))
        projector.update_projection(i2.id)

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        proj = projector.get_projection(feedback_key=fb_key)

        assert proj is not None
        assert proj.issue_count == 1
        # Should keep i1's text (the earliest) since they collapse
        assert "Same problem" in proj.latest_issues


# ---------------------------------------------------------------------------
# 6. Stable ordering
# ---------------------------------------------------------------------------


class TestStableOrdering:
    def test_projection_stable_ordering(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        # Create issues in specific order
        i1 = store.create_issue(_make_create(issue_text="First issue"))
        i2 = store.create_issue(_make_create(issue_text="Second issue"))
        i3 = store.create_issue(_make_create(issue_text="Third issue"))
        projector.update_projection(i3.id)

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        proj = projector.get_projection(feedback_key=fb_key)

        assert proj is not None
        # latest_issues should be in created_at ascending order
        assert proj.latest_issues == ["First issue", "Second issue", "Third issue"]


# ---------------------------------------------------------------------------
# 7. Top 5 latest issues
# ---------------------------------------------------------------------------


class TestLatestTopFive:
    def test_projection_latest_issues_top_5(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        ids = []
        for i in range(7):
            issue = store.create_issue(_make_create(issue_text=f"Issue number {i}"))
            ids.append(issue.id)

        # Trigger projection via last issue
        projector.update_projection(ids[-1])

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        proj = projector.get_projection(feedback_key=fb_key)

        assert proj is not None
        assert proj.issue_count == 7
        assert len(proj.latest_issues) == 5
        # Should keep the 5 most recent (issues 2-6 in ascending order)
        assert proj.latest_issues == [
            "Issue number 2",
            "Issue number 3",
            "Issue number 4",
            "Issue number 5",
            "Issue number 6",
        ]


# ---------------------------------------------------------------------------
# 8. Get projection by entity_key
# ---------------------------------------------------------------------------


class TestGetByEntityKey:
    def test_get_projection_by_entity_key(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        issue = store.create_issue(_make_create())
        entity = _make_entity()
        store.bind_entity(issue.id, entity, confirmed_by="reviewer1")
        projector.update_projection(issue.id)

        proj = projector.get_projection(entity_key=entity)

        assert proj is not None
        assert proj.entity_key == entity
        assert proj.issue_count == 1


# ---------------------------------------------------------------------------
# 9. Get projection by feedback_key
# ---------------------------------------------------------------------------


class TestGetByFeedbackKey:
    def test_get_projection_by_feedback_key(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        issue = store.create_issue(_make_create())
        projector.update_projection(issue.id)

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        proj = projector.get_projection(feedback_key=fb_key)

        assert proj is not None
        assert proj.feedback_key == fb_key
        assert proj.entity_key is None


# ---------------------------------------------------------------------------
# 10. Nonexistent returns None
# ---------------------------------------------------------------------------


class TestGetNonexistent:
    def test_get_projection_nonexistent_returns_none(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        entity = _make_entity()
        assert projector.get_projection(entity_key=entity) is None

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        assert projector.get_projection(feedback_key=fb_key) is None


# ---------------------------------------------------------------------------
# 11. Get projections for markers — filter
# ---------------------------------------------------------------------------


class TestGetForMarkersFilter:
    def test_get_projections_for_markers_filters_correctly(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        # Create issues for CD3 and CD4
        i1 = store.create_issue(_make_create(marker="CD3", issue_text="CD3 issue"))
        projector.update_projection(i1.id)
        i2 = store.create_issue(_make_create(marker="CD4", issue_text="CD4 issue"))
        projector.update_projection(i2.id)

        # Should only get CD3 projection
        results = projector.get_projections_for_markers(["cd3"])

        assert len(results) == 1
        assert results[0].issue_count == 1


# ---------------------------------------------------------------------------
# 12. Get projections for markers — sorted by count
# ---------------------------------------------------------------------------


class TestGetForMarkersSortedByCount:
    def test_get_projections_for_markers_sorted_by_count(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        # CD3: 1 issue
        i1 = store.create_issue(_make_create(marker="CD3", issue_text="CD3 issue"))
        projector.update_projection(i1.id)

        # CD4: 3 issues
        for idx in range(3):
            issue = store.create_issue(
                _make_create(marker="CD4", issue_text=f"CD4 issue {idx}")
            )
            projector.update_projection(issue.id)

        results = projector.get_projections_for_markers(["cd3", "cd4"])

        assert len(results) == 2
        # Most problematic first (CD4 has 3, CD3 has 1)
        assert results[0].feedback_key is not None
        assert results[0].feedback_key.normalized_marker == "cd4"
        assert results[0].issue_count == 3
        assert results[1].feedback_key is not None
        assert results[1].feedback_key.normalized_marker == "cd3"
        assert results[1].issue_count == 1


# ---------------------------------------------------------------------------
# 13. Projection survives store recreation
# ---------------------------------------------------------------------------


class TestProjectionPersistence:
    def test_projection_survives_store_recreation(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector1 = QualityProjector(store)

        issue = store.create_issue(_make_create())
        proj1 = projector1.update_projection(issue.id)

        # Create a new projector pointing at the same data dir
        projector2 = QualityProjector(store)
        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        proj2 = projector2.get_projection(feedback_key=fb_key)

        assert proj2 is not None
        assert proj2.issue_count == proj1.issue_count
        assert proj2.latest_issues == proj1.latest_issues


# ---------------------------------------------------------------------------
# 14. Unbound issues separate from bound
# ---------------------------------------------------------------------------


class TestUnboundSeparateFromBound:
    def test_unbound_issues_separate_from_bound(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        # Issue A: stays unbound
        issue_a = store.create_issue(_make_create(issue_text="Unbound issue"))
        projector.update_projection(issue_a.id)

        # Issue B: gets bound to entity
        issue_b = store.create_issue(_make_create(issue_text="Bound issue"))
        entity = _make_entity()
        store.bind_entity(issue_b.id, entity, confirmed_by="reviewer1")
        projector.update_projection(issue_b.id)

        # Entity projection: should only have issue B
        entity_proj = projector.get_projection(entity_key=entity)
        assert entity_proj is not None
        assert entity_proj.issue_count == 1
        assert entity_proj.entity_key == entity

        # Feedback projection: should only have issue A (unbound)
        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        fb_proj = projector.get_projection(feedback_key=fb_key)
        assert fb_proj is not None
        assert fb_proj.issue_count == 1
        assert fb_proj.entity_key is None
        assert "Unbound issue" in fb_proj.latest_issues


# ---------------------------------------------------------------------------
# 15. Resolve status updates aggregate
# ---------------------------------------------------------------------------


class TestResolveStatusUpdatesAggregate:
    def test_resolve_status_updates_aggregate_status(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        # Create issue → should be flagged
        issue = store.create_issue(_make_create(issue_text="Problem"))
        proj = projector.update_projection(issue.id)
        assert proj.aggregate_status == "flagged"

        # Bind + send to review + resolve → should be clean
        entity = _make_entity()
        store.bind_entity(issue.id, entity, confirmed_by="rev1")
        store.send_to_review(issue.id)
        store.resolve_review(issue.id, reviewer="dr_house")
        proj = projector.update_projection(issue.id)

        assert proj.aggregate_status == "clean"
