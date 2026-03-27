import pytest


@pytest.mark.asyncio
async def test_generate_panels_returns_unique_system_codes(client):
    payload = {
        "markers": ["CD3", "CD4", "CD8a"],
        "inventory_file": "tests/fixtures/panel_inventory.csv",
        "max_solutions": 5,
    }

    resp = await client.post("/api/v1/panels/generate", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "success"
    assert body["candidates"]

    for candidate in body["candidates"]:
        system_codes = [ab_info["system_code"] for ab_info in candidate.values()]
        assert len(system_codes) == len(set(system_codes))


@pytest.mark.asyncio
async def test_generate_panels_reports_missing_markers(client):
    payload = {
        "markers": ["CD3", "CD999"],
        "inventory_file": "tests/fixtures/panel_inventory.csv",
        "max_solutions": 3,
    }

    resp = await client.post("/api/v1/panels/generate", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "success"
    assert "CD999" in body["missing_markers"]
