"""Tests for quality context injection into evaluate_candidates_with_llm().

Verifies:
1. Quality context appears in prompt when projections exist
2. Quality context is absent when no projections exist
3. Quality context does not change candidate generation
4. evaluate_candidates_with_llm() survives quality context failures
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from backend.app.schemas.quality_registry import (
    EntityKey,
    QualityIssueCreate,
)
from backend.app.services.quality_registry_store import QualityRegistryStore
from backend.app.services.quality_projection import QualityProjector
from panel_generator import evaluate_candidates_with_llm, _build_quality_context_section


MOCK_LLM_RESPONSE = json.dumps({
    "selected_option_index": 1,
    "rationale": "Test rationale",
    "gating_detail": [],
})

CANDIDATE_A = {
    "CD3": {"fluorochrome": "PE", "system_code": "B", "brightness": 5},
    "CD4": {"fluorochrome": "APC", "system_code": "C", "brightness": 4},
}
CANDIDATE_B = {
    "CD3": {"fluorochrome": "FITC", "system_code": "A", "brightness": 3},
    "CD4": {"fluorochrome": "APC", "system_code": "C", "brightness": 4},
}
CANDIDATES = [CANDIDATE_A, CANDIDATE_B]


def _setup_store_with_issue(tmp_path):
    store = QualityRegistryStore(data_dir=str(tmp_path))
    projector = QualityProjector(store)

    entity_key = EntityKey(
        species="human",
        normalized_marker="cd3",
        clone="UCHT1",
        brand="BioLegend",
        catalog_number="CAT-001",
    )

    issue = store.create_issue(QualityIssueCreate(
        issue_text="High background staining observed",
        reported_by="tester",
        species="human",
        marker="CD3",
        fluorochrome="PE",
        brand="BioLegend",
        clone="UCHT1",
    ))
    store.bind_entity(issue.id, entity_key, "tester")
    projector.update_projection(issue.id)

    return store, projector


@patch("panel_generator.consult_gpt_oss", return_value=MOCK_LLM_RESPONSE)
def test_quality_context_present_when_projections_exist(mock_llm, tmp_path):
    store, projector = _setup_store_with_issue(tmp_path)

    with patch("panel_generator._quality_store", store), \
         patch("panel_generator._quality_projector", projector):
        result = evaluate_candidates_with_llm(CANDIDATES)

    assert result["status"] == "success"
    prompt_arg = mock_llm.call_args[0][0]
    assert "Antibody Quality Notes" in prompt_arg
    assert "High background staining observed" in prompt_arg
    # Quality notes must be advisory-only, not mandatory
    assert "auto-exclude" not in prompt_arg.lower() or "do NOT auto-exclude" in prompt_arg


@patch("panel_generator.consult_gpt_oss", return_value=MOCK_LLM_RESPONSE)
def test_quality_context_absent_when_no_projections(mock_llm, tmp_path):
    store = QualityRegistryStore(data_dir=str(tmp_path))
    projector = QualityProjector(store)

    with patch("panel_generator._quality_store", store), \
         patch("panel_generator._quality_projector", projector):
        result = evaluate_candidates_with_llm(CANDIDATES)

    assert result["status"] == "success"
    prompt_arg = mock_llm.call_args[0][0]
    assert "Antibody Quality Notes" not in prompt_arg


@patch("panel_generator.consult_gpt_oss", return_value=MOCK_LLM_RESPONSE)
def test_quality_context_does_not_change_candidate_generation(mock_llm, tmp_path):
    result_no_ctx = evaluate_candidates_with_llm(CANDIDATES)

    store, projector = _setup_store_with_issue(tmp_path)
    with patch("panel_generator._quality_store", store), \
         patch("panel_generator._quality_projector", projector):
        result_with_ctx = evaluate_candidates_with_llm(CANDIDATES)

    # Both should succeed and select the same panel (Option 1)
    assert result_no_ctx["status"] == "success"
    assert result_with_ctx["status"] == "success"
    assert result_no_ctx["selected_panel"] == result_with_ctx["selected_panel"]


@patch("panel_generator.consult_gpt_oss", return_value=MOCK_LLM_RESPONSE)
def test_quality_context_graceful_failure(mock_llm):
    with patch("panel_generator._build_quality_context_section", side_effect=RuntimeError("boom")):
        result = evaluate_candidates_with_llm(CANDIDATES)

    # _build_quality_context_section catches exceptions internally and returns ""
    # But if it somehow didn't, evaluate_candidates_with_llm should still work.
    # Since _build_quality_context_section has its own try/except, the side_effect
    # will be caught there. But let's also test the case where the helper itself
    # is patched to return "" (simulating a caught error).
    assert result["status"] == "success"


@patch("panel_generator.consult_gpt_oss", return_value=MOCK_LLM_RESPONSE)
def test_quality_context_graceful_failure_via_empty_return(mock_llm):
    with patch("panel_generator._build_quality_context_section", return_value=""):
        result = evaluate_candidates_with_llm(CANDIDATES)

    assert result["status"] == "success"
    prompt_arg = mock_llm.call_args[0][0]
    assert "Antibody Quality Notes" not in prompt_arg
