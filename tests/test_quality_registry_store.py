"""TDD tests for QualityRegistryStore persistence layer.

Tests are written BEFORE implementation. Every test should initially FAIL,
then pass once the store is implemented correctly.
"""

from datetime import datetime, timezone

import pytest

from backend.app.schemas.quality_registry import (
    EntityKey,
    FeedbackKey,
    QualityIssueCreate,
)
from backend.app.services.quality_registry_store import AuditEvent, QualityRegistryStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_create(
    issue_text: str = "Staining intensity low",
    reported_by: str = "alice",
    species: str = "Human",
    marker: str = "CD3",
    fluorochrome: str = "FITC",
    brand: str = "BioLegend",
    clone: str | None = None,
) -> QualityIssueCreate:
    return QualityIssueCreate(
        issue_text=issue_text,
        reported_by=reported_by,
        species=species,
        marker=marker,
        fluorochrome=fluorochrome,
        brand=brand,
        clone=clone,
    )


def _make_entity(
    species: str = "Human",
    marker: str = "CD3",
    clone: str = "OKT3",
    brand: str = "BioLegend",
    catalog: str = "317326",
    lot: str | None = None,
) -> EntityKey:
    return EntityKey.from_antibody(
        species=species, marker=marker, clone=clone,
        brand=brand, catalog=catalog, lot=lot,
    )


# ---------------------------------------------------------------------------
# 1. Create issue returns response with id and timestamps
# ---------------------------------------------------------------------------


class TestCreateIssue:
    def test_create_issue_returns_response_with_id_and_timestamps(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        create = _make_create()
        result = store.create_issue(create)

        assert result.id  # non-empty string
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)
        assert result.created_at <= datetime.now(timezone.utc)
        assert result.updated_at <= datetime.now(timezone.utc)

    def test_create_issue_generates_feedback_key(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        create = _make_create(species="Human", marker="CD3", fluorochrome="FITC", brand="BioLegend", clone="OKT3")
        result = store.create_issue(create)

        expected_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend", clone="OKT3")
        assert result.feedback_key == expected_key

    def test_create_issue_creates_audit_event(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        create = _make_create()
        result = store.create_issue(create)

        history = store.get_history(result.id)
        assert len(history) >= 1
        assert history[0].action == "created"
        assert history[0].issue_id == result.id

    def test_create_issue_default_status_is_submitted(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        result = store.create_issue(_make_create())
        assert result.status == "submitted"

    def test_create_issue_entity_key_is_none_initially(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        result = store.create_issue(_make_create())
        assert result.entity_key is None

    def test_create_issue_preserves_fields(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        create = _make_create(issue_text="bad lot", reported_by="bob")
        result = store.create_issue(create)
        assert result.issue_text == "bad lot"
        assert result.reported_by == "bob"


# ---------------------------------------------------------------------------
# 2. Get issue
# ---------------------------------------------------------------------------


class TestGetIssue:
    def test_get_issue_returns_created_record(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        create = _make_create()
        created = store.create_issue(create)

        fetched = store.get_issue(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.issue_text == created.issue_text
        assert fetched.feedback_key == created.feedback_key

    def test_get_nonexistent_issue_returns_none(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        assert store.get_issue("nonexistent-id") is None


# ---------------------------------------------------------------------------
# 3. List issues
# ---------------------------------------------------------------------------


class TestListIssues:
    def test_list_issues_returns_all(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        store.create_issue(_make_create(marker="CD3"))
        store.create_issue(_make_create(marker="CD4"))
        store.create_issue(_make_create(marker="CD8"))

        all_issues = store.list_issues()
        assert len(all_issues) == 3

    def test_list_issues_filter_by_status(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        store.create_issue(_make_create(marker="CD3"))
        created2 = store.create_issue(_make_create(marker="CD4"))
        entity = _make_entity()
        store.bind_entity(created2.id, entity, confirmed_by="reviewer1")

        submitted = store.list_issues(status="submitted")
        confirmed = store.list_issues(status="confirmed")
        assert len(submitted) == 1
        assert len(confirmed) == 1

    def test_list_issues_filter_by_feedback_key(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        store.create_issue(_make_create(marker="CD3", fluorochrome="FITC"))
        store.create_issue(_make_create(marker="CD3", fluorochrome="PE"))

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        filtered = store.list_issues(feedback_key=fb_key)
        assert len(filtered) == 1
        assert filtered[0].feedback_key == fb_key

    def test_list_issues_empty_store(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        assert store.list_issues() == []

    def test_list_issues_combined_filters(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        store.create_issue(_make_create(marker="CD3"))
        created2 = store.create_issue(_make_create(marker="CD4"))
        entity = _make_entity(marker="CD4", clone="RPA-T4", catalog="300530")
        store.bind_entity(created2.id, entity, confirmed_by="reviewer1")

        fb_key = FeedbackKey.from_submission("Human", "CD4", "FITC", "BioLegend")
        confirmed_cd4 = store.list_issues(feedback_key=fb_key, status="confirmed")
        assert len(confirmed_cd4) == 1


# ---------------------------------------------------------------------------
# 4. Bind entity
# ---------------------------------------------------------------------------


class TestBindEntity:
    def test_bind_entity_updates_status(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        created = store.create_issue(_make_create())
        entity = _make_entity()

        result = store.bind_entity(created.id, entity, confirmed_by="reviewer1")
        assert result.status == "confirmed"
        assert result.entity_key == entity

    def test_bind_entity_creates_audit_event(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        created = store.create_issue(_make_create())
        entity = _make_entity()

        store.bind_entity(created.id, entity, confirmed_by="reviewer1")
        history = store.get_history(created.id)

        actions = [e.action for e in history]
        assert "entity_bound" in actions
        bound_event = [e for e in history if e.action == "entity_bound"][0]
        assert bound_event.actor == "reviewer1"

    def test_bind_entity_updates_persisted_record(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        created = store.create_issue(_make_create())
        entity = _make_entity()

        store.bind_entity(created.id, entity, confirmed_by="reviewer1")
        fetched = store.get_issue(created.id)
        assert fetched is not None
        assert fetched.status == "confirmed"
        assert fetched.entity_key == entity


# ---------------------------------------------------------------------------
# 5. Send to review
# ---------------------------------------------------------------------------


class TestSendToReview:
    def test_send_to_review_changes_status(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        created = store.create_issue(_make_create())
        entity = _make_entity()
        confirmed = store.bind_entity(created.id, entity, confirmed_by="reviewer1")

        result = store.send_to_review(confirmed.id)
        assert result.status == "pending_review"

    def test_send_to_review_creates_audit_event(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        created = store.create_issue(_make_create())
        entity = _make_entity()
        confirmed = store.bind_entity(created.id, entity, confirmed_by="reviewer1")

        store.send_to_review(confirmed.id)
        history = store.get_history(created.id)
        actions = [e.action for e in history]
        assert "status_changed" in actions


# ---------------------------------------------------------------------------
# 6. Resolve review
# ---------------------------------------------------------------------------


class TestResolveReview:
    def test_resolve_review_changes_status(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        created = store.create_issue(_make_create())
        entity = _make_entity()
        confirmed = store.bind_entity(created.id, entity, confirmed_by="reviewer1")
        pending = store.send_to_review(confirmed.id)

        result = store.resolve_review(pending.id, reviewer="dr_house")
        assert result.status == "resolved"

    def test_resolve_review_with_entity_key(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        created = store.create_issue(_make_create())
        entity = _make_entity()
        confirmed = store.bind_entity(created.id, entity, confirmed_by="reviewer1")
        pending = store.send_to_review(confirmed.id)

        new_entity = _make_entity(catalog="999999")
        result = store.resolve_review(pending.id, reviewer="dr_house", entity_key=new_entity)
        assert result.entity_key == new_entity

    def test_resolve_review_creates_audit_event(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        created = store.create_issue(_make_create())
        entity = _make_entity()
        confirmed = store.bind_entity(created.id, entity, confirmed_by="reviewer1")
        pending = store.send_to_review(confirmed.id)

        store.resolve_review(pending.id, reviewer="dr_house")
        history = store.get_history(created.id)
        actions = [e.action for e in history]
        assert "resolved" in actions


# ---------------------------------------------------------------------------
# 7. Audit history immutability
# ---------------------------------------------------------------------------


class TestAuditHistoryImmutability:
    def test_history_is_append_only(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        created = store.create_issue(_make_create())
        entity = _make_entity()

        h1 = store.get_history(created.id)
        assert len(h1) == 1

        store.bind_entity(created.id, entity, confirmed_by="reviewer1")
        h2 = store.get_history(created.id)
        assert len(h2) == 2

        store.send_to_review(created.id)
        h3 = store.get_history(created.id)
        assert len(h3) == 3

        store.resolve_review(created.id, reviewer="dr_house")
        h4 = store.get_history(created.id)
        assert len(h4) == 4

    def test_history_events_are_immutable(self, tmp_path):
        """Modifying returned audit event data has no effect on stored data."""
        store = QualityRegistryStore(data_dir=str(tmp_path))
        created = store.create_issue(_make_create())

        history = store.get_history(created.id)
        original_action = history[0].action
        original_details = dict(history[0].details)

        # Attempt to mutate the returned event
        history[0].details["tampered"] = True

        # Re-fetch and verify original data intact
        history2 = store.get_history(created.id)
        assert "tampered" not in history2[0].details
        assert history2[0].action == original_action


# ---------------------------------------------------------------------------
# 8. Audit event structure
# ---------------------------------------------------------------------------


class TestAuditEventStructure:
    def test_audit_event_has_required_fields(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        created = store.create_issue(_make_create())
        history = store.get_history(created.id)
        event = history[0]

        assert event.event_id  # non-empty
        assert event.issue_id == created.id
        assert event.action == "created"
        assert event.actor  # non-empty
        assert isinstance(event.details, dict)
        assert isinstance(event.timestamp, datetime)


# ---------------------------------------------------------------------------
# 9. Concurrent creates and edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_concurrent_create_same_feedback_key(self, tmp_path):
        """Two creates for same feedback key produce two different records."""
        store = QualityRegistryStore(data_dir=str(tmp_path))
        create = _make_create()

        r1 = store.create_issue(create)
        r2 = store.create_issue(create)

        assert r1.id != r2.id
        all_issues = store.list_issues()
        assert len(all_issues) == 2

    def test_bind_nonexistent_issue_raises(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        entity = _make_entity()

        with pytest.raises(Exception):
            store.bind_entity("nonexistent-id", entity, confirmed_by="reviewer1")

    def test_send_to_review_nonexistent_raises(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        with pytest.raises(Exception):
            store.send_to_review("nonexistent-id")

    def test_resolve_review_nonexistent_raises(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        with pytest.raises(Exception):
            store.resolve_review("nonexistent-id", reviewer="dr_house")

    def test_get_history_nonexistent_returns_empty(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        history = store.get_history("nonexistent-id")
        assert history == []

    def test_persisted_data_survives_store_recreation(self, tmp_path):
        """Data persists across store instances pointing at same dir."""
        store1 = QualityRegistryStore(data_dir=str(tmp_path))
        created = store1.create_issue(_make_create())

        store2 = QualityRegistryStore(data_dir=str(tmp_path))
        fetched = store2.get_issue(created.id)
        assert fetched is not None
        assert fetched.id == created.id
