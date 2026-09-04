from __future__ import annotations

import json
import os
import sys

import anyio
import pytest

pytest.importorskip("mcp")

from mcp import ClientSession, StdioServerParameters, stdio_client

from panelagent.db import connect, ensure_schema
from panelagent.importers import import_antibody_csv
from panelagent.seed import seed_database


def test_mcp_stdio_stats_and_search(tmp_path):
    db_path = tmp_path / "mcp.db"
    conn = connect(db_path)
    ensure_schema(conn)
    seed_database(conn)
    inventory = os.path.join(os.path.dirname(__file__), "../../inventory/panel_inventory.csv")
    import_antibody_csv(conn, inventory, "Mouse")
    conn.close()

    async def exercise() -> None:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "panelagent", "mcp", "--db", str(db_path)],
        )
        async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            stats = await session.call_tool("db_stats")

            def _is_err(r):
                return getattr(r, "is_error", None) if hasattr(r, "is_error") else r.isError

            def _structured(r):
                return r.structured_content if hasattr(r, "structured_content") else r.structuredContent

            assert not _is_err(stats)
            stats_value = json.loads(stats.content[0].text)
            assert stats_value["antibodies"] == 5
            search = await session.call_tool("search_antibodies", {"library": "Mouse", "target": "CD3"})
            assert not _is_err(search)
            assert _structured(search)["result"][0]["target"] == "CD3"

    anyio.run(exercise)
