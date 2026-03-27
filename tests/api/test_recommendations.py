from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_recommend_markers_success(client):
    llm_response = (
        '{"markers_detail": ['
        '{"marker": "CD3", "type": "Lineage", "reason": "Define T cells"}, '
        '{"marker": "CD8a", "type": "Lineage", "reason": "Resolve cytotoxic subset"}'
        "]}"
    )

    payload = {
        "experimental_goal": "Profile tumor-infiltrating T cells",
        "num_colors": 2,
        "inventory_file": "tests/fixtures/panel_inventory.csv",
    }

    with patch("llm_api_client.consult_gpt_oss", return_value=llm_response), patch(
        "panel_generator.consult_gpt_oss", return_value=llm_response
    ):
        resp = await client.post("/api/v1/recommendations/markers", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["selected_markers"] == ["CD3", "CD8a"]
    assert len(body["markers_detail"]) == 2


@pytest.mark.asyncio
async def test_recommend_markers_llm_error_returns_error_status(client):
    payload = {
        "experimental_goal": "Profile tumor-infiltrating T cells",
        "num_colors": 2,
        "inventory_file": "tests/fixtures/panel_inventory.csv",
    }

    with patch("llm_api_client.consult_gpt_oss", side_effect=RuntimeError("LLM down")), patch(
        "panel_generator.consult_gpt_oss", side_effect=RuntimeError("LLM down")
    ):
        resp = await client.post("/api/v1/recommendations/markers", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "error"
    assert "LLM recommendation failed" in body["message"]
