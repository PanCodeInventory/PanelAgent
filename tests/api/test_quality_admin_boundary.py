"""Boundary tests for public vs admin quality-registry routes."""

from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.services.quality_projection import QualityProjector
from backend.app.services.quality_registry_store import QualityRegistryStore

TEST_PASSWORD = "test-secret-password-123"
SESSION_SECRET = "test-session-secret-for-tests-only"

VALID_ISSUE = {
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
async def client(tmp_path):
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
async def test_public_get_issue_list_removed(client):
    resp = await client.get("/api/v1/quality-registry/issues")
    assert resp.status_code in {404, 405}


@pytest.mark.asyncio
async def test_public_put_issue_removed(client):
    resp = await client.put(
        "/api/v1/quality-registry/issues/nonexistent-id",
        json={"issue_text": "Updated issue text", "reported_by": "bob"},
    )
    assert resp.status_code in {404, 405}


@pytest.mark.asyncio
async def test_public_create_issue_still_works(client):
    resp = await client.post("/api/v1/quality-registry/issues", json=VALID_ISSUE)
    assert resp.status_code == 200
    assert resp.json()["issue_text"] == VALID_ISSUE["issue_text"]


@pytest.mark.asyncio
async def test_admin_issue_list_requires_auth(client):
    resp = await client.get("/api/v1/admin/quality-registry/issues")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_issue_list_allows_authenticated_admin(client):
    await client.post("/api/v1/quality-registry/issues", json=VALID_ISSUE)
    admin_cookies = await _admin_cookie(client)

    resp = await client.get("/api/v1/admin/quality-registry/issues", cookies=admin_cookies)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_admin_resolve_requires_auth(client):
    from backend.app.api.v1.admin.endpoints import quality_registry as admin_qr_mod

    create_resp = await client.post("/api/v1/quality-registry/issues", json={**VALID_ISSUE, "clone": None})
    issue_id = create_resp.json()["id"]
    admin_qr_mod._store.send_to_review(issue_id)

    resp = await client.post(
        f"/api/v1/admin/quality-registry/review-queue/{issue_id}/resolve",
        json={"reviewer": "admin"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_update_allows_authenticated_admin(client):
    create_resp = await client.post("/api/v1/quality-registry/issues", json=VALID_ISSUE)
    issue_id = create_resp.json()["id"]
    admin_cookies = await _admin_cookie(client)

    resp = await client.put(
        f"/api/v1/admin/quality-registry/issues/{issue_id}",
        json={"issue_text": "Updated issue text", "reported_by": "bob"},
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    assert resp.json()["issue_text"] == "Updated issue text"
