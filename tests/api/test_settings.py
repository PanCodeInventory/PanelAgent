"""Tests for protected /api/v1/admin/settings/llm endpoints."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.services.admin_database import get_db_path

TEST_PASSWORD = "test-secret-password-123"
SESSION_SECRET = "test-session-secret-for-tests-only"


@pytest.fixture(autouse=True)
def _set_admin_env(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", TEST_PASSWORD)
    monkeypatch.setenv("ADMIN_SESSION_SECRET", SESSION_SECRET)


@pytest.fixture()
def tmp_db(tmp_path: Path):
    db_file = tmp_path / "test_admin.sqlite3"
    conn = sqlite3.connect(str(db_file))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS llm_settings ("
        "id INTEGER PRIMARY KEY CHECK (id = 1), "
        "api_base TEXT NOT NULL, api_key TEXT NULL, "
        "model_name TEXT NOT NULL, updated_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS panel_history ("
        "id TEXT PRIMARY KEY, created_at TEXT NOT NULL, "
        "species TEXT NOT NULL, inventory_file TEXT NULL, "
        "requested_markers TEXT NOT NULL, missing_markers TEXT NOT NULL, "
        "selected_panel TEXT NOT NULL, rationale TEXT NOT NULL, "
        "model_name TEXT NOT NULL, api_base TEXT NOT NULL)"
    )
    conn.commit()
    conn.close()
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
