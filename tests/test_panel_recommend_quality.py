"""Tests for quality context injection into recommend_markers_from_inventory().

Verifies:
1. Quality context appears in prompt when projections exist
2. Quality context is absent when no projections exist
3. Function survives quality context failures gracefully
4. Quality context does not change output format
"""

import json
from unittest.mock import patch

import pytest

from backend.app.schemas.quality_registry import (
    EntityKey,
    QualityIssueCreate,
)
from backend.app.services.quality_registry_store import QualityRegistryStore
from backend.app.services.quality_projection import QualityProjector
from panel_generator import recommend_markers_from_inventory


MOCK_LLM_RESPONSE = json.dumps({
    "markers_detail": [
        {"marker": "CD3", "type": "Lineage", "reason": "T cell identification"},
        {"marker": "CD4", "type": "Lineage", "reason": "Helper T cell subset"},
    ],
})

AVAILABLE_TARGETS = ["CD3", "CD4", "CD8", "CD45"]


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
def test_recommend_quality_context_present(mock_llm, tmp_path):
    """Quality context appears in prompt when projections exist."""
    store, projector = _setup_store_with_issue(tmp_path)

    with patch("panel_generator._quality_store", store), \
         patch("panel_generator._quality_projector", projector):
        result = recommend_markers_from_inventory("T cell panel", 5, AVAILABLE_TARGETS)

    assert result["status"] == "success"
    prompt_arg = mock_llm.call_args[0][0]
    assert "Antibody Quality Notes" in prompt_arg
    assert "High background staining observed" in prompt_arg
    assert "do NOT auto-exclude" in prompt_arg


@patch("panel_generator.consult_gpt_oss", return_value=MOCK_LLM_RESPONSE)
def test_recommend_quality_context_absent(mock_llm, tmp_path):
    """Quality context is absent when no projections exist."""
    store = QualityRegistryStore(data_dir=str(tmp_path))
    projector = QualityProjector(store)

    with patch("panel_generator._quality_store", store), \
         patch("panel_generator._quality_projector", projector):
        result = recommend_markers_from_inventory("T cell panel", 5, AVAILABLE_TARGETS)

    assert result["status"] == "success"
    prompt_arg = mock_llm.call_args[0][0]
    assert "Antibody Quality Notes" not in prompt_arg


@patch("panel_generator.consult_gpt_oss", return_value=MOCK_LLM_RESPONSE)
def test_recommend_quality_context_graceful_failure(mock_llm):
    """Function survives when _build_quality_context_section raises."""
    with patch("panel_generator._build_quality_context_section", side_effect=RuntimeError("boom")):
        result = recommend_markers_from_inventory("T cell panel", 5, AVAILABLE_TARGETS)

    assert result["status"] == "success"


@patch("panel_generator.consult_gpt_oss", return_value=MOCK_LLM_RESPONSE)
def test_recommend_quality_does_not_change_output_format(mock_llm, tmp_path):
    """Quality context is informational — same mock LLM = same output."""
    # Without quality context
    result_no_ctx = recommend_markers_from_inventory("T cell panel", 5, AVAILABLE_TARGETS)

    # With quality context
    store, projector = _setup_store_with_issue(tmp_path)
    with patch("panel_generator._quality_store", store), \
         patch("panel_generator._quality_projector", projector):
        result_with_ctx = recommend_markers_from_inventory("T cell panel", 5, AVAILABLE_TARGETS)

    # Both succeed with identical structure
    assert result_no_ctx["status"] == "success"
    assert result_with_ctx["status"] == "success"
    assert result_no_ctx["markers_detail"] == result_with_ctx["markers_detail"]
    assert result_no_ctx["selected_markers"] == result_with_ctx["selected_markers"]
