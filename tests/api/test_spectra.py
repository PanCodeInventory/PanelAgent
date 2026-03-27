"""Tests for POST /api/v1/spectra/render-data endpoint."""

import pytest


@pytest.mark.asyncio
async def test_render_spectra_known_fluorochromes(client):
    """Happy path: FITC, PE, APC should return series with correct peaks."""
    payload = {
        "fluorochromes": ["FITC", "PE", "APC"],
    }
    resp = await client.post("/api/v1/spectra/render-data", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "success"
    assert len(body["series"]) == 3
    assert body["warnings"] == []

    # Verify series structure
    peaks = {s["fluorochrome"]: s["peak"] for s in body["series"]}
    assert peaks["FITC"] == 519
    assert peaks["PE"] == 575
    assert peaks["APC"] == 660

    # Verify x/y data shape matches linspace(350, 900, 550)
    for s in body["series"]:
        assert len(s["x"]) == 550
        assert len(s["y"]) == 550
        assert s["x"][0] == pytest.approx(350.0, abs=0.01)
        assert s["x"][-1] == pytest.approx(900.0, abs=0.01)
        # Peak normalized to 100
        assert max(s["y"]) == pytest.approx(100.0, abs=0.01)


@pytest.mark.asyncio
async def test_render_spectra_unknown_fluorochrome(client):
    """Edge case: unknown fluorochrome should appear in warnings, not crash."""
    payload = {
        "fluorochromes": ["FITC", "NOT_A_REAL_DYE"],
    }
    resp = await client.post("/api/v1/spectra/render-data", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "success"
    assert len(body["series"]) == 1
    assert body["series"][0]["fluorochrome"] == "FITC"
    assert any("NOT_A_REAL_DYE" in w for w in body["warnings"])


@pytest.mark.asyncio
async def test_render_spectra_empty_list(client):
    """Edge case: empty fluorochrome list returns success with no series."""
    payload = {
        "fluorochromes": [],
    }
    resp = await client.post("/api/v1/spectra/render-data", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "success"
    assert body["series"] == []
    assert body["warnings"] == []
    assert body["message"] is not None


@pytest.mark.asyncio
async def test_render_spectra_all_unknown(client):
    """Edge case: all unknown fluorochromes returns error status."""
    payload = {
        "fluorochromes": ["GHOST_DYE_1", "GHOST_DYE_2"],
    }
    resp = await client.post("/api/v1/spectra/render-data", json=payload)
    assert resp.status_code == 400

    body = resp.json()
    assert body["detail"] == "No valid fluorochromes found in request."


@pytest.mark.asyncio
async def test_render_spectra_case_insensitive(client):
    """Case-insensitive match should work (e.g., 'fitc' resolves to FITC data)."""
    payload = {
        "fluorochromes": ["fitc"],
    }
    resp = await client.post("/api/v1/spectra/render-data", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "success"
    assert len(body["series"]) == 1
    assert body["series"][0]["peak"] == 519
    assert body["series"][0]["color"] == "#00FF00"


@pytest.mark.asyncio
async def test_render_spectra_gaussian_peak_at_100(client):
    """Verify the Gaussian peak value is exactly 100 for a known fluorochrome."""
    payload = {
        "fluorochromes": ["PE"],
    }
    resp = await client.post("/api/v1/spectra/render-data", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    s = body["series"][0]
    peak_idx = s["y"].index(max(s["y"]))
    assert s["y"][peak_idx] == pytest.approx(100.0, abs=0.01)
    assert s["x"][peak_idx] == pytest.approx(575.0, abs=1.0)


@pytest.mark.asyncio
async def test_render_spectra_includes_color_metadata(client):
    """Each series must include color and category from spectral_data.json."""
    payload = {
        "fluorochromes": ["APC", "BV421"],
    }
    resp = await client.post("/api/v1/spectra/render-data", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    meta = {s["fluorochrome"]: s for s in body["series"]}
    assert meta["APC"]["color"] == "#FF0000"
    assert meta["APC"]["category"] == "Red Laser"
    assert meta["BV421"]["color"] == "#8A2BE2"
    assert meta["BV421"]["category"] == "Violet Laser"
