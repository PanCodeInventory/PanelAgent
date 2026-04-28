"""Tests for panel history persistence and protected admin API endpoints."""

from unittest.mock import patch, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.services.panel_history_store import PanelHistoryStore, PanelHistoryEntry
from backend.app.services.admin_database import init_db, get_db_path

TEST_PASSWORD = "test-secret-password-123"
SESSION_SECRET = "test-session-secret-for-tests-only"


@pytest.fixture(autouse=True)
def _set_admin_env(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", TEST_PASSWORD)
    monkeypatch.setenv("ADMIN_SESSION_SECRET", SESSION_SECRET)


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    """Redirect admin DB to a temp file for test isolation."""
    db_file = tmp_path / "test_admin.sqlite3"
    monkeypatch.setattr("backend.app.services.admin_database.get_db_path", lambda _: db_file)
    init_db(str(db_file))
    yield


MOCK_EVALUATE_SUCCESS = {
    "status": "success",
    "selected_panel": {
        "CD3": {"system_code": "FITC", "fluorochrome": "FITC", "brightness": 5, "clone": "OKT3", "brand": "BioLegend", "catalog_number": "317306", "target": "CD3", "stock": 10},
        "CD4": {"system_code": "PE", "fluorochrome": "PE", "brightness": 4, "clone": "RPA-T4", "brand": "BioLegend", "catalog_number": "300558", "target": "CD4", "stock": 8},
    },
    "rationale": "CD3-FITC and CD4-PE provide good separation with minimal spillover.",
    "gating_detail": [],
    "message": None,
}

MOCK_EVALUATE_FAILURE = {
    "status": "error",
    "message": "All candidates have fatal conflicts.",
}

CANDIDATES = [
    {
        "CD3": {"system_code": "FITC", "fluorochrome": "FITC", "brightness": 5, "clone": "OKT3", "brand": "BioLegend", "catalog_number": "317306", "target": "CD3", "stock": 10},
        "CD4": {"system_code": "PE", "fluorochrome": "PE", "brightness": 4, "clone": "RPA-T4", "brand": "BioLegend", "catalog_number": "300558", "target": "CD4", "stock": 8},
    }
]


@pytest_asyncio.fixture
async def client():
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
async def test_successful_evaluate_writes_history(client):
    """After successful evaluate, a history entry should be persisted."""
    mock_llm_settings = MagicMock()
    mock_llm_settings.model_name = "gpt-test"
    mock_llm_settings.api_base = "https://api.test.com/v1"

    with (
        patch("panel_generator.evaluate_candidates_with_llm", return_value=MOCK_EVALUATE_SUCCESS),
        patch("backend.app.services.llm_settings_store.LlmSettingsStore.get_effective_settings", return_value=mock_llm_settings),
    ):
        resp = await client.post("/api/v1/panels/evaluate", json={
            "candidates": CANDIDATES,
            "missing_markers": ["CD8"],
            "species": "Mouse",
            "markers": ["CD3", "CD4", "CD8"],
            "inventory_file": "mouse_inventory.csv",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"

    store = PanelHistoryStore()
    entries = store.list_entries()
    assert len(entries) == 1

    entry = entries[0]
    assert entry.species == "Mouse"
    assert entry.inventory_file == "mouse_inventory.csv"
    assert entry.requested_markers == ["CD3", "CD4", "CD8"]
    assert entry.missing_markers == ["CD8"]
    assert entry.rationale == MOCK_EVALUATE_SUCCESS["rationale"]
    assert entry.model_name == "gpt-test"
    assert entry.api_base == "https://api.test.com/v1"
    assert len(entry.selected_panel) == 2


@pytest.mark.asyncio
async def test_failed_evaluate_does_not_write_history(client):
    """Failed evaluate (LLM returns error) must NOT create a history entry."""
    with (
        patch("panel_generator.evaluate_candidates_with_llm", return_value=MOCK_EVALUATE_FAILURE),
    ):
        resp = await client.post("/api/v1/panels/evaluate", json={
            "candidates": CANDIDATES,
            "missing_markers": [],
        })
        assert resp.status_code == 400

    store = PanelHistoryStore()
    entries = store.list_entries()
    assert len(entries) == 0


@pytest.mark.asyncio
async def test_evaluate_exception_does_not_write_history(client):
    """If LLM call raises an exception, no history entry should be created."""
    with (
        patch("panel_generator.evaluate_candidates_with_llm", side_effect=RuntimeError("LLM down")),
    ):
        resp = await client.post("/api/v1/panels/evaluate", json={
            "candidates": CANDIDATES,
            "missing_markers": [],
        })
        assert resp.status_code == 400

    store = PanelHistoryStore()
    entries = store.list_entries()
    assert len(entries) == 0


@pytest.mark.asyncio
async def test_history_list_returns_desc_order(client):
    """GET /admin/panel-history requires auth and returns DESC order."""
    store = PanelHistoryStore()
    mock_llm_settings = MagicMock()
    mock_llm_settings.model_name = "test-model"
    mock_llm_settings.api_base = "https://test.api/v1"

    with patch("backend.app.services.llm_settings_store.LlmSettingsStore.get_effective_settings", return_value=mock_llm_settings):
        for i in range(3):
            with patch("panel_generator.evaluate_candidates_with_llm", return_value=MOCK_EVALUATE_SUCCESS):
                await client.post("/api/v1/panels/evaluate", json={
                    "candidates": CANDIDATES,
                    "missing_markers": [],
                    "species": f"Species{i}",
                    "markers": [],
                })

    resp = await client.get("/api/v1/admin/panel-history")
    assert resp.status_code == 401

    admin_cookies = await _admin_cookie(client)
    resp = await client.get("/api/v1/admin/panel-history", cookies=admin_cookies)
    assert resp.status_code == 200
    body = resp.json()

    items = body["items"]
    assert len(items) == 3
    assert items[0]["species"] == "Species2"
    assert items[1]["species"] == "Species1"
    assert items[2]["species"] == "Species0"


@pytest.mark.asyncio
async def test_history_detail_returns_full_entry(client):
    """GET /admin/panel-history/{id} requires auth and returns full entry."""
    mock_llm_settings = MagicMock()
    mock_llm_settings.model_name = "detail-model"
    mock_llm_settings.api_base = "https://detail.api/v1"

    with (
        patch("panel_generator.evaluate_candidates_with_llm", return_value=MOCK_EVALUATE_SUCCESS),
        patch("backend.app.services.llm_settings_store.LlmSettingsStore.get_effective_settings", return_value=mock_llm_settings),
    ):
        await client.post("/api/v1/panels/evaluate", json={
            "candidates": CANDIDATES,
            "missing_markers": [],
            "species": "Human",
            "markers": ["CD3", "CD4"],
        })

    store = PanelHistoryStore()
    entries = store.list_entries()
    assert len(entries) == 1
    entry_id = entries[0].id

    resp = await client.get(f"/api/v1/admin/panel-history/{entry_id}")
    assert resp.status_code == 401

    admin_cookies = await _admin_cookie(client)
    resp = await client.get(
        f"/api/v1/admin/panel-history/{entry_id}",
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    body = resp.json()

    detail = body["item"]
    assert detail["id"] == entry_id
    assert detail["species"] == "Human"
    assert detail["model_name"] == "detail-model"
    assert detail["api_base"] == "https://detail.api/v1"
    assert len(detail["selected_panel"]) == 2
    assert detail["rationale"] == MOCK_EVALUATE_SUCCESS["rationale"]


@pytest.mark.asyncio
async def test_history_detail_not_found(client):
    """GET /admin/panel-history/{id} requires auth and 404s when missing."""
    resp = await client.get("/api/v1/admin/panel-history/nonexistent-id")
    assert resp.status_code == 401

    admin_cookies = await _admin_cookie(client)
    resp = await client.get(
        "/api/v1/admin/panel-history/nonexistent-id",
        cookies=admin_cookies,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_history_record_contains_model_snapshot(client):
    """History entry snapshots the LLM model_name and api_base at evaluation time."""
    mock_settings = MagicMock()
    mock_settings.model_name = "snapshot-model"
    mock_settings.api_base = "https://snapshot.api/v1"

    with (
        patch("panel_generator.evaluate_candidates_with_llm", return_value=MOCK_EVALUATE_SUCCESS),
        patch("backend.app.services.llm_settings_store.LlmSettingsStore.get_effective_settings", return_value=mock_settings),
    ):
        await client.post("/api/v1/panels/evaluate", json={
            "candidates": CANDIDATES,
            "missing_markers": [],
            "species": "Mouse",
        })

    store = PanelHistoryStore()
    entries = store.list_entries()
    assert len(entries) == 1
    assert entries[0].model_name == "snapshot-model"
    assert entries[0].api_base == "https://snapshot.api/v1"


@pytest.mark.asyncio
async def test_evaluate_without_context_uses_defaults(client):
    """Evaluate without species/markers still writes history with defaults."""
    mock_llm_settings = MagicMock()
    mock_llm_settings.model_name = "default-model"
    mock_llm_settings.api_base = "https://default.api/v1"

    with (
        patch("panel_generator.evaluate_candidates_with_llm", return_value=MOCK_EVALUATE_SUCCESS),
        patch("backend.app.services.llm_settings_store.LlmSettingsStore.get_effective_settings", return_value=mock_llm_settings),
    ):
        resp = await client.post("/api/v1/panels/evaluate", json={
            "candidates": CANDIDATES,
            "missing_markers": [],
        })
        assert resp.status_code == 200

    store = PanelHistoryStore()
    entries = store.list_entries()
    assert len(entries) == 1
    assert entries[0].species == "unknown"
    assert entries[0].requested_markers == []
