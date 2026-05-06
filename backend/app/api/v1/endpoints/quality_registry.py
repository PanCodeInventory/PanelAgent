"""Quality Registry API endpoints — antibody quality issue lifecycle.

Endpoints:
    POST   /quality-registry/issues                     — create issue
    GET    /quality-registry/issues                     — list issues
    GET    /quality-registry/issues/{issue_id}          — issue detail
    GET    /quality-registry/issues/{issue_id}/history  — audit history
    POST   /quality-registry/candidates/lookup          — candidate lookup
    POST   /quality-registry/candidates/confirm         — confirm candidate
    GET    /quality-registry/review-queue               — manual review queue
    POST   /quality-registry/review-queue/{issue_id}/resolve — resolve review
"""

import importlib
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ....core.config import get_settings, project_root, resolve_static_data_path
from ....services.inventory_loader import load_inventory

# ---------------------------------------------------------------------------
# Lazy schema imports (importlib pattern used by other endpoint modules)
# ---------------------------------------------------------------------------

_schemas = importlib.import_module("backend.app.schemas.quality_registry")
QualityIssueCreate = _schemas.QualityIssueCreate
QualityIssueResponse = _schemas.QualityIssueResponse
CandidateLookupRequest = _schemas.CandidateLookupRequest
CandidateLookupResponse = _schemas.CandidateLookupResponse
CandidateMatch = _schemas.CandidateMatch
EntityKey = _schemas.EntityKey
_normalize_marker = _schemas._normalize_marker

_store_module = importlib.import_module("backend.app.services.quality_registry_store")
QualityRegistryStore = _store_module.QualityRegistryStore
_proj_module = importlib.import_module("backend.app.services.quality_projection")
QualityProjector = _proj_module.QualityProjector

router = APIRouter(prefix="/quality-registry")

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

_store = QualityRegistryStore()
_projector = QualityProjector(_store)

# ---------------------------------------------------------------------------
# Inline request schemas
# ---------------------------------------------------------------------------


class CandidateConfirmWithIssue(BaseModel):
    """Confirm a candidate entity selection for a specific issue."""

    issue_id: str = Field(min_length=1)
    entity_key: EntityKey


class ResolveReviewRequest(BaseModel):
    """Resolve a manual review item."""

    reviewer: str = Field(min_length=1)
    entity_key: Optional[EntityKey] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_inventory_path(species: str | None) -> Path | None:
    """Resolve the inventory CSV path for a given species."""
    if not species:
        return None
    settings = get_settings()
    root = project_root()
    inventory_dir = root / settings.INVENTORY_DIR
    mapping = settings.SPECIES_INVENTORY_MAP

    # 1. Exact match
    filename = mapping.get(species)
    if filename:
        return inventory_dir / filename

    # 2. Case-insensitive match
    species_lower = species.lower()
    for key, val in mapping.items():
        if key.lower() == species_lower:
            return inventory_dir / val

    # 3. Extract base name (e.g., "Mouse" from "Mouse (小鼠)") and match
    base = species.split("(")[0].split("（")[0].strip()
    if base and base.lower() != species_lower:
        for key, val in mapping.items():
            if key.lower() == base.lower():
                return inventory_dir / val

    return None


def _load_inventory_df(inventory_path: Path):
    return load_inventory(inventory_path, include_viability=False)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/issues", response_model=QualityIssueResponse)
async def create_issue(payload: QualityIssueCreate) -> QualityIssueResponse:
    """Create a new quality issue and trigger projection update."""
    issue = _store.create_issue(payload)
    _projector.update_projection(issue.id)

    # Auto-route to pending_review if no clone was provided (no candidate match)
    if not payload.clone:
        issue = _store.send_to_review(issue.id)

    return issue


@router.post("/candidates/lookup", response_model=CandidateLookupResponse)
async def candidate_lookup(payload: CandidateLookupRequest) -> CandidateLookupResponse:
    """Look up candidate antibody matches from inventory.

    Simple heuristic: filter inventory by marker and fluorochrome,
    rank by exactness of match.
    """
    candidates: list[CandidateMatch] = []

    # Resolve inventory path from species
    inventory_path = _resolve_inventory_path(payload.species)
    if inventory_path is None or not inventory_path.exists():
        return CandidateLookupResponse(candidates=[])

    try:
        df = _load_inventory_df(inventory_path)
    except Exception:
        return CandidateLookupResponse(candidates=[])

    if df is None or df.empty:
        return CandidateLookupResponse(candidates=[])

    # Filter by marker if provided
    norm_marker = _normalize_marker(payload.marker) if payload.marker else None
    fluorochrome = payload.fluorochrome
    brand_filter = payload.brand.strip().lower() if payload.brand else None

    for _, row in df.iterrows():
        target = str(row.get("Target", "")).strip()
        fluor = str(row.get("Fluorescein", "")).strip()
        clone = str(row.get("Clone", "")).strip()
        brand = str(row.get("Brand", "")).strip()
        catalog = str(row.get("Catalog Number", "")).strip()

        if not target or not fluor or not clone or not brand or not catalog:
            continue

        row_norm_marker = _normalize_marker(target)

        # Filter by marker
        if norm_marker and row_norm_marker != norm_marker:
            # Check partial match
            if norm_marker not in row_norm_marker and row_norm_marker not in norm_marker:
                continue

        # Filter by fluorochrome
        if fluorochrome and fluorochrome.lower() not in fluor.lower():
            continue

        # Filter by brand
        if brand_filter and brand_filter not in brand.lower():
            continue

        # Score: exact marker + brand = 1.0, exact marker = 0.8, partial = 0.5
        if norm_marker and row_norm_marker == norm_marker:
            if brand_filter and brand.lower() == brand_filter:
                confidence = 1.0
            else:
                confidence = 0.8
        else:
            confidence = 0.5

        entity_key = EntityKey.from_antibody(
            species=payload.species or "Unknown",
            marker=target,
            clone=clone,
            brand=brand,
            catalog=catalog,
        )

        candidates.append(
            CandidateMatch(
                entity_key=entity_key,
                confidence=confidence,
                source="inventory",
                matched_marker=target,
            )
        )

    # Sort by confidence descending
    candidates.sort(key=lambda c: c.confidence, reverse=True)

    return CandidateLookupResponse(candidates=candidates)


@router.post("/candidates/confirm", response_model=QualityIssueResponse)
async def candidate_confirm(payload: CandidateConfirmWithIssue) -> QualityIssueResponse:
    """Confirm a candidate entity selection for a quality issue."""
    issue = _store.get_issue(payload.issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Validate species compatibility
    if payload.entity_key.species.lower() != issue.feedback_key.species.lower():
        raise HTTPException(
            status_code=422,
            detail=f"Entity species '{payload.entity_key.species}' does not match issue species '{issue.feedback_key.species}'",
        )

    old_entity_key = issue.entity_key

    updated = _store.bind_entity(
        issue_id=payload.issue_id,
        entity_key=payload.entity_key,
        confirmed_by="user",
    )
    _projector.update_projection(payload.issue_id)

    if old_entity_key is not None and old_entity_key != payload.entity_key:
        _projector.recompute_entity_projection(old_entity_key)

    return updated

