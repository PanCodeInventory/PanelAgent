"""End-to-end integration tests for the antibody quality registry pipeline.

Tests the full backend flow without hitting real APIs or LLMs:
1. Issue → Projection → LLM context (happy path)
2. Issue → Projection → LLM context in evaluate_candidates_with_llm()
3. No-match flow → pending_review status
4. Deduplication in projection
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from backend.app.schemas.quality_registry import (
    AntibodyQualityProjection,
    EntityKey,
    FeedbackKey,
    QualityIssueCreate,
)
from backend.app.services.quality_context_formatter import (
    QUALITY_CONTEXT_HEADER,
    format_quality_context,
)
from backend.app.services.quality_projection import QualityProjector
from backend.app.services.quality_registry_store import QualityRegistryStore
from panel_generator import evaluate_candidates_with_llm


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

MOCK_LLM_RESPONSE = json.dumps({
    "selected_option_index": 1,
    "rationale": "Test rationale",
    "gating_detail": [],
})

CANDIDATE_A = {
    "CD3": {"fluorochrome": "PE", "system_code": "Y1_PE", "brightness": 5},
    "CD4": {"fluorochrome": "APC", "system_code": "R1_APC", "brightness": 4},
}
CANDIDATE_B = {
    "CD3": {"fluorochrome": "FITC", "system_code": "B1_FITC", "brightness": 3},
    "CD4": {"fluorochrome": "APC", "system_code": "R1_APC", "brightness": 4},
}
CANDIDATES = [CANDIDATE_A, CANDIDATE_B]


# ---------------------------------------------------------------------------
# Test 1: Issue → Projection → LLM Context (happy path)
# ---------------------------------------------------------------------------


class TestIssueProjectionLLMContext:
    """Full happy-path: create issue, verify projection, verify LLM context."""

    def test_issue_appears_in_projection_and_llm_context(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        # Create issue with full entity_key (known clone, brand, catalog)
        issue = store.create_issue(QualityIssueCreate(
            issue_text="High background staining observed",
            reported_by="tester",
            species="human",
            marker="CD3",
            fluorochrome="PE",
            brand="BioLegend",
            clone="UCHT1",
        ))

        entity_key = EntityKey(
            species="human",
            normalized_marker="cd3",
            clone="UCHT1",
            brand="BioLegend",
            catalog_number="CAT-001",
        )
        store.bind_entity(issue.id, entity_key, confirmed_by="tester")
        projector.update_projection(issue.id)

        # 1. Verify the issue appears in store.list_issues()
        all_issues = store.list_issues()
        assert len(all_issues) == 1
        assert all_issues[0].id == issue.id

        # 2. Verify projection exists via get_projections_for_markers
        projections = projector.get_projections_for_markers(["cd3"])
        assert len(projections) == 1

        proj = projections[0]
        # 3. Verify projection has entity_key bound (not None)
        assert proj.entity_key is not None
        assert proj.entity_key.normalized_marker == "cd3"
        assert proj.entity_key.clone == "UCHT1"
        assert proj.issue_count == 1
        assert "High background staining observed" in proj.latest_issues

        # 4. Verify format_quality_context produces context containing marker + issue
        schema_proj = AntibodyQualityProjection(
            entity_key=proj.entity_key,
            issue_count=proj.issue_count,
            latest_issues=proj.latest_issues,
            aggregate_status=proj.aggregate_status,
        )
        ctx = format_quality_context([schema_proj])

        assert ctx.total_chars > 0
        assert ctx.truncated is False
        full_text = QUALITY_CONTEXT_HEADER + "\n".join(ctx.entries)
        assert "cd3" in full_text
        assert "High background staining observed" in full_text


# ---------------------------------------------------------------------------
# Test 2: Issue → Projection → LLM context in evaluate_candidates_with_llm()
# ---------------------------------------------------------------------------


class TestEvaluateCandidatesWithLLMContext:
    """Verify quality context is injected into evaluate_candidates_with_llm()."""

    @patch("panel_generator.consult_gpt_oss", return_value=MOCK_LLM_RESPONSE)
    def test_llm_prompt_contains_quality_context_header(self, mock_llm, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        # Create issue for specific marker/fluorochrome/brand/clone
        issue = store.create_issue(QualityIssueCreate(
            issue_text="Weak staining signal on lot #2024-03",
            reported_by="researcher",
            species="human",
            marker="CD3",
            fluorochrome="PE",
            brand="BioLegend",
            clone="UCHT1",
        ))

        entity_key = EntityKey(
            species="human",
            normalized_marker="cd3",
            clone="UCHT1",
            brand="BioLegend",
            catalog_number="CAT-001",
        )
        store.bind_entity(issue.id, entity_key, confirmed_by="researcher")
        projector.update_projection(issue.id)

        # Patch module-level singletons
        with patch("panel_generator._quality_store", store), \
             patch("panel_generator._quality_projector", projector):
            result = evaluate_candidates_with_llm(CANDIDATES)

        assert result["status"] == "success"

        # Assert mock LLM received prompt containing quality context header
        prompt_arg = mock_llm.call_args[0][0]
        assert "Antibody Quality" in prompt_arg
        # Sanitization strips # chars, so the stored text "lot #2024-03"
        # becomes "lot 2024-03" in the formatted context
        assert "Weak staining signal on lot" in prompt_arg
        assert "2024-03" in prompt_arg

        # Assert prompt does NOT contain raw markdown injection characters
        # (sanitized via sanitize_for_markdown)
        assert "### ###" not in prompt_arg


# ---------------------------------------------------------------------------
# Test 3: No-match flow → pending_review status
# ---------------------------------------------------------------------------


class TestNoMatchFlowToPendingReview:
    """Issues without entity_key route to pending_review queue."""

    def test_no_entity_key_routes_to_pending_review(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        # Create issue WITHOUT entity_key (clone=None)
        issue = store.create_issue(QualityIssueCreate(
            issue_text="Unrecognized antibody with poor performance",
            reported_by="user_a",
            species="human",
            marker="CD3",
            fluorochrome="FITC",
            brand="UnknownBrand",
            clone=None,
        ))
        projector.update_projection(issue.id)

        # Verify issue appears in pending_review list
        pending = store.list_issues(status="submitted")
        assert len(pending) == 1
        assert pending[0].id == issue.id

        # Manually advance through the review flow:
        # bind_entity → confirmed, send_to_review → pending_review
        entity_key = EntityKey(
            species="human",
            normalized_marker="cd3",
            clone="OKT3",
            brand="UnknownBrand",
            catalog_number="CAT-NEW-001",
        )
        confirmed = store.bind_entity(issue.id, entity_key, confirmed_by="curator")
        assert confirmed.status == "confirmed"

        pending_review = store.send_to_review(confirmed.id)
        assert pending_review.status == "pending_review"

        # Verify list_issues filters by pending_review
        review_items = store.list_issues(status="pending_review")
        assert len(review_items) == 1
        assert review_items[0].id == issue.id

        # Resolve the review
        resolved = store.resolve_review(issue.id, reviewer="dr_reviewer")
        assert resolved.status == "resolved"

        # Verify the projection now has entity_key bound
        projector.update_projection(issue.id)
        proj = projector.get_projection(entity_key=entity_key)
        assert proj is not None
        assert proj.entity_key == entity_key


# ---------------------------------------------------------------------------
# Test 4: Deduplication in projection
# ---------------------------------------------------------------------------


class TestDeduplicationInProjection:
    """Duplicate issue texts collapse; distinct texts increment count."""

    def test_similar_issues_deduplicated_in_projection(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        entity_key = EntityKey(
            species="human",
            normalized_marker="cd3",
            clone="UCHT1",
            brand="BioLegend",
            catalog_number="CAT-001",
        )

        # Issue 1 & 2: same text after strip+lower
        i1 = store.create_issue(QualityIssueCreate(
            issue_text="  Low signal  ",
            reported_by="user1",
            species="human",
            marker="CD3",
            fluorochrome="PE",
            brand="BioLegend",
            clone="UCHT1",
        ))
        store.bind_entity(i1.id, entity_key, confirmed_by="system")
        projector.update_projection(i1.id)

        i2 = store.create_issue(QualityIssueCreate(
            issue_text="low signal",
            reported_by="user2",
            species="human",
            marker="CD3",
            fluorochrome="PE",
            brand="BioLegend",
            clone="UCHT1",
        ))
        store.bind_entity(i2.id, entity_key, confirmed_by="system")
        projector.update_projection(i2.id)

        # Both map to same entity_key, so they share a projection
        proj = projector.get_projection(entity_key=entity_key)
        assert proj is not None
        # Deduplicated: same text after strip+lower → count is 1
        assert proj.issue_count == 1

        # Issue 3: DIFFERENT text
        i3 = store.create_issue(QualityIssueCreate(
            issue_text="High background",
            reported_by="user3",
            species="human",
            marker="CD3",
            fluorochrome="PE",
            brand="BioLegend",
            clone="UCHT1",
        ))
        store.bind_entity(i3.id, entity_key, confirmed_by="system")
        projector.update_projection(i3.id)

        proj = projector.get_projection(entity_key=entity_key)
        assert proj is not None
        # Now 2 distinct issues: "Low signal" (deduped) and "High background"
        assert proj.issue_count == 2
