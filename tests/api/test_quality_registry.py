"""Comprehensive API tests for quality registry endpoints.

Tests cover all 8 endpoints:
  POST   /quality-registry/issues                     — create issue
  GET    /quality-registry/issues                     — list issues
  GET    /quality-registry/issues/{issue_id}          — issue detail
  GET    /quality-registry/issues/{issue_id}/history  — audit history
  POST   /quality-registry/candidates/lookup          — candidate lookup
  POST   /quality-registry/candidates/confirm         — confirm candidate
  GET    /quality-registry/review-queue               — manual review queue
  POST   /quality-registry/review-queue/{issue_id}/resolve — resolve review
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

from backend.app.services.quality_registry_store import QualityRegistryStore
from backend.app.services.quality_projection import QualityProjector
from backend.app.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_VALID_ISSUE = {
    "issue_text": "Fluorescence spill-over detected on channel PE-Cy7",
    "reported_by": "alice",
    "species": "Mouse",
    "marker": "CD3",
    "fluorochrome": "APC",
    "brand": "BioLegend",
    "clone": "17A2",
}


@pytest_asyncio.fixture
async def qr_client(tmp_path):
    """AsyncClient with isolated store/projector using tmp_path."""
    from backend.app.api.v1.endpoints import quality_registry as qr_mod

    test_store = QualityRegistryStore(data_dir=str(tmp_path / "quality_registry"))
    test_projector = QualityProjector(test_store)

    with (
        patch.object(qr_mod, "_store", test_store),
        patch.object(qr_mod, "_projector", test_projector),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


# ---------------------------------------------------------------------------
# 1. Create issue
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# 2. Create issue — validation failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_issue_validation_missing_fields(qr_client):
    resp = await qr_client.post("/api/v1/quality-registry/issues", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_issue_validation_blank_issue_text(qr_client):
    payload = {**_VALID_ISSUE, "issue_text": "   "}
    resp = await qr_client.post("/api/v1/quality-registry/issues", json=payload)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 3. List issues
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_issues(qr_client):
    # Create two issues
    await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue2 = {**_VALID_ISSUE, "marker": "CD4", "fluorochrome": "PE"}
    await qr_client.post("/api/v1/quality-registry/issues", json=issue2)

    resp = await qr_client.get("/api/v1/quality-registry/issues")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2


# ---------------------------------------------------------------------------
# 4. List issues — filter by status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_issues_filter_by_status(qr_client):
    # Create an issue (status=submitted)
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    # Get submitted issues
    resp = await qr_client.get("/api/v1/quality-registry/issues", params={"status": "submitted"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Get resolved issues — should be empty
    resp2 = await qr_client.get("/api/v1/quality-registry/issues", params={"status": "resolved"})
    assert resp2.status_code == 200
    assert len(resp2.json()) == 0


# ---------------------------------------------------------------------------
# 5. Get issue detail
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_issue_detail(qr_client):
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    resp = await qr_client.get(f"/api/v1/quality-registry/issues/{issue_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == issue_id
    assert body["status"] == "submitted"
    assert body["issue_text"] == _VALID_ISSUE["issue_text"]


# ---------------------------------------------------------------------------
# 6. Get issue detail — not found
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_issue_detail_not_found(qr_client):
    resp = await qr_client.get("/api/v1/quality-registry/issues/nonexistent-id")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 7. Get history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_history(qr_client):
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    # History should have 1 event (created)
    resp = await qr_client.get(f"/api/v1/quality-registry/issues/{issue_id}/history")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 1
    assert events[0]["action"] == "created"
    assert events[0]["issue_id"] == issue_id


@pytest.mark.asyncio
async def test_get_history_with_entity_bind(qr_client):
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    # Confirm a candidate (binds entity)
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

    # History should have 2 events: created + entity_bound
    resp = await qr_client.get(f"/api/v1/quality-registry/issues/{issue_id}/history")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 2
    actions = [e["action"] for e in events]
    assert "created" in actions
    assert "entity_bound" in actions


@pytest.mark.asyncio
async def test_get_history_not_found(qr_client):
    resp = await qr_client.get("/api/v1/quality-registry/issues/nonexistent/history")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 8. Candidate lookup
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_candidate_lookup_with_inventory(qr_client):
    """Lookup with species=Mouse should search inventory if mapped file exists."""
    payload = {
        "text": "CD3 APC antibody",
        "species": "Mouse",
        "marker": "CD3",
        "fluorochrome": "APC",
    }
    # The inventory for Mouse may or may not exist in test env.
    # If it doesn't exist, we just get an empty list — that's fine.
    resp = await qr_client.post("/api/v1/quality-registry/candidates/lookup", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "candidates" in body


@pytest.mark.asyncio
async def test_candidate_lookup_no_species(qr_client):
    """Lookup without species returns empty candidates (no inventory resolved)."""
    payload = {
        "text": "CD3 APC antibody",
        "marker": "CD3",
        "fluorochrome": "APC",
    }
    resp = await qr_client.post("/api/v1/quality-registry/candidates/lookup", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["candidates"] == []


@pytest.mark.asyncio
async def test_candidate_lookup_nonexistent_marker(qr_client):
    """Lookup with marker not in inventory returns empty candidates."""
    payload = {
        "text": "XYZ999 antibody",
        "species": "Mouse",
        "marker": "XYZ999",
        "fluorochrome": "APC",
    }
    resp = await qr_client.post("/api/v1/quality-registry/candidates/lookup", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["candidates"] == []


# ---------------------------------------------------------------------------
# 9. Candidate confirm
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_candidate_confirm(qr_client):
    # Create an issue
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    # Confirm a candidate
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


# ---------------------------------------------------------------------------
# 10. Manual review queue
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_review_queue_empty(qr_client):
    resp = await qr_client.get("/api/v1/quality-registry/review-queue")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_review_queue_with_items(qr_client):
    from backend.app.api.v1.endpoints import quality_registry as qr_mod

    # Create issue then send to review via the store directly
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]

    # Send to review using the patched store
    qr_mod._store.send_to_review(issue_id)

    resp = await qr_client.get("/api/v1/quality-registry/review-queue")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == issue_id
    assert body[0]["status"] == "pending_review"


# ---------------------------------------------------------------------------
# 11. Resolve review
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_review(qr_client):
    from backend.app.api.v1.endpoints import quality_registry as qr_mod

    # Create issue and send to review
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]
    qr_mod._store.send_to_review(issue_id)

    # Resolve review
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
        f"/api/v1/quality-registry/review-queue/{issue_id}/resolve",
        json=resolve_payload,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == issue_id
    assert body["status"] == "resolved"
    assert body["entity_key"] is not None


@pytest.mark.asyncio
async def test_resolve_review_without_entity(qr_client):
    from backend.app.api.v1.endpoints import quality_registry as qr_mod

    # Create issue and send to review
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    issue_id = r.json()["id"]
    qr_mod._store.send_to_review(issue_id)

    # Resolve without entity key
    resolve_payload = {"reviewer": "carol"}
    resp = await qr_client.post(
        f"/api/v1/quality-registry/review-queue/{issue_id}/resolve",
        json=resolve_payload,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "resolved"


@pytest.mark.asyncio
async def test_resolve_review_not_found(qr_client):
    resolve_payload = {"reviewer": "bob"}
    resp = await qr_client.post(
        "/api/v1/quality-registry/review-queue/nonexistent/resolve",
        json=resolve_payload,
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_issues_empty(qr_client):
    resp = await qr_client.get("/api/v1/quality-registry/issues")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_candidate_confirm_updates_projection(qr_client):
    """Verify that confirming a candidate triggers projection update (no error)."""
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
    # Check the issue is now confirmed
    detail = await qr_client.get(f"/api/v1/quality-registry/issues/{issue_id}")
    assert detail.json()["status"] == "confirmed"


@pytest.mark.asyncio
async def test_full_lifecycle(qr_client):
    """End-to-end: create → confirm → send_to_review → resolve."""
    from backend.app.api.v1.endpoints import quality_registry as qr_mod

    # 1. Create
    r = await qr_client.post("/api/v1/quality-registry/issues", json=_VALID_ISSUE)
    assert r.status_code == 200
    issue_id = r.json()["id"]
    assert r.json()["status"] == "submitted"

    # 2. Confirm candidate
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

    # 3. Send to review
    qr_mod._store.send_to_review(issue_id)
    r3 = await qr_client.get("/api/v1/quality-registry/review-queue")
    assert len(r3.json()) == 1
    assert r3.json()[0]["status"] == "pending_review"

    # 4. Resolve review
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
        f"/api/v1/quality-registry/review-queue/{issue_id}/resolve",
        json=resolve,
    )
    assert r4.status_code == 200
    assert r4.json()["status"] == "resolved"

    # 5. Review queue should be empty now
    r5 = await qr_client.get("/api/v1/quality-registry/review-queue")
    assert r5.json() == []

    # 6. History should have 4 events: created, entity_bound, status_changed, resolved
    r6 = await qr_client.get(f"/api/v1/quality-registry/issues/{issue_id}/history")
    events = r6.json()
    actions = [e["action"] for e in events]
    assert "created" in actions
    assert "entity_bound" in actions
    assert "status_changed" in actions
    assert "resolved" in actions


# ---------------------------------------------------------------------------
# Brand filtering in candidate lookup
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_candidate_lookup_filters_by_brand(qr_client):
    """Lookup should return only candidates matching the requested brand."""
    response = await qr_client.post("/api/v1/quality-registry/candidates/lookup", json={
        "text": "CD3",
        "species": "Mouse",
        "marker": "CD3",
        "fluorochrome": "APC",
        "brand": "BioLegend",
    })
    data = response.json()
    assert response.status_code == 200
    for c in data["candidates"]:
        assert c["entity_key"]["brand"].lower() == "biolegend"


# ---------------------------------------------------------------------------
# Auto-route to pending_review
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_issue_auto_routes_to_pending_review(qr_client):
    """Issues without clone should auto-transition to pending_review."""
    response = await qr_client.post("/api/v1/quality-registry/issues", json={
        "issue_text": "Poor staining",
        "reported_by": "researcher",
        "species": "Human",
        "marker": "CD3",
        "fluorochrome": "APC",
        "brand": "BioLegend",
    })
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "pending_review"
    assert data["entity_key"] is None


@pytest.mark.asyncio
async def test_create_issue_stays_submitted_with_clone(qr_client):
    """Issues with clone should stay as submitted (not auto-routed)."""
    response = await qr_client.post("/api/v1/quality-registry/issues", json={
        "issue_text": "Poor staining",
        "reported_by": "researcher",
        "species": "Human",
        "marker": "CD3",
        "fluorochrome": "APC",
        "brand": "BioLegend",
        "clone": "UCHT1",
    })
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "submitted"


@pytest.mark.asyncio
async def test_candidate_lookup_with_localized_species(qr_client):
    """Lookup should work with localized species strings like 'Mouse (小鼠)'."""
    response = await qr_client.post("/api/v1/quality-registry/candidates/lookup", json={
        "text": "CD3",
        "species": "Mouse (小鼠)",
        "marker": "CD3",
        "fluorochrome": "APC",
    })
    assert response.status_code == 200
    data = response.json()
    assert "candidates" in data


@pytest.mark.asyncio
async def test_candidate_confirm_rejects_species_mismatch(qr_client):
    """Confirm should reject entity_key with different species than issue."""
    create_resp = await qr_client.post("/api/v1/quality-registry/issues", json={
        "issue_text": "Test issue",
        "reported_by": "researcher",
        "species": "Human",
        "marker": "CD3",
        "fluorochrome": "APC",
        "brand": "BioLegend",
        "clone": "UCHT1",
    })
    issue = create_resp.json()

    confirm_resp = await qr_client.post("/api/v1/quality-registry/candidates/confirm", json={
        "issue_id": issue["id"],
        "entity_key": {
            "species": "Mouse",
            "normalized_marker": "CD3",
            "clone": "17A2",
            "brand": "BioLegend",
            "catalog_number": "100206",
        },
    })
    assert confirm_resp.status_code == 422
