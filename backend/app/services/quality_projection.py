"""Incremental antibody-level quality projection.

On each issue mutation (create / bind / resolve), the projection for the
affected antibody is recomputed from the store's current issue set.
Deterministic deduplication and stable ordering ensure reproducible output.

Storage layout:
    {store._data_dir}/projections/{key_hash}.json
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from backend.app.schemas.quality_registry import (
    EntityKey,
    FeedbackKey,
    QualityIssueResponse,
)
from backend.app.services.quality_registry_store import QualityRegistryStore


# ---------------------------------------------------------------------------
# Projection record (internal model — supports both bound & unbound)
# ---------------------------------------------------------------------------

class ProjectionRecord(BaseModel):
    """Aggregated quality view for a single antibody (bound or unbound)."""

    entity_key: Optional[EntityKey] = None
    feedback_key: Optional[FeedbackKey] = None
    issue_count: int = Field(ge=0)
    latest_issues: list[str] = Field(default_factory=list)
    aggregate_status: str = "clean"
    dedup_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _key_hash(
    entity_key: Optional[EntityKey] = None,
    feedback_key: Optional[FeedbackKey] = None,
) -> str:
    """Deterministic hex hash for an entity_key or feedback_key tuple."""
    if entity_key is not None:
        t = entity_key._identity_tuple()
    elif feedback_key is not None:
        t = (
            feedback_key.species,
            feedback_key.normalized_marker,
            feedback_key.fluorochrome,
            feedback_key.brand,
            feedback_key.clone,
        )
    else:
        raise ValueError("Must provide entity_key or feedback_key")
    return hashlib.sha256(str(t).encode()).hexdigest()[:16]


def _atomic_write(path: Path, data: str) -> None:
    """Write data atomically: temp file then rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(tmp_path, str(path))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# QualityProjector
# ---------------------------------------------------------------------------

class QualityProjector:
    """Incremental per-antibody quality projection.

    Call ``update_projection(issue_id)`` after any issue mutation to keep
    the derived view in sync with the store.
    """

    def __init__(self, store: QualityRegistryStore) -> None:
        self._store = store
        self._projections_dir = Path(store._data_dir) / "projections"
        self._projections_dir.mkdir(parents=True, exist_ok=True)

    # -- Private helpers --------------------------------------------------

    def _projection_path(self, *, entity_key=None, feedback_key=None) -> Path:
        h = _key_hash(entity_key=entity_key, feedback_key=feedback_key)
        return self._projections_dir / f"{h}.json"

    def _persist(self, proj: ProjectionRecord) -> None:
        """Write projection to disk atomically."""
        if proj.entity_key is not None:
            path = self._projection_path(entity_key=proj.entity_key)
        else:
            path = self._projection_path(feedback_key=proj.feedback_key)
        _atomic_write(path, proj.model_dump_json(indent=2))

    def _remove(self, *, entity_key=None, feedback_key=None) -> None:
        """Delete a projection file (e.g. when all issues are bound away)."""
        path = self._projection_path(entity_key=entity_key, feedback_key=feedback_key)
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    def _load_projection_file(self, path: Path) -> Optional[ProjectionRecord]:
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        return ProjectionRecord.model_validate(raw)

    @staticmethod
    def _deduplicate(issues: list[QualityIssueResponse]) -> list[QualityIssueResponse]:
        """Collapse semantically identical issue texts, keeping the earliest.

        Two issues are identical if ``issue_text.strip().lower()`` matches.
        On collision the one with the smaller ``(created_at, issue_id)`` wins.
        """
        seen: dict[str, QualityIssueResponse] = {}
        for issue in issues:
            text_key = issue.issue_text.strip().lower()
            if text_key not in seen:
                seen[text_key] = issue
            else:
                existing = seen[text_key]
                if (issue.created_at, issue.id) < (existing.created_at, existing.id):
                    seen[text_key] = issue
        return list(seen.values())

    def _build_projection(
        self,
        issues: list[QualityIssueResponse],
        *,
        entity_key: Optional[EntityKey] = None,
        feedback_key: Optional[FeedbackKey] = None,
    ) -> ProjectionRecord:
        """Compute a ProjectionRecord from a list of issues for one key."""
        if not issues:
            return ProjectionRecord(
                entity_key=entity_key,
                feedback_key=feedback_key,
                issue_count=0,
                latest_issues=[],
                aggregate_status="clean",
                dedup_count=0,
            )

        deduped = self._deduplicate(issues)

        # Stable ordering: created_at ascending, then issue_id for tiebreak
        deduped.sort(key=lambda i: (i.created_at, i.id))

        # Aggregate status: "flagged" if any open issue remains
        has_open = any(i.status != "resolved" for i in deduped)
        aggregate_status = "flagged" if has_open else "clean"

        # Top 5 latest issues (last 5 in ascending order = most recent 5)
        latest = deduped[-5:] if len(deduped) > 5 else list(deduped)
        latest_issues = [i.issue_text for i in latest]

        return ProjectionRecord(
            entity_key=entity_key,
            feedback_key=feedback_key,
            issue_count=len(deduped),
            latest_issues=latest_issues,
            aggregate_status=aggregate_status,
            dedup_count=len(issues) - len(deduped),
        )

    def _compute_entity_projection(self, entity_key: EntityKey) -> ProjectionRecord:
        all_issues = self._store.list_issues()
        matching = [i for i in all_issues if i.entity_key is not None and i.entity_key == entity_key]
        return self._build_projection(matching, entity_key=entity_key)

    def _compute_feedback_projection(self, feedback_key: FeedbackKey) -> ProjectionRecord:
        all_issues = self._store.list_issues(feedback_key=feedback_key)
        # Only unbound issues belong to the feedback-key projection
        matching = [i for i in all_issues if i.entity_key is None]
        return self._build_projection(matching, feedback_key=feedback_key)

    # -- Public API -------------------------------------------------------

    def update_projection(self, issue_id: str) -> ProjectionRecord:
        """Recompute projections affected by *issue_id* and persist them.

        Called after any issue mutation (create, bind, resolve).  Returns the
        *primary* projection — the one keyed by the issue's current identity.
        """
        issue = self._store.get_issue(issue_id)
        if issue is None:
            raise ValueError(f"Issue {issue_id} not found")

        if issue.entity_key is not None:
            # Bound issue → compute entity projection
            proj = self._compute_entity_projection(issue.entity_key)
            self._persist(proj)

            # Also recompute the feedback-key projection (issue may have left it)
            fb_proj = self._compute_feedback_projection(issue.feedback_key)
            if fb_proj.issue_count > 0:
                self._persist(fb_proj)
            else:
                self._remove(feedback_key=issue.feedback_key)

            return proj

        # Unbound issue → compute feedback-key projection
        proj = self._compute_feedback_projection(issue.feedback_key)
        self._persist(proj)
        return proj

    def recompute_entity_projection(self, entity_key: EntityKey) -> ProjectionRecord:
        """Force recompute and persist projection for a given entity key.

        Use when an issue is re-bound from one entity to another to clean
        up the stale projection of the old entity.
        """
        proj = self._compute_entity_projection(entity_key)
        if proj.issue_count > 0:
            self._persist(proj)
        else:
            self._remove(entity_key=entity_key)
        return proj

    def get_projection(
        self,
        *,
        entity_key: Optional[EntityKey] = None,
        feedback_key: Optional[FeedbackKey] = None,
    ) -> Optional[ProjectionRecord]:
        """Look up a persisted projection by entity_key (bound) or feedback_key (unbound)."""
        if entity_key is not None:
            path = self._projection_path(entity_key=entity_key)
        elif feedback_key is not None:
            path = self._projection_path(feedback_key=feedback_key)
        else:
            return None
        return self._load_projection_file(path)

    def get_projections_for_markers(
        self, marker_names: list[str]
    ) -> list[ProjectionRecord]:
        """Find all projections matching any normalised marker in *marker_names*.

        Returns projections sorted by ``issue_count`` descending (most
        problematic antibodies first).
        """
        from backend.app.schemas.quality_registry import _normalize_marker

        targets = {_normalize_marker(m) for m in marker_names}
        results: list[tuple[ProjectionRecord, str]] = []

        for path in self._projections_dir.glob("*.json"):
            proj = self._load_projection_file(path)
            if proj is None:
                continue
            nm: Optional[str] = None
            if proj.entity_key is not None:
                nm = proj.entity_key.normalized_marker
            elif proj.feedback_key is not None:
                nm = proj.feedback_key.normalized_marker
            if nm is not None and nm in targets:
                results.append((proj, nm))

        # Sort by issue_count desc, then normalized_marker alpha for tiebreak
        results.sort(key=lambda t: (-t[0].issue_count, t[1]))
        return [r[0] for r in results]
