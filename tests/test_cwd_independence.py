"""
Cross-flow CWD-independence regression tests.

These tests verify that the full API flow (panels generate, recommendations, evaluation)
works correctly when pytest is executed from a non-project-root working directory.

The key insight is that when CWD is changed to /tmp, the API should still work because:
1. panel_generator.py now uses resolve_static_data_path() for absolute paths
2. Endpoints use project_root() and resolve_static_data_path() for absolute paths
3. Test fixtures use resolve_static_data_path() for absolute paths

This is a regression test to ensure future changes don't break CWD independence.
"""

from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.app.main import app


@pytest_asyncio.fixture
async def client():
    """ASGI test client for API endpoint testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _candidates_fixture():
    """Return test candidates data for evaluation endpoint."""
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
        }
    ]


@pytest.mark.asyncio
async def test_api_panels_generate_from_nonroot_cwd(client, monkeypatch, tmp_path):
    """
    Test /api/v1/panels/generate from non-root CWD.

    This test verifies that the panels generation endpoint works correctly
    even when the current working directory is changed to /tmp.
    """
    llm_response = (
        '{"candidates": ['
        '{"CD3": {"system_code": "APC-A", "fluorochrome": "APC", "brightness": 4, '
        '"clone": "17A2", "brand": "BioLegend", "catalog_number": "100235", "target": "CD3"}}'
        '], "missing_markers": []}'
    )

    payload = {
        "markers": ["CD3", "CD4"],
        "inventory_file": "panel_inventory.csv",
        "max_solutions": 3,
    }

    # Change CWD to tmp_path (simulating /tmp)
    monkeypatch.chdir(tmp_path)

    # Verify CWD is actually changed
    import os
    assert os.getcwd() == str(tmp_path), "CWD should be changed to tmp_path"

    # Mock LLM calls to prevent network dependencies
    with patch("llm_api_client.consult_gpt_oss", return_value=llm_response), \
         patch("panel_generator.consult_gpt_oss", return_value=llm_response):
        resp = await client.post("/api/v1/panels/generate", json=payload)

    # Verify successful response
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["candidates"]
    assert len(body["candidates"]) > 0


@pytest.mark.asyncio
async def test_api_recommendations_from_nonroot_cwd(client, monkeypatch, tmp_path):
    """
    Test /api/v1/recommendations/markers from non-root CWD.

    This test verifies that the recommendations endpoint works correctly
    even when the current working directory is changed to /tmp.
    """
    llm_response = (
        '{"markers_detail": ['
        '{"marker": "CD3", "type": "Lineage", "reason": "Define T cells"}, '
        '{"marker": "CD8a", "type": "Lineage", "reason": "Resolve cytotoxic subset"}'
        "]}"
    )

    payload = {
        "experimental_goal": "test",
        "num_colors": 2,
        "inventory_file": "panel_inventory.csv",
    }

    # Change CWD to tmp_path (simulating /tmp)
    monkeypatch.chdir(tmp_path)

    # Verify CWD is actually changed
    import os
    assert os.getcwd() == str(tmp_path), "CWD should be changed to tmp_path"

    # Mock LLM calls to prevent network dependencies
    with patch("llm_api_client.consult_gpt_oss", return_value=llm_response), \
         patch("panel_generator.consult_gpt_oss", return_value=llm_response):
        resp = await client.post("/api/v1/recommendations/markers", json=payload)

    # Verify successful response
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["selected_markers"] == ["CD3", "CD8a"]
    assert len(body["markers_detail"]) == 2


@pytest.mark.asyncio
async def test_api_evaluation_from_nonroot_cwd(client, monkeypatch, tmp_path):
    """
    Test /api/v1/panels/evaluate from non-root CWD.

    This test verifies that the evaluation endpoint works correctly
    even when the current working directory is changed to /tmp.
    """
    llm_response = (
        '{"selected_option_index": 0, '
        '"rationale": "Option 1 is optimal.", '
        '"gating_detail": []}'
    )

    payload = {
        "candidates": _candidates_fixture(),
        "missing_markers": [],
    }

    # Change CWD to tmp_path (simulating /tmp)
    monkeypatch.chdir(tmp_path)

    # Verify CWD is actually changed
    import os
    assert os.getcwd() == str(tmp_path), "CWD should be changed to tmp_path"

    # Mock LLM calls to prevent network dependencies
    with patch("llm_api_client.consult_gpt_oss", return_value=llm_response), \
         patch("panel_generator.consult_gpt_oss", return_value=llm_response):
        resp = await client.post("/api/v1/panels/evaluate", json=payload)

    # Verify successful response
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["selected_panel"]["CD3"]["fluorochrome"] == "APC"
    assert body["rationale"] == "Option 1 is optimal."
    assert body["gating_detail"] == []
