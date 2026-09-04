from __future__ import annotations

import sqlite3

import pytest

from panelagent.db import connect, ensure_schema
from panelagent.seed import seed_database


@pytest.fixture
def seeded_conn(tmp_path) -> sqlite3.Connection:
    conn = connect(tmp_path / "core.db")
    ensure_schema(conn)
    seed_database(conn)
    yield conn
    conn.close()
