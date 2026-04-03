"""Dedicated registry persistence layer for antibody quality records.

JSON file-based storage with immutable audit trail.
Every mutation creates an append-only audit event.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from backend.app.schemas.quality_registry import (
    EntityKey,
    FeedbackKey,
    QualityIssueCreate,
    QualityIssueResponse,
)


# ---------------------------------------------------------------------------
# Audit Event model
# ---------------------------------------------------------------------------

class AuditEvent(BaseModel):
    """Immutable record of a single mutation on a quality issue."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    issue_id: str
    action: str
    actor: str
    details: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _atomic_write(path: Path, data: str) -> None:
    """Write data to a file atomically: write to temp, then rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(tmp_path, str(path))
    except BaseException:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _read_json(path: Path) -> list:
    """Read JSON array from file, returning [] if missing/empty."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        return json.loads(content)


def _write_json(path: Path, data: list) -> None:
    """Write list as JSON array atomically."""
    _atomic_write(path, json.dumps(data, indent=2, default=str, ensure_ascii=False))


# ---------------------------------------------------------------------------
# QualityRegistryStore
# ---------------------------------------------------------------------------

class QualityRegistryStore:
    """File-based persistence for quality issue records and audit trail.

    Storage layout:
        {data_dir}/issues.json          — array of QualityIssueResponse dicts
        {data_dir}/audit/{issue_id}.json — per-issue audit event arrays
    """

    def __init__(self, data_dir: str = "data/quality_registry") -> None:
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        (self._data_dir / "audit").mkdir(parents=True, exist_ok=True)

    # -- Private helpers --------------------------------------------------

    def _issues_path(self) -> Path:
        return self._data_dir / "issues.json"

    def _audit_path(self, issue_id: str) -> Path:
        return self._data_dir / "audit" / f"{issue_id}.json"

    def _load_issues(self) -> list[QualityIssueResponse]:
        raw = _read_json(self._issues_path())
        return [QualityIssueResponse(**r) for r in raw]

    def _save_issues(self, issues: list[QualityIssueResponse]) -> None:
        _write_json(self._issues_path(), [i.model_dump(mode="json") for i in issues])

    def _load_audit(self, issue_id: str) -> list[AuditEvent]:
        raw = _read_json(self._audit_path(issue_id))
        return [AuditEvent(**r) for r in raw]

    def _append_audit(self, event: AuditEvent) -> None:
        events = self._load_audit(event.issue_id)
        events.append(event)
        _write_json(self._audit_path(event.issue_id), [e.model_dump(mode="json") for e in events])

    def _find_issue(self, issues: list[QualityIssueResponse], issue_id: str) -> QualityIssueResponse | None:
        for i in issues:
            if i.id == issue_id:
                return i
        return None

    def _update_issue(
        self,
        issues: list[QualityIssueResponse],
        issue_id: str,
        updates: dict,
    ) -> QualityIssueResponse:
        """Find issue by id, apply updates dict, save, return updated."""
        for idx, issue in enumerate(issues):
            if issue.id == issue_id:
                updated_data = issue.model_dump(mode="json")
                updated_data.update(updates)
                updated_data["updated_at"] = _now()
                updated = QualityIssueResponse(**updated_data)
                issues[idx] = updated
                self._save_issues(issues)
                return updated
        raise ValueError(f"Issue {issue_id} not found")

    # -- Public API -------------------------------------------------------

    def create_issue(self, create: QualityIssueCreate) -> QualityIssueResponse:
        """Create a new quality issue record + audit event."""
        issue_id = str(uuid.uuid4())
        now = _now()

        feedback_key = FeedbackKey.from_submission(
            species=create.species,
            marker=create.marker,
            fluorochrome=create.fluorochrome,
            brand=create.brand,
            clone=create.clone,
        )

        response = QualityIssueResponse(
            id=issue_id,
            feedback_key=feedback_key,
            entity_key=None,
            issue_text=create.issue_text,
            reported_by=create.reported_by,
            status="submitted",
            created_at=now,
            updated_at=now,
        )

        # Persist issue
        issues = self._load_issues()
        issues.append(response)
        self._save_issues(issues)

        # Create audit event
        event = AuditEvent(
            issue_id=issue_id,
            action="created",
            actor=create.reported_by,
            details={
                "issue_text": create.issue_text,
                "feedback_key": feedback_key.model_dump(mode="json"),
            },
            timestamp=now,
        )
        self._append_audit(event)

        return response

    def get_issue(self, issue_id: str) -> Optional[QualityIssueResponse]:
        """Return a single issue by ID, or None if not found."""
        issues = self._load_issues()
        return self._find_issue(issues, issue_id)

    def list_issues(
        self,
        feedback_key: Optional[FeedbackKey] = None,
        status: Optional[str] = None,
    ) -> list[QualityIssueResponse]:
        """Return all issues, optionally filtered by feedback_key and/or status."""
        issues = self._load_issues()

        if feedback_key is not None:
            issues = [i for i in issues if i.feedback_key == feedback_key]

        if status is not None:
            issues = [i for i in issues if i.status == status]

        return issues

    def bind_entity(
        self,
        issue_id: str,
        entity_key: EntityKey,
        confirmed_by: str,
    ) -> QualityIssueResponse:
        """Bind an entity key to an issue, changing status to 'confirmed'."""
        issues = self._load_issues()
        found = self._find_issue(issues, issue_id)
        if found is None:
            raise ValueError(f"Issue {issue_id} not found")

        updated = self._update_issue(issues, issue_id, {
            "entity_key": entity_key.model_dump(mode="json"),
            "status": "confirmed",
        })

        # Audit event
        event = AuditEvent(
            issue_id=issue_id,
            action="entity_bound",
            actor=confirmed_by,
            details={
                "entity_key": entity_key.model_dump(mode="json"),
                "previous_status": found.status,
                "new_status": "confirmed",
            },
        )
        self._append_audit(event)

        return updated

    def send_to_review(self, issue_id: str) -> QualityIssueResponse:
        """Transition issue to 'pending_review' status."""
        issues = self._load_issues()
        found = self._find_issue(issues, issue_id)
        if found is None:
            raise ValueError(f"Issue {issue_id} not found")

        updated = self._update_issue(issues, issue_id, {
            "status": "pending_review",
        })

        event = AuditEvent(
            issue_id=issue_id,
            action="status_changed",
            actor="system",
            details={
                "previous_status": found.status,
                "new_status": "pending_review",
            },
        )
        self._append_audit(event)

        return updated

    def resolve_review(
        self,
        issue_id: str,
        reviewer: str,
        entity_key: Optional[EntityKey] = None,
    ) -> QualityIssueResponse:
        """Resolve a review, changing status to 'resolved'."""
        issues = self._load_issues()
        found = self._find_issue(issues, issue_id)
        if found is None:
            raise ValueError(f"Issue {issue_id} not found")

        updates: dict = {"status": "resolved"}
        if entity_key is not None:
            updates["entity_key"] = entity_key.model_dump(mode="json")

        updated = self._update_issue(issues, issue_id, updates)

        event = AuditEvent(
            issue_id=issue_id,
            action="resolved",
            actor=reviewer,
            details={
                "previous_status": found.status,
                "new_status": "resolved",
                **({"entity_key": entity_key.model_dump(mode="json")} if entity_key else {}),
            },
        )
        self._append_audit(event)

        return updated

    def get_history(self, issue_id: str) -> list[AuditEvent]:
        """Return all audit events for an issue (append-only, never mutated).

        Returns a copy to prevent external mutation from affecting stored data.
        """
        events = self._load_audit(issue_id)
        # Return deep copies to enforce immutability
        return [AuditEvent(**e.model_dump()) for e in events]
