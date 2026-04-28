"""Persistence layer for panel design history entries."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from backend.app.services.admin_database import get_connection, init_db


class PanelHistoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    species: str
    inventory_file: Optional[str] = None
    requested_markers: list[str]
    missing_markers: list[str]
    selected_panel: list[dict[str, Any]]
    rationale: str
    model_name: str
    api_base: str


class PanelHistoryStore:
    """CRUD operations for panel design history stored in SQLite."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = db_path
        init_db(db_path)

    def create_entry(self, entry: PanelHistoryEntry) -> PanelHistoryEntry:
        """Insert a new history entry and return it (with id / created_at populated)."""
        conn = get_connection(self._db_path)
        try:
            conn.execute(
                "INSERT INTO panel_history "
                "(id, created_at, species, inventory_file, requested_markers, "
                "missing_markers, selected_panel, rationale, model_name, api_base) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    entry.id,
                    entry.created_at,
                    entry.species,
                    entry.inventory_file,
                    json.dumps(entry.requested_markers),
                    json.dumps(entry.missing_markers),
                    json.dumps(entry.selected_panel),
                    entry.rationale,
                    entry.model_name,
                    entry.api_base,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return entry

    def list_entries(self, limit: int = 50, offset: int = 0) -> list[PanelHistoryEntry]:
        """Return history entries ordered by created_at DESC with pagination."""
        conn = get_connection(self._db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM panel_history ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        finally:
            conn.close()

        return [_row_to_entry(r) for r in rows]

    def get_entry(self, entry_id: str) -> Optional[PanelHistoryEntry]:
        """Return a single entry by id, or None if not found."""
        conn = get_connection(self._db_path)
        try:
            row = conn.execute(
                "SELECT * FROM panel_history WHERE id = ?",
                (entry_id,),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return None
        return _row_to_entry(row)


def _row_to_entry(row: "sqlite3.Row") -> PanelHistoryEntry:  # type: ignore[name-defined]
    """Convert a sqlite3.Row to a PanelHistoryEntry, deserialising JSON fields."""
    return PanelHistoryEntry(
        id=row["id"],
        created_at=row["created_at"],
        species=row["species"],
        inventory_file=row["inventory_file"],
        requested_markers=json.loads(row["requested_markers"]),
        missing_markers=json.loads(row["missing_markers"]),
        selected_panel=json.loads(row["selected_panel"]),
        rationale=row["rationale"],
        model_name=row["model_name"],
        api_base=row["api_base"],
    )
