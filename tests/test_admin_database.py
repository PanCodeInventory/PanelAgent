"""Tests for admin_database: schema bootstrap and idempotent re-init."""

import sqlite3
from pathlib import Path

import pytest

from backend.app.services.admin_database import get_connection, get_db_path, init_db


class TestGetDbPath:
    def test_explicit_path_returned_as_resolved(self, tmp_path: Path):
        db_file = tmp_path / "test.sqlite3"
        result = get_db_path(str(db_file))
        assert result == db_file.resolve()

    def test_none_returns_project_root_default(self):
        result = get_db_path(None)
        assert result.name == "admin_console.sqlite3"
        assert "data" in str(result.parent)


class TestInitDb:
    def test_creates_database_file(self, tmp_path: Path):
        db_file = tmp_path / "subdir" / "test.sqlite3"
        result = init_db(str(db_file))
        assert result.exists()

    def test_creates_parent_directory(self, tmp_path: Path):
        db_file = tmp_path / "deep" / "nested" / "dir" / "test.sqlite3"
        init_db(str(db_file))
        assert db_file.parent.exists()

    def test_llm_settings_table_exists(self, tmp_path: Path):
        db_file = tmp_path / "test.sqlite3"
        init_db(str(db_file))
        conn = sqlite3.connect(str(db_file))
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='llm_settings'"
        ).fetchall()
        conn.close()
        assert len(tables) == 1

    def test_panel_history_table_exists(self, tmp_path: Path):
        db_file = tmp_path / "test.sqlite3"
        init_db(str(db_file))
        conn = sqlite3.connect(str(db_file))
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='panel_history'"
        ).fetchall()
        conn.close()
        assert len(tables) == 1

    def test_idempotent_reinit_no_error(self, tmp_path: Path):
        db_file = tmp_path / "test.sqlite3"
        init_db(str(db_file))
        init_db(str(db_file))
        init_db(str(db_file))
        conn = sqlite3.connect(str(db_file))
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        conn.close()
        assert len(tables) == 2

    def test_wal_journal_mode(self, tmp_path: Path):
        db_file = tmp_path / "test.sqlite3"
        init_db(str(db_file))
        conn = sqlite3.connect(str(db_file))
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        assert mode == "wal"


class TestGetConnection:
    def test_returns_connection_with_row_factory(self, tmp_path: Path):
        db_file = tmp_path / "test.sqlite3"
        init_db(str(db_file))
        conn = get_connection(str(db_file))
        assert conn.row_factory is sqlite3.Row
        conn.close()

    def test_auto_inits_if_missing(self, tmp_path: Path):
        db_file = tmp_path / "auto_init.sqlite3"
        conn = get_connection(str(db_file))
        assert db_file.exists()
        conn.close()

    def test_connection_queryable(self, tmp_path: Path):
        db_file = tmp_path / "test.sqlite3"
        init_db(str(db_file))
        conn = get_connection(str(db_file))
        row = conn.execute("SELECT 1 AS val").fetchone()
        assert row["val"] == 1
        conn.close()
