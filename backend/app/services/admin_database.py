"""Shared SQLite access layer for admin console persistence.

Provides a single database file at ``data/admin_console.sqlite3`` with
two tables: ``llm_settings`` and ``panel_history``.

Initialisation is idempotent — calling :func:`init_db` repeatedly is safe.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from backend.app.core.config import project_root

# ---------------------------------------------------------------------------
# Default database path
# ---------------------------------------------------------------------------

_DEFAULT_DB_RELATIVE = "data/admin_console.sqlite3"


def get_db_path(db_path: str | Path | None = None) -> Path:
    """Return the absolute path to the SQLite database file.

    Args:
        db_path: Explicit path.  When *None* the default
            ``data/admin_console.sqlite3`` relative to the project root
            is used, or — when ``PANELAGENT_DATA_DIR`` is set (single-exe
            mode) — under that writable user directory.

    Returns:
        Absolute :class:`Path` to the database file.
    """
    if db_path is not None:
        return Path(db_path).resolve()
    data_dir = os.environ.get("PANELAGENT_DATA_DIR", "").strip()
    if data_dir:
        return Path(data_dir) / _DEFAULT_DB_RELATIVE
    return project_root() / _DEFAULT_DB_RELATIVE


# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_CREATE_LLM_SETTINGS = """
CREATE TABLE IF NOT EXISTS llm_settings (
    id          INTEGER PRIMARY KEY CHECK (id = 1),
    api_base    TEXT    NOT NULL,
    api_key     TEXT    NULL,
    model_name  TEXT    NOT NULL,
    provider    TEXT    NULL,
    updated_at  TEXT    NOT NULL
);
"""

# Additive migration for databases created before the provider column.
_ADD_PROVIDER_COLUMN = "ALTER TABLE llm_settings ADD COLUMN provider TEXT NULL;"

_CREATE_PANEL_HISTORY = """
CREATE TABLE IF NOT EXISTS panel_history (
    id                 TEXT PRIMARY KEY,
    created_at         TEXT    NOT NULL,
    species            TEXT    NOT NULL,
    inventory_file     TEXT    NULL,
    requested_markers  TEXT    NOT NULL,
    missing_markers    TEXT    NOT NULL,
    selected_panel     TEXT    NOT NULL,
    rationale          TEXT    NOT NULL,
    model_name         TEXT    NOT NULL,
    api_base           TEXT    NOT NULL
);
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db(db_path: str | Path | None = None) -> Path:
    """Ensure the database file and both tables exist.

    Creates the parent directory and the two tables (``llm_settings``,
    ``panel_history``) if they do not already exist.  Repeated calls are
    idempotent — ``CREATE TABLE IF NOT EXISTS`` guarantees this.

    Args:
        db_path: Explicit database path.  Defaults to
            ``data/admin_console.sqlite3`` under the project root.

    Returns:
        The resolved :class:`Path` of the database file.
    """
    path = get_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(_CREATE_LLM_SETTINGS)
        # Idempotent migration: add provider column to pre-existing tables.
        # sqlite3 raises OperationalError "duplicate column name" if it exists.
        try:
            conn.execute(_ADD_PROVIDER_COLUMN)
        except sqlite3.OperationalError:
            pass
        conn.execute(_CREATE_PANEL_HISTORY)
        conn.commit()
    finally:
        conn.close()

    return path


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Return a :class:`sqlite3.Connection` with row factory set to :class:`dict`.

    Ensures the database is initialised before opening the connection.

    Args:
        db_path: Explicit database path (same semantics as :func:`init_db`).

    Returns:
        An open :class:`sqlite3.Connection`.
    """
    path = get_db_path(db_path)
    if not path.exists():
        init_db(db_path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn
