"""Tests for /api/v1/health endpoint."""

import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    """GET /api/v1/health should return 200 with status ok."""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"] == "1.0.0"
