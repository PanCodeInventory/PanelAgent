"""Tests for the public (non-admin) /api/v1/settings endpoints.

LLM settings are now sourced purely from environment variables; the write
(PUT) path and the admin-mounted settings router have been removed.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_llm_settings_returns_env_default(client):
    resp = await client.get("/api/v1/settings/llm")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "env-default"
    assert isinstance(body["api_base"], str)
    assert len(body["api_base"]) > 0
    assert isinstance(body["model_name"], str)
    assert len(body["model_name"]) > 0
    assert body["has_api_key"] is True
    assert "lm-studio" not in body.get("api_key_masked", "")
    assert body["api_key_masked"] is not None


@pytest.mark.asyncio
async def test_put_llm_settings_does_not_exist(client):
    """The PUT route has been removed — must return 404/405."""
    resp = await client.put(
        "/api/v1/settings/llm",
        json={
            "api_base": "https://api.openai.com/v1",
            "model_name": "gpt-4o",
        },
    )
    assert resp.status_code in (404, 405)


@pytest.mark.asyncio
async def test_admin_llm_settings_router_removed(client):
    """The admin-mounted settings router no longer exists."""
    resp = await client.get("/api/v1/admin/settings/llm")
    assert resp.status_code in (404, 405)


@pytest.mark.asyncio
async def test_get_never_returns_raw_api_key(client):
    secret = "sk-super-secret-key-1234567890abcdef"
    resp = await client.get("/api/v1/settings/llm")
    assert resp.status_code == 200
    text = resp.text
    assert "sk-super-secret" not in text
    assert secret not in text


@pytest.mark.asyncio
async def test_list_providers_is_public(client):
    """GET /api/v1/settings/providers is not admin-gated."""
    resp = await client.get("/api/v1/settings/providers")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    ids = {p["id"] for p in body}
    assert {"lmstudio", "openai", "deepseek", "custom"}.issubset(ids)
