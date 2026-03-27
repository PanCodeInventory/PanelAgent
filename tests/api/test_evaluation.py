from unittest.mock import patch

import pytest


def _candidates_fixture():
    return [
        {
            "CD3": {
                "system_code": "APC-A",
                "fluorochrome": "APC",
                "brightness": 4,
                "clone": "17A2",
                "brand": "BioLegend",
                "catalog_number": "100235",
                "target": "CD3",
            },
            "CD8a": {
                "system_code": "PE-Cy7-A",
                "fluorochrome": "PE/Cyanine7",
                "brightness": 5,
                "clone": "53-6.7",
                "brand": "BioLegend",
                "catalog_number": "100721",
                "target": "CD8a",
            },
        },
        {
            "CD3": {
                "system_code": "APC-A",
                "fluorochrome": "APC",
                "brightness": 4,
                "clone": "17A2",
                "brand": "BioLegend",
                "catalog_number": "100235",
                "target": "CD3",
            },
            "CD8a": {
                "system_code": "BV510-A",
                "fluorochrome": "Brilliant Violet 510™",
                "brightness": 3,
                "clone": "53-6.7",
                "brand": "BioLegend",
                "catalog_number": "100752",
                "target": "CD8a",
            },
        },
    ]


@pytest.mark.asyncio
async def test_evaluate_panels_success(client):
    llm_response = (
        '{"selected_option_index": 2, '
        '"rationale": "Option 2 minimizes spillover for CD8a.", '
        '"gating_detail": [{"step": 1, "parent": "All Events", "axis": "FSC-A / SSC-A", '
        '"gate": "Polygon around lymphocytes", "population": "Lymphocytes"}]}'
    )

    payload = {
        "candidates": _candidates_fixture(),
        "missing_markers": ["CD19"],
    }

    with patch("llm_api_client.consult_gpt_oss", return_value=llm_response), patch(
        "panel_generator.consult_gpt_oss", return_value=llm_response
    ):
        resp = await client.post("/api/v1/panels/evaluate", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["selected_panel"]["CD8a"]["fluorochrome"] == "Brilliant Violet 510™"
    assert body["selected_panel"]["CD19"]["Note"] == "Not found in library"
    assert body["rationale"] == "Option 2 minimizes spillover for CD8a."
    assert len(body["gating_detail"]) == 1


@pytest.mark.asyncio
async def test_evaluate_panels_invalid_llm_output_falls_back_to_option_one(client):
    payload = {"candidates": _candidates_fixture(), "missing_markers": []}

    with patch("llm_api_client.consult_gpt_oss", return_value="garbage-output"), patch(
        "panel_generator.consult_gpt_oss", return_value="garbage-output"
    ):
        resp = await client.post("/api/v1/panels/evaluate", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["selected_panel"]["CD8a"]["fluorochrome"] == "PE/Cyanine7"
    assert body["rationale"] == "LLM output invalid. Shown Option 1."
    assert body["gating_detail"] == []


@pytest.mark.asyncio
async def test_evaluate_panels_llm_exception_returns_error(client):
    payload = {"candidates": _candidates_fixture(), "missing_markers": []}

    with patch("llm_api_client.consult_gpt_oss", side_effect=RuntimeError("LLM down")), patch(
        "panel_generator.consult_gpt_oss", side_effect=RuntimeError("LLM down")
    ):
        resp = await client.post("/api/v1/panels/evaluate", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "error"
    assert "LLM evaluation failed" in body["message"]
