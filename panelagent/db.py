"""SQLite connection and schema management."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1


def default_db_path() -> Path:
    return Path(os.environ.get("PANELAGENT_DB", "~/.local/share/panelagent/panelagent.db")).expanduser()


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    db_path = Path(path).expanduser() if path is not None else default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS instruments(
              id INTEGER PRIMARY KEY,
              vendor TEXT NOT NULL, model TEXT NOT NULL,
              UNIQUE(vendor, model)
            );
            CREATE TABLE IF NOT EXISTS channels(
              instrument_id INTEGER NOT NULL REFERENCES instruments(id),
              channel TEXT NOT NULL, laser TEXT,
              PRIMARY KEY(instrument_id, channel)
            );
            CREATE TABLE IF NOT EXISTS channel_mapping(
              instrument_id INTEGER NOT NULL REFERENCES instruments(id),
              fluorochrome TEXT NOT NULL, channel TEXT NOT NULL,
              PRIMARY KEY(instrument_id, fluorochrome)
            );
            CREATE TABLE IF NOT EXISTS fluorochrome_spectra(
              name TEXT PRIMARY KEY, peak_nm REAL, sigma REAL,
              color TEXT, category TEXT
            );
            CREATE TABLE IF NOT EXISTS fluorochrome_aliases(
              alias TEXT PRIMARY KEY,
              canonical TEXT NOT NULL REFERENCES fluorochrome_spectra(name)
            );
            CREATE TABLE IF NOT EXISTS fluorochrome_brightness(
              name TEXT PRIMARY KEY,
              brightness INTEGER NOT NULL CHECK(brightness BETWEEN 1 AND 5)
            );
            CREATE TABLE IF NOT EXISTS antibodies(
              id INTEGER PRIMARY KEY,
              library TEXT NOT NULL, target TEXT,
              fluorochrome TEXT, clone_name TEXT, brand TEXT,
              catalog_number TEXT, extra JSON, quality_flag TEXT,
              quality_notes TEXT, quality_updated_at TEXT,
              source_file TEXT, imported_at TEXT,
              UNIQUE(library, target, fluorochrome, clone_name, catalog_number)
            );
            CREATE INDEX IF NOT EXISTS idx_antibodies_target
              ON antibodies(library, target);
            PRAGMA user_version=1;
            """
        )


def schema_version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])
