"""Tests for PUT /admin/quality-registry/issues/{issue_id} endpoint."""

from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.services.quality_projection import QualityProjector
from backend.app.services.quality_registry_store import QualityRegistryStore

TEST_PASSWORD = "test-secret-password-123"
SESSION_SECRET = "test-session-secret-for-tests-only"

_VALID_ISSUE = {
    "issue_text": "Fluorescence spill-over detected on channel PE-Cy7",
    "reported_by": "alice",
    "species": "Mouse",
    "marker": "CD3",
    "fluorochrome": "APC",
    "brand": "BioLegend",
    "clone": "17A2",
}


@pytest.fixture(autouse=True)
def _set_admin_env(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", TEST_PASSWORD)
    monkeypatch.setenv("ADMIN_SESSION_SECRET", SESSION_SECRET)


@pytest_asyncio.fixture
async def qr_client(tmp_path):
    from backend.app.api.v1.admin.endpoints import quality_registry as admin_qr_mod
    from backend.app.api.v1.endpoints import quality_registry as qr_mod

    test_store = QualityRegistryStore(data_dir=str(tmp_path / "quality_registry"))
    test_projector = QualityProjector(test_store)

    with (
        patch.object(qr_mod, "_store", test_store),
        patch.object(qr_mod, "_projector", test_projector),
        patch.object(admin_qr_mod, "_store", test_store),
        patch.object(admin_qr_mod, "_projector", test_projector),
    ):
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
async def test_update_issue_success(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    resp = await qr_client.put(
        f"/api/v1/admin/quality-registry/issues/{issue_id}",
        json={"issue_text": "Updated issue text", "reported_by": "bob"},
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == issue_id
    assert body["issue_text"] == "Updated issue text"
    assert body["reported_by"] == "bob"


@pytest.mark.asyncio
async def test_update_issue_not_found(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    resp = await qr_client.put(
        "/api/v1/admin/quality-registry/issues/nonexistent-id",
        json={"issue_text": "Something", "reported_by": "alice"},
        cookies=admin_cookies,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_issue_blank_issue_text(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    resp = await qr_client.put(
        f"/api/v1/admin/quality-registry/issues/{issue_id}",
        json={"issue_text": "", "reported_by": "alice"},
        cookies=admin_cookies,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_issue_blank_reported_by(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    resp = await qr_client.put(
        f"/api/v1/admin/quality-registry/issues/{issue_id}",
        json={"issue_text": "Valid text", "reported_by": ""},
        cookies=admin_cookies,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_issue_whitespace_issue_text(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    resp = await qr_client.put(
        f"/api/v1/admin/quality-registry/issues/{issue_id}",
        json={"issue_text": "   ", "reported_by": "alice"},
        cookies=admin_cookies,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_issue_preserves_immutable_fields(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    created = r.json()
    issue_id = created["id"]

    resp = await qr_client.put(
        f"/api/v1/admin/quality-registry/issues/{issue_id}",
        json={"issue_text": "Changed text", "reported_by": "bob"},
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["feedback_key"] == created["feedback_key"]
    assert body["status"] == created["status"]
    assert body["created_at"] == created["created_at"]
    assert body["entity_key"] is None


@pytest.mark.asyncio
async def test_update_issue_audit_history(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    await qr_client.put(
        f"/api/v1/admin/quality-registry/issues/{issue_id}",
        json={"issue_text": "Updated text", "reported_by": "bob"},
        cookies=admin_cookies,
    )

    hist = await qr_client.get(
        f"/api/v1/admin/quality-registry/issues/{issue_id}/history",
        cookies=admin_cookies,
    )
    events = hist.json()
    assert len(events) == 2

    edited = [e for e in events if e["action"] == "edited"]
    assert len(edited) == 1

    details = edited[0]["details"]
    assert details["old_issue_text"] == _VALID_ISSUE["issue_text"]
    assert details["new_issue_text"] == "Updated text"
    assert details["old_reported_by"] == "alice"
    assert details["new_reported_by"] == "bob"
    assert edited[0]["actor"] == "bob"
