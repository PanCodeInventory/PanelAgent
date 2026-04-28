"""Pydantic schemas for the antibody quality registry.

Dual-key identity contracts:
- FeedbackKey: submission identity (clone optional)
- EntityKey: canonical antibody identity (all required, lot as metadata)
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Marker normalisation (mirrors data_preprocessing.normalize_marker_name)
# ---------------------------------------------------------------------------

def _normalize_marker(name: str) -> str:
    """Normalise a marker name: strip parens, lowercase, remove dashes/spaces, handle CD8a/b suffixes."""
    if not isinstance(name, str):
        return ""
    name = re.sub(r"\s*\(.*?\)", "", name)
    name = name.lower().replace("-", "").replace(" ", "")
    if name.endswith("a") or name.endswith("b"):
        name = name[:-1]
    return name


# ---------------------------------------------------------------------------
# A. FeedbackKey — submission identity (clone optional)
# ---------------------------------------------------------------------------

class FeedbackKey(BaseModel):
    """Identity key for a quality-feedback submission.

    Equality & hashing are based on all non-None fields, so two submissions
    that differ only in clone (where one has clone=None) are *not* equal.
    """

    model_config = ConfigDict(frozen=True)

    species: str
    normalized_marker: str
    fluorochrome: str
    brand: str
    clone: Optional[str] = None

    @classmethod
    def from_submission(
        cls,
        species: str,
        marker: str,
        fluorochrome: str,
        brand: str,
        clone: Optional[str] = None,
    ) -> FeedbackKey:
        """Build a FeedbackKey, normalising the marker name automatically."""
        return cls(
            species=species,
            normalized_marker=_normalize_marker(marker),
            fluorochrome=fluorochrome,
            brand=brand,
            clone=clone,
        )


# ---------------------------------------------------------------------------
# B. EntityKey — canonical antibody identity (all required, lot as metadata)
# ---------------------------------------------------------------------------

class EntityKey(BaseModel):
    """Canonical identity for a specific antibody reagent.

    Equality & hashing are based on the 5 required fields.
    ``lot_number`` is tracked as metadata but is NOT part of identity.
    """

    model_config = ConfigDict(frozen=True)

    species: str
    normalized_marker: str
    clone: str
    brand: str
    catalog_number: str
    lot_number: Optional[str] = None

    def _identity_tuple(self) -> tuple:
        return (self.species, self.normalized_marker, self.clone, self.brand, self.catalog_number)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EntityKey):
            return NotImplemented
        return self._identity_tuple() == other._identity_tuple()

    def __hash__(self) -> int:
        return hash(self._identity_tuple())

    @classmethod
    def from_antibody(
        cls,
        species: str,
        marker: str,
        clone: str,
        brand: str,
        catalog: str,
        lot: Optional[str] = None,
    ) -> EntityKey:
        """Build an EntityKey, normalising the marker name automatically."""
        return cls(
            species=species,
            normalized_marker=_normalize_marker(marker),
            clone=clone,
            brand=brand,
            catalog_number=catalog,
            lot_number=lot,
        )


# ---------------------------------------------------------------------------
# C. Quality Issue Record
# ---------------------------------------------------------------------------

class QualityIssueCreate(BaseModel):
    """Payload for submitting a new quality issue."""

    issue_text: str = Field(min_length=1, max_length=2000)
    reported_by: str = Field(min_length=1)
    species: str = Field(min_length=1)
    marker: str = Field(min_length=1)
    fluorochrome: str = Field(min_length=1)
    brand: str = Field(min_length=1)
    clone: Optional[str] = None

    @model_validator(mode="after")
    def _strip_blank_fields(self) -> QualityIssueCreate:
        if self.issue_text.strip() == "":
            raise ValueError("issue_text must not be blank")
        # Normalize clone: treat whitespace-only as None
        if self.clone is not None and self.clone.strip() == "":
            self.clone = None
        return self


class QualityIssueUpdate(BaseModel):
    """Payload for editing an existing quality issue.

    Only ``issue_text`` and ``reported_by`` may be changed.
    ``feedback_key``, ``entity_key``, and ``status`` are immutable via this schema.
    """

    issue_text: str = Field(min_length=1, max_length=2000)
    reported_by: str = Field(min_length=1)

    @model_validator(mode="after")
    def _strip_blank_fields(self) -> QualityIssueUpdate:
        if self.issue_text.strip() == "":
            raise ValueError("issue_text must not be blank")
        return self


class QualityIssueResponse(BaseModel):
    """Full representation of a persisted quality issue."""

    id: str
    feedback_key: FeedbackKey
    entity_key: Optional[EntityKey] = None
    issue_text: str
    reported_by: str
    status: str = "submitted"
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# D. Candidate Match (lookup disambiguation)
# ---------------------------------------------------------------------------

class CandidateLookupRequest(BaseModel):
    """Request to look up candidate antibody matches."""

    text: str = Field(min_length=1, description="Natural-language description of the antibody.")
    species: Optional[str] = None
    marker: Optional[str] = None
    fluorochrome: Optional[str] = None
    brand: Optional[str] = None


class CandidateMatch(BaseModel):
    """A single candidate match from the lookup."""

    entity_key: EntityKey
    confidence: float = Field(ge=0.0, le=1.0)
    source: str
    matched_marker: Optional[str] = None


class CandidateLookupResponse(BaseModel):
    """Response containing candidate antibody matches."""

    candidates: list[CandidateMatch] = Field(default_factory=list)


class CandidateConfirmRequest(BaseModel):
    """Confirm selection of a candidate entity."""

    entity_key: EntityKey


# ---------------------------------------------------------------------------
# E. Manual Review Item
# ---------------------------------------------------------------------------

class ReviewItemResponse(BaseModel):
    """A quality issue queued for manual review."""

    id: str
    feedback_key: FeedbackKey
    entity_key: Optional[EntityKey] = None
    issue_text: str
    reported_by: str
    status: str = "pending_review"
    reviewer: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# F. Organized Projection (per-antibody summary)
# ---------------------------------------------------------------------------

class AntibodyQualityProjection(BaseModel):
    """Aggregated quality view for a single antibody reagent."""

    entity_key: EntityKey
    issue_count: int = Field(ge=0)
    latest_issues: list[str] = Field(default_factory=list)
    aggregate_status: str = "clean"


# ---------------------------------------------------------------------------
# G. Prompt Context Payload
# ---------------------------------------------------------------------------

class QualityPromptContext(BaseModel):
    """Formatted quality context ready for injection into an LLM prompt."""

    entries: list[str] = Field(default_factory=list)
    total_chars: int = 0
    truncated: bool = False
