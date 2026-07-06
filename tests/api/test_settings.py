"""Tests for protected /api/v1/admin/settings/llm endpoints."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.services.admin_database import get_db_path, init_db

TEST_PASSWORD = "test-secret-password-123"
SESSION_SECRET = "test-session-secret-for-tests-only"


@pytest.fixture(autouse=True)
def _set_admin_env(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", TEST_PASSWORD)
    monkeypatch.setenv("ADMIN_SESSION_SECRET", SESSION_SECRET)


@pytest.fixture()
def tmp_db(tmp_path: Path):
    db_file = tmp_path / "test_admin.sqlite3"
    # Use init_db so the table schema (including the provider column) matches
    # production exactly, rather than re-declaring DDL here.
    init_db(str(db_file))
    return str(db_file)


@pytest_asyncio.fixture()
async def client(tmp_db: str):
    with patch("backend.app.api.v1.endpoints.settings._store") as mock_store_factory:
        from backend.app.services.llm_settings_store import LlmSettingsStore

        store_instance = LlmSettingsStore(db_path=tmp_db)
        mock_store_factory.return_value = store_instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


async def _admin_cookie(client: AsyncClient) -> dict[str, str]:
    resp = await client.post("/api/v1/admin/auth/login", json={"password": TEST_PASSWORD})
    assert resp.status_code == 200
    session_cookie = resp.cookies.get("panelagent_admin_session")
    assert session_cookie is not None
    return {"panelagent_admin_session": session_cookie}


@pytest.mark.asyncio
async def test_get_llm_settings_requires_admin_auth(client):
    resp = await client.get("/api/v1/admin/settings/llm")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_llm_settings_env_default(client):
    resp = await client.get("/api/v1/admin/settings/llm", cookies=await _admin_cookie(client))
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
async def test_put_llm_settings_full_update(client):
    admin_cookies = await _admin_cookie(client)
    resp = await client.put(
        "/api/v1/admin/settings/llm",
        json={
            "api_base": "https://api.openai.com/v1",
            "model_name": "gpt-4o",
            "api_key": "sk-abcdefghijklmnop1234567890",
        },
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "runtime"
    assert body["api_base"] == "https://api.openai.com/v1"
    assert body["model_name"] == "gpt-4o"
    assert body["has_api_key"] is True
    assert "sk-" in body["api_key_masked"]
    assert "7890" in body["api_key_masked"]
    assert "****" in body["api_key_masked"]


@pytest.mark.asyncio
async def test_put_partial_update_preserves_existing(client):
    admin_cookies = await _admin_cookie(client)
    await client.put(
        "/api/v1/admin/settings/llm",
        json={
            "api_base": "https://api.openai.com/v1",
            "model_name": "gpt-4o",
            "api_key": "sk-abcdefghijklmnop1234567890",
        },
        cookies=admin_cookies,
    )

    resp = await client.put(
        "/api/v1/admin/settings/llm",
        json={"api_base": "https://custom.api.com/v1"},
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["api_base"] == "https://custom.api.com/v1"
    assert body["model_name"] == "gpt-4o"
    assert body["has_api_key"] is True


@pytest.mark.asyncio
async def test_put_empty_api_key_clears_stored_key(client):
    admin_cookies = await _admin_cookie(client)
    await client.put(
        "/api/v1/admin/settings/llm",
        json={"api_key": "sk-some-long-key-here-123456"},
        cookies=admin_cookies,
    )

    resp = await client.put(
        "/api/v1/admin/settings/llm",
        json={"api_key": ""},
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_api_key"] is False
    assert body["api_key_masked"] is None


@pytest.mark.asyncio
async def test_get_never_returns_raw_api_key(client):
    secret = "sk-super-secret-key-1234567890abcdef"
    admin_cookies = await _admin_cookie(client)
    await client.put(
        "/api/v1/admin/settings/llm",
        json={"api_key": secret},
        cookies=admin_cookies,
    )

    resp = await client.get("/api/v1/admin/settings/llm", cookies=admin_cookies)
    assert resp.status_code == 200
    text = resp.text
    assert secret not in text


@pytest.mark.asyncio
async def test_masking_short_key(client):
    admin_cookies = await _admin_cookie(client)
    resp = await client.put(
        "/api/v1/admin/settings/llm",
        json={"api_key": "short"},
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["api_key_masked"] == "****"


@pytest.mark.asyncio
async def test_masking_long_key(client):
    admin_cookies = await _admin_cookie(client)
    resp = await client.put(
        "/api/v1/admin/settings/llm",
        json={"api_key": "sk-abcdefghijklmnop"},
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["api_key_masked"] == "sk-****mnop"


@pytest.mark.asyncio
async def test_get_after_put_returns_runtime_source(client):
    admin_cookies = await _admin_cookie(client)
    await client.put(
        "/api/v1/admin/settings/llm",
        json={"api_base": "http://localhost:9999/v1"},
        cookies=admin_cookies,
    )

    resp = await client.get("/api/v1/admin/settings/llm", cookies=admin_cookies)
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "runtime"
    assert body["api_base"] == "http://localhost:9999/v1"


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


@pytest.mark.asyncio
async def test_public_settings_llm_endpoint_works(client):
    """The non-admin /api/v1/settings/llm endpoint is now reachable."""
    resp = await client.get("/api/v1/settings/llm")
    assert resp.status_code == 200
    body = resp.json()
    assert "provider" in body


@pytest.mark.asyncio
async def test_put_and_get_provider_roundtrip(client):
    admin_cookies = await _admin_cookie(client)
    resp = await client.put(
        "/api/v1/admin/settings/llm",
        json={
            "api_base": "https://api.deepseek.com/v1",
            "model_name": "deepseek-chat",
            "api_key": "sk-abcdefghijklmnop1234567890",
            "provider": "deepseek",
        },
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "deepseek"

    resp = await client.get("/api/v1/admin/settings/llm", cookies=admin_cookies)
    assert resp.status_code == 200
    assert resp.json()["provider"] == "deepseek"
