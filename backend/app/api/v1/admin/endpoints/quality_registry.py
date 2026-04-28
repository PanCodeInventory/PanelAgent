"""Admin quality registry endpoints — protected review and management flows."""

import importlib
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.v1.admin.dependencies import require_admin_session

_schemas = importlib.import_module("backend.app.schemas.quality_registry")
QualityIssueResponse = _schemas.QualityIssueResponse
QualityIssueUpdate = _schemas.QualityIssueUpdate
EntityKey = _schemas.EntityKey
ReviewItemResponse = _schemas.ReviewItemResponse

_store_module = importlib.import_module("backend.app.services.quality_registry_store")
QualityRegistryStore = _store_module.QualityRegistryStore
AuditEvent = _store_module.AuditEvent

_proj_module = importlib.import_module("backend.app.services.quality_projection")
QualityProjector = _proj_module.QualityProjector

public_module = importlib.import_module("backend.app.api.v1.endpoints.quality_registry")
ResolveReviewRequest = public_module.ResolveReviewRequest

router = APIRouter(
    prefix="/quality-registry",
    dependencies=[Depends(require_admin_session)],
)

_store = QualityRegistryStore()
_projector = QualityProjector(_store)


@router.put("/issues/{issue_id}", response_model=QualityIssueResponse)
async def update_issue(issue_id: str, payload: QualityIssueUpdate) -> QualityIssueResponse:
    issue = _store.get_issue(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    return _store.update_issue(issue_id, payload)


@router.get("/issues", response_model=list[QualityIssueResponse])
async def list_issues(status: Optional[str] = None) -> list[QualityIssueResponse]:
    """List quality issues, optionally filtered by status."""
    return _store.list_issues(status=status)


@router.get("/issues/{issue_id}", response_model=QualityIssueResponse)
async def get_issue(issue_id: str) -> QualityIssueResponse:
    """Get a single quality issue by ID."""
    issue = _store.get_issue(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.get("/issues/{issue_id}/history", response_model=list[AuditEvent])
async def get_history(issue_id: str) -> list[AuditEvent]:
    """Get audit history for a quality issue."""
    issue = _store.get_issue(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return _store.get_history(issue_id)


@router.get("/review-queue", response_model=list[ReviewItemResponse])
async def review_queue() -> list[ReviewItemResponse]:
    """List all issues in pending_review status."""
    issues = _store.list_issues(status="pending_review")
    return [
        ReviewItemResponse(
            id=i.id,
            feedback_key=i.feedback_key,
            entity_key=i.entity_key,
            issue_text=i.issue_text,
            reported_by=i.reported_by,
            status=i.status,
            reviewer=None,
            reviewed_at=None,
            created_at=i.created_at,
            updated_at=i.updated_at,
        )
        for i in issues
    ]


@router.post("/review-queue/{issue_id}/resolve", response_model=QualityIssueResponse)
async def resolve_review(issue_id: str, payload: ResolveReviewRequest) -> QualityIssueResponse:
    """Resolve a manual review item."""
    issue = _store.get_issue(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    if payload.entity_key is not None:
        if payload.entity_key.species.lower() != issue.feedback_key.species.lower():
            raise HTTPException(
                status_code=422,
                detail=f"Entity species '{payload.entity_key.species}' does not match issue species '{issue.feedback_key.species}'",
            )

    old_entity_key: EntityKey | None = issue.entity_key

    updated = _store.resolve_review(
        issue_id=issue_id,
        reviewer=payload.reviewer,
        entity_key=payload.entity_key,
    )
    _projector.update_projection(issue_id)

    if old_entity_key is not None and payload.entity_key is not None and old_entity_key != payload.entity_key:
        _projector.recompute_entity_projection(old_entity_key)

    return updated
