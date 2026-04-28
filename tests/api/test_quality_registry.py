"""Comprehensive API tests for quality registry endpoints."""

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
    """AsyncClient with isolated store/projector using tmp_path."""
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
async def test_create_issue(qr_client):
    resp = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body
    assert body["status"] == "submitted"
    assert body["issue_text"] == _VALID_ISSUE["issue_text"]
    assert body["reported_by"] == "alice"
    assert body["feedback_key"]["species"] == "Mouse"
    assert body["feedback_key"]["normalized_marker"] == "cd3"
    assert body["feedback_key"]["fluorochrome"] == "APC"
    assert body["feedback_key"]["brand"] == "BioLegend"
    assert "created_at" in body
    assert "updated_at" in body
    assert body["entity_key"] is None


@pytest.mark.asyncio
async def test_create_issue_validation_missing_fields(qr_client):
    resp = await qr_client.post("/api/v1/quality-registry/issues", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_issue_validation_blank_issue_text(qr_client):
    payload = {**_VALID_ISSUE, "issue_text": "   "}
    resp = await qr_client.post("/api/v1/quality-registry/issues", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_issues(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue2 = {**_VALID_ISSUE, "marker": "CD4", "fluorochrome": "PE"}
    await qr_client.post("/api/v1/quality-registry/issues", json=issue2)

    resp = await qr_client.get("/api/v1/admin/quality-registry/issues", cookies=admin_cookies)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_issues_filter_by_status(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)

    resp = await qr_client.get(
        "/api/v1/admin/quality-registry/issues",
        params={"status": "submitted"},
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    resp2 = await qr_client.get(
        "/api/v1/admin/quality-registry/issues",
        params={"status": "resolved"},
        cookies=admin_cookies,
    )
    assert resp2.status_code == 200
    assert len(resp2.json()) == 0


@pytest.mark.asyncio
async def test_get_issue_detail(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    resp = await qr_client.get(
        f"/api/v1/admin/quality-registry/issues/{issue_id}",
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == issue_id
    assert body["status"] == "submitted"
    assert body["issue_text"] == _VALID_ISSUE["issue_text"]


@pytest.mark.asyncio
async def test_get_issue_detail_not_found(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    resp = await qr_client.get(
        "/api/v1/admin/quality-registry/issues/nonexistent-id",
        cookies=admin_cookies,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_history(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    resp = await qr_client.get(
        f"/api/v1/admin/quality-registry/issues/{issue_id}/history",
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 1
    assert events[0]["action"] == "created"
    assert events[0]["issue_id"] == issue_id


@pytest.mark.asyncio
async def test_get_history_with_entity_bind(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    confirm_payload = {
        "issue_id": issue_id,
        "entity_key": {
            "species": "Mouse",
            "normalized_marker": "cd3",
            "clone": "17A2",
            "brand": "BioLegend",
            "catalog_number": "100235",
        },
    }
    await qr_client.post("/api/v1/quality-registry/candidates/confirm", json=confirm_payload)

    resp = await qr_client.get(
        f"/api/v1/admin/quality-registry/issues/{issue_id}/history",
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    actions = [e["action"] for e in resp.json()]
    assert "created" in actions
    assert "entity_bound" in actions


@pytest.mark.asyncio
async def test_get_history_not_found(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    resp = await qr_client.get(
        "/api/v1/admin/quality-registry/issues/nonexistent/history",
        cookies=admin_cookies,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_candidate_lookup_with_inventory(qr_client):
    payload = {
        "text": "CD3 APC antibody",
        "species": "Mouse",
        "marker": "CD3",
        "fluorochrome": "APC",
    }
    resp = await qr_client.post("/api/v1/quality-registry/candidates/lookup", json=payload)
    assert resp.status_code == 200
    assert "candidates" in resp.json()


@pytest.mark.asyncio
async def test_candidate_lookup_no_species(qr_client):
    payload = {"text": "CD3 APC antibody", "marker": "CD3", "fluorochrome": "APC"}
    resp = await qr_client.post("/api/v1/quality-registry/candidates/lookup", json=payload)
    assert resp.status_code == 200
    assert resp.json()["candidates"] == []


@pytest.mark.asyncio
async def test_candidate_lookup_nonexistent_marker(qr_client):
    payload = {
        "text": "XYZ999 antibody",
        "species": "Mouse",
        "marker": "XYZ999",
        "fluorochrome": "APC",
    }
    resp = await qr_client.post("/api/v1/quality-registry/candidates/lookup", json=payload)
    assert resp.status_code == 200
    assert resp.json()["candidates"] == []


@pytest.mark.asyncio
async def test_candidate_confirm(qr_client):
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    confirm_payload = {
        "issue_id": issue_id,
        "entity_key": {
            "species": "Mouse",
            "normalized_marker": "cd3",
            "clone": "17A2",
            "brand": "BioLegend",
            "catalog_number": "100235",
        },
    }
    resp = await qr_client.post("/api/v1/quality-registry/candidates/confirm", json=confirm_payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == issue_id
    assert body["status"] == "confirmed"
    assert body["entity_key"] is not None
    assert body["entity_key"]["clone"] == "17A2"
    assert body["entity_key"]["catalog_number"] == "100235"


@pytest.mark.asyncio
async def test_candidate_confirm_issue_not_found(qr_client):
    confirm_payload = {
        "issue_id": "nonexistent-id",
        "entity_key": {
            "species": "Mouse",
            "normalized_marker": "cd3",
            "clone": "17A2",
            "brand": "BioLegend",
            "catalog_number": "100235",
        },
    }
    resp = await qr_client.post("/api/v1/quality-registry/candidates/confirm", json=confirm_payload)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_review_queue_empty(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    resp = await qr_client.get("/api/v1/admin/quality-registry/review-queue", cookies=admin_cookies)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_review_queue_with_items(qr_client):
    from backend.app.api.v1.admin.endpoints import quality_registry as admin_qr_mod

    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]
    admin_qr_mod._store.send_to_review(issue_id)

    resp = await qr_client.get("/api/v1/admin/quality-registry/review-queue", cookies=admin_cookies)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == issue_id
    assert body[0]["status"] == "pending_review"


@pytest.mark.asyncio
async def test_resolve_review(qr_client):
    from backend.app.api.v1.admin.endpoints import quality_registry as admin_qr_mod

    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]
    admin_qr_mod._store.send_to_review(issue_id)

    resolve_payload = {
        "reviewer": "bob",
        "entity_key": {
            "species": "Mouse",
            "normalized_marker": "cd3",
            "clone": "17A2",
            "brand": "BioLegend",
            "catalog_number": "100235",
        },
    }
    resp = await qr_client.post(
        f"/api/v1/admin/quality-registry/review-queue/{issue_id}/resolve",
        json=resolve_payload,
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == issue_id
    assert body["status"] == "resolved"
    assert body["entity_key"] is not None


@pytest.mark.asyncio
async def test_resolve_review_without_entity(qr_client):
    from backend.app.api.v1.admin.endpoints import quality_registry as admin_qr_mod

    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]
    admin_qr_mod._store.send_to_review(issue_id)

    resp = await qr_client.post(
        f"/api/v1/admin/quality-registry/review-queue/{issue_id}/resolve",
        json={"reviewer": "carol"},
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"


@pytest.mark.asyncio
async def test_resolve_review_not_found(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    resp = await qr_client.post(
        "/api/v1/admin/quality-registry/review-queue/nonexistent/resolve",
        json={"reviewer": "bob"},
        cookies=admin_cookies,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_issues_empty(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    resp = await qr_client.get("/api/v1/admin/quality-registry/issues", cookies=admin_cookies)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_candidate_confirm_updates_projection(qr_client):
    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    confirm_payload = {
        "issue_id": issue_id,
        "entity_key": {
            "species": "Mouse",
            "normalized_marker": "cd3",
            "clone": "17A2",
            "brand": "BioLegend",
            "catalog_number": "100235",
        },
    }
    resp = await qr_client.post("/api/v1/quality-registry/candidates/confirm", json=confirm_payload)
    assert resp.status_code == 200

    detail = await qr_client.get(
        f"/api/v1/admin/quality-registry/issues/{issue_id}",
        cookies=admin_cookies,
    )
    assert detail.json()["status"] == "confirmed"


@pytest.mark.asyncio
async def test_full_lifecycle(qr_client):
    from backend.app.api.v1.admin.endpoints import quality_registry as admin_qr_mod

    admin_cookies = await _admin_cookie(qr_client)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    assert r.status_code == 200
    issue_id = r.json()["id"]
    assert r.json()["status"] == "submitted"

    confirm = {
        "issue_id": issue_id,
        "entity_key": {
            "species": "Mouse",
            "normalized_marker": "cd3",
            "clone": "17A2",
            "brand": "BioLegend",
            "catalog_number": "100235",
        },
    }
    r2 = await qr_client.post("/api/v1/quality-registry/candidates/confirm", json=confirm)
    assert r2.status_code == 200
    assert r2.json()["status"] == "confirmed"

    admin_qr_mod._store.send_to_review(issue_id)
    r3 = await qr_client.get("/api/v1/admin/quality-registry/review-queue", cookies=admin_cookies)
    assert len(r3.json()) == 1
    assert r3.json()[0]["status"] == "pending_review"

    resolve = {
        "reviewer": "admin",
        "entity_key": {
            "species": "Mouse",
            "normalized_marker": "cd3",
            "clone": "17A2",
            "brand": "BioLegend",
            "catalog_number": "100235",
        },
    }
    r4 = await qr_client.post(
        f"/api/v1/admin/quality-registry/review-queue/{issue_id}/resolve",
        json=resolve,
        cookies=admin_cookies,
    )
    assert r4.status_code == 200
    assert r4.json()["status"] == "resolved"

    r5 = await qr_client.get("/api/v1/admin/quality-registry/review-queue", cookies=admin_cookies)
    assert r5.json() == []

    r6 = await qr_client.get(
        f"/api/v1/admin/quality-registry/issues/{issue_id}/history",
        cookies=admin_cookies,
    )
    actions = [e["action"] for e in r6.json()]
    assert "created" in actions
    assert "entity_bound" in actions
    assert "status_changed" in actions
    assert "resolved" in actions


@pytest.mark.asyncio
async def test_candidate_lookup_filters_by_brand(qr_client):
    response = await qr_client.post(
        "/api/v1/quality-registry/candidates/lookup",
        json={
            "text": "CD3",
            "species": "Mouse",
            "marker": "CD3",
            "fluorochrome": "APC",
            "brand": "BioLegend",
        },
    )
    data = response.json()
    assert response.status_code == 200
    for c in data["candidates"]:
        assert c["entity_key"]["brand"].lower() == "biolegend"


@pytest.mark.asyncio
async def test_create_issue_auto_routes_to_pending_review(qr_client):
    response = await qr_client.post(
        "/api/v1/quality-registry/issues",
        json={
            "issue_text": "Poor staining",
            "reported_by": "researcher",
            "species": "Human",
            "marker": "CD3",
            "fluorochrome": "APC",
            "brand": "BioLegend",
        },
    )
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "pending_review"
    assert data["entity_key"] is None


@pytest.mark.asyncio
async def test_create_issue_stays_submitted_with_clone(qr_client):
    response = await qr_client.post(
        "/api/v1/quality-registry/issues",
        json={
            "issue_text": "Poor staining",
            "reported_by": "researcher",
            "species": "Human",
            "marker": "CD3",
            "fluorochrome": "APC",
            "brand": "BioLegend",
            "clone": "UCHT1",
        },
    )
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "submitted"


@pytest.mark.asyncio
async def test_candidate_lookup_with_localized_species(qr_client):
    response = await qr_client.post(
        "/api/v1/quality-registry/candidates/lookup",
        json={
            "text": "CD3",
            "species": "Mouse (小鼠)",
            "marker": "CD3",
            "fluorochrome": "APC",
        },
    )
    assert response.status_code == 200
    assert "candidates" in response.json()


@pytest.mark.asyncio
async def test_candidate_confirm_rejects_species_mismatch(qr_client):
    create_resp = await qr_client.post(
        "/api/v1/quality-registry/issues",
        json={
            "issue_text": "Test issue",
            "reported_by": "researcher",
            "species": "Human",
            "marker": "CD3",
            "fluorochrome": "APC",
            "brand": "BioLegend",
            "clone": "UCHT1",
        },
    )
    issue = create_resp.json()

    confirm_resp = await qr_client.post(
        "/api/v1/quality-registry/candidates/confirm",
        json={
            "issue_id": issue["id"],
            "entity_key": {
                "species": "Mouse",
                "normalized_marker": "CD3",
                "clone": "17A2",
                "brand": "BioLegend",
                "catalog_number": "100206",
            },
        },
    )
    assert confirm_resp.status_code == 422
