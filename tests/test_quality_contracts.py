"""Contract tests for the antibody quality registry dual-key schemas.

TDD: These tests define the expected behavior of all Pydantic schemas in
backend/app/schemas/quality_registry.py BEFORE implementation.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.app.schemas.quality_registry import (
    AntibodyQualityProjection,
    CandidateConfirmRequest,
    CandidateLookupRequest,
    CandidateLookupResponse,
    CandidateMatch,
    EntityKey,
    FeedbackKey,
    QualityIssueCreate,
    QualityIssueResponse,
    QualityPromptContext,
    ReviewItemResponse,
)


# ---------------------------------------------------------------------------
# 1. FeedbackKey normalisation
# ---------------------------------------------------------------------------


class TestFeedbackKeyNormalization:
    """Same marker with different casing/spacing/aliases produces same key."""

    def test_case_insensitive(self):
        k1 = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        k2 = FeedbackKey.from_submission("Human", "cd3", "FITC", "BioLegend")
        assert k1 == k2

    def test_dash_and_space_stripped(self):
        k1 = FeedbackKey.from_submission("Human", "CD-3", "FITC", "BioLegend")
        k2 = FeedbackKey.from_submission("Human", "CD 3", "FITC", "BioLegend")
        assert k1 == k2

    def test_parenthetical_removed(self):
        k1 = FeedbackKey.from_submission("Human", "CD96 (TACTILE)", "PE", "BioLegend")
        k2 = FeedbackKey.from_submission("Human", "CD96", "PE", "BioLegend")
        assert k1 == k2

    def test_suffix_stripped(self):
        """CD8a / CD8b should normalize to cd8."""
        k_a = FeedbackKey.from_submission("Human", "CD8a", "APC", "BioLegend")
        k_b = FeedbackKey.from_submission("Human", "CD8b", "APC", "BioLegend")
        k_plain = FeedbackKey.from_submission("Human", "CD8", "APC", "BioLegend")
        assert k_a == k_b
        assert k_a == k_plain


# ---------------------------------------------------------------------------
# 2. FeedbackKey clone optional
# ---------------------------------------------------------------------------


class TestFeedbackKeyCloneOptional:
    """Submission without clone produces a valid feedback key."""

    def test_without_clone(self):
        key = FeedbackKey.from_submission("Mouse", "CD4", "BV421", "Tonbo")
        assert key.clone is None
        # Should still be usable as a dict key
        d = {key: "value"}
        assert d[key] == "value"

    def test_with_clone(self):
        key = FeedbackKey.from_submission("Mouse", "CD4", "BV421", "Tonbo", clone="GK1.5")
        assert key.clone == "GK1.5"


# ---------------------------------------------------------------------------
# 3. EntityKey all required
# ---------------------------------------------------------------------------


class TestEntityKeyAllRequired:
    """Missing any required field raises ValidationError."""

    @pytest.mark.parametrize(
        "kwargs,missing",
        [
            ({"species": "Human", "normalized_marker": "cd3", "clone": "OKT3", "brand": "BioLegend"}, "catalog_number"),
            ({"species": "Human", "normalized_marker": "cd3", "clone": "OKT3", "catalog_number": "317326"}, "brand"),
            ({"species": "Human", "normalized_marker": "cd3", "brand": "BioLegend", "catalog_number": "317326"}, "clone"),
            ({"species": "Human", "clone": "OKT3", "brand": "BioLegend", "catalog_number": "317326"}, "normalized_marker"),
            ({"normalized_marker": "cd3", "clone": "OKT3", "brand": "BioLegend", "catalog_number": "317326"}, "species"),
        ],
    )
    def test_missing_field_raises(self, kwargs, missing):
        with pytest.raises(ValidationError, match=missing):
            EntityKey(**kwargs)


# ---------------------------------------------------------------------------
# 4. EntityKey lot metadata
# ---------------------------------------------------------------------------


class TestEntityKeyLotMetadata:
    """lot_number accepted but not part of equality."""

    def test_lot_not_in_equality(self):
        k1 = EntityKey(
            species="Human",
            normalized_marker="cd3",
            clone="OKT3",
            brand="BioLegend",
            catalog_number="317326",
            lot_number="LOT-A",
        )
        k2 = EntityKey(
            species="Human",
            normalized_marker="cd3",
            clone="OKT3",
            brand="BioLegend",
            catalog_number="317326",
            lot_number="LOT-B",
        )
        assert k1 == k2

    def test_lot_optional(self):
        k = EntityKey(
            species="Human",
            normalized_marker="cd3",
            clone="OKT3",
            brand="BioLegend",
            catalog_number="317326",
        )
        assert k.lot_number is None

    def test_from_antibody(self):
        k = EntityKey.from_antibody(
            species="Human", marker="CD3", clone="OKT3",
            brand="BioLegend", catalog="317326", lot="LOT-A",
        )
        assert k.normalized_marker == "cd3"
        assert k.lot_number == "LOT-A"


# ---------------------------------------------------------------------------
# 5. QualityIssueCreate validation
# ---------------------------------------------------------------------------


class TestQualityIssueCreateValidation:
    """blank issue_text, empty reported_by, missing species all rejected."""

    def test_blank_issue_text(self):
        with pytest.raises(ValidationError):
            QualityIssueCreate(
                issue_text="   ",
                reported_by="alice",
                species="Human",
                marker="CD3",
                fluorochrome="FITC",
                brand="BioLegend",
            )

    def test_empty_reported_by(self):
        with pytest.raises(ValidationError):
            QualityIssueCreate(
                issue_text="Some issue",
                reported_by="",
                species="Human",
                marker="CD3",
                fluorochrome="FITC",
                brand="BioLegend",
            )

    def test_missing_species(self):
        with pytest.raises(ValidationError):
            QualityIssueCreate(
                issue_text="Some issue",
                reported_by="alice",
                marker="CD3",
                fluorochrome="FITC",
                brand="BioLegend",
            )


# ---------------------------------------------------------------------------
# 6. QualityIssueCreate max length
# ---------------------------------------------------------------------------


class TestQualityIssueCreateMaxLength:
    """issue_text over 2000 chars rejected."""

    def test_over_2000(self):
        with pytest.raises(ValidationError):
            QualityIssueCreate(
                issue_text="x" * 2001,
                reported_by="alice",
                species="Human",
                marker="CD3",
                fluorochrome="FITC",
                brand="BioLegend",
            )

    def test_exactly_2000(self):
        issue = QualityIssueCreate(
            issue_text="x" * 2000,
            reported_by="alice",
            species="Human",
            marker="CD3",
            fluorochrome="FITC",
            brand="BioLegend",
        )
        assert len(issue.issue_text) == 2000


# ---------------------------------------------------------------------------
# 7. CandidateLookupResponse shape
# ---------------------------------------------------------------------------


class TestCandidateLookupResponseShape:
    """Verify response structure matches schema."""

    def test_structure(self):
        entity = EntityKey(
            species="Human", normalized_marker="cd3",
            clone="OKT3", brand="BioLegend", catalog_number="317326",
        )
        match = CandidateMatch(
            entity_key=entity, confidence=0.95,
            source="inventory", matched_marker="CD3",
        )
        resp = CandidateLookupResponse(candidates=[match])
        assert len(resp.candidates) == 1
        assert resp.candidates[0].confidence == 0.95
        assert resp.candidates[0].entity_key == entity


# ---------------------------------------------------------------------------
# 8. CandidateConfirm requires entity_key
# ---------------------------------------------------------------------------


class TestCandidateConfirmRequiresEntityKey:
    """Empty / missing entity_key rejected."""

    def test_missing_entity_key(self):
        with pytest.raises(ValidationError):
            CandidateConfirmRequest()

    def test_valid_confirm(self):
        entity = EntityKey(
            species="Human", normalized_marker="cd3",
            clone="OKT3", brand="BioLegend", catalog_number="317326",
        )
        req = CandidateConfirmRequest(entity_key=entity)
        assert req.entity_key == entity


# ---------------------------------------------------------------------------
# 9. Projection model shape
# ---------------------------------------------------------------------------


class TestProjectionModelShape:
    """Verify projection structure."""

    def test_shape(self):
        entity = EntityKey(
            species="Human", normalized_marker="cd3",
            clone="OKT3", brand="BioLegend", catalog_number="317326",
        )
        proj = AntibodyQualityProjection(
            entity_key=entity,
            issue_count=3,
            latest_issues=["bad staining", "lot failure", "weak signal"],
            aggregate_status="flagged",
        )
        assert proj.issue_count == 3
        assert len(proj.latest_issues) == 3
        assert proj.aggregate_status == "flagged"


# ---------------------------------------------------------------------------
# 10. PromptContext truncated flag
# ---------------------------------------------------------------------------


class TestPromptContextTruncatedFlag:
    """Verify truncated field exists."""

    def test_fields(self):
        ctx = QualityPromptContext(
            entries=["entry1", "entry2"],
            total_chars=100,
            truncated=False,
        )
        assert ctx.truncated is False
        assert ctx.total_chars == 100
        assert len(ctx.entries) == 2


# ---------------------------------------------------------------------------
# 11. FeedbackKey hashable
# ---------------------------------------------------------------------------


class TestFeedbackKeyHashable:
    """FeedbackKey works as dict key and in sets."""

    def test_dict_key(self):
        k1 = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        k2 = FeedbackKey.from_submission("Human", "CD4", "FITC", "BioLegend")
        d = {k1: "first", k2: "second"}
        assert d[k1] == "first"
        assert d[k2] == "second"

    def test_set_dedup(self):
        k1 = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        k2 = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        s = {k1, k2}
        assert len(s) == 1

    def test_clone_different_still_same_without_clone(self):
        """Two keys differing only by clone value should NOT be equal
        when both have clone set."""
        k_no = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        k_with = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend", clone="OKT3")
        assert k_no != k_with


# ---------------------------------------------------------------------------
# 12. EntityKey hashable
# ---------------------------------------------------------------------------


class TestEntityKeyHashable:
    """EntityKey works as dict key and in sets."""

    def test_dict_key(self):
        k1 = EntityKey(
            species="Human", normalized_marker="cd3",
            clone="OKT3", brand="BioLegend", catalog_number="317326",
        )
        k2 = EntityKey(
            species="Human", normalized_marker="cd4",
            clone="RPA-T4", brand="BioLegend", catalog_number="300530",
        )
        d = {k1: "first", k2: "second"}
        assert d[k1] == "first"

    def test_set_dedup(self):
        k1 = EntityKey(
            species="Human", normalized_marker="cd3",
            clone="OKT3", brand="BioLegend", catalog_number="317326",
        )
        k2 = EntityKey(
            species="Human", normalized_marker="cd3",
            clone="OKT3", brand="BioLegend", catalog_number="317326",
        )
        s = {k1, k2}
        assert len(s) == 1


# ---------------------------------------------------------------------------
# Bonus: ReviewItemResponse shape
# ---------------------------------------------------------------------------


class TestReviewItemResponseShape:
    def test_basic_shape(self):
        entity = EntityKey(
            species="Human", normalized_marker="cd3",
            clone="OKT3", brand="BioLegend", catalog_number="317326",
        )
        fb = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        now = datetime.now()
        item = ReviewItemResponse(
            id="abc123",
            feedback_key=fb,
            entity_key=entity,
            issue_text="bad staining",
            reported_by="alice",
            status="pending_review",
            created_at=now,
            updated_at=now,
        )
        assert item.status == "pending_review"
        assert item.reviewer is None
