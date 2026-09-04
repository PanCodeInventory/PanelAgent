"""Thin FastMCP wrapper around the PanelAgent core."""

from __future__ import annotations

from dataclasses import asdict

try:
    from mcp.server.fastmcp import FastMCP  # mcp 1.x
except ImportError:
    try:
        from mcp.server.mcpserver import MCPServer as FastMCP  # mcp 2.x: FastMCP renamed
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise ImportError("MCP support requires: pip install panelagent[mcp]") from exc

from .db import connect, ensure_schema
from .engine import diagnose_conflicts, generate_candidates
from .repo import Repo
from .resolve import resolve_fluorochrome


def create_server(db_path: str | None = None) -> FastMCP:
    server = FastMCP("panelagent")

    def session():
        conn = connect(db_path)
        ensure_schema(conn)
        return conn

    @server.tool()
    def list_fluorochromes(laser: str | None = None) -> list[dict]:
        """List known fluorochromes, optionally restricted by laser."""
        with session() as conn:
            return Repo(conn).list_dyes(laser)

    @server.tool()
    def get_fluorochrome(name: str) -> dict | None:
        """Resolve one exact fluorochrome name or configured alias."""
        with session() as conn:
            value = resolve_fluorochrome(conn, name)
            return asdict(value) if value else None

    @server.tool()
    def list_channels(laser: str | None = None) -> list[dict]:
        """List instrument channels."""
        with session() as conn:
            return Repo(conn).list_channels(laser)

    @server.tool()
    def search_antibodies(
        library: str | None = None, target: str | None = None, keyword: str | None = None
    ) -> list[dict]:
        """Search antibody inventory."""
        with session() as conn:
            return Repo(conn).antibodies(library=library, target=target, keyword=keyword)

    @server.tool()
    def generate_panel(library: str, markers: list[str], max_solutions: int = 10, include_bad: bool = False) -> dict:
        """Generate channel-conflict-free panel candidates."""
        with session() as conn:
            return generate_candidates(conn, library, markers, max_solutions, include_bad)

    @server.tool()
    def diagnose_panel(library: str, markers: list[str]) -> dict:
        """Diagnose missing markers and channel pigeonhole conflicts."""
        with session() as conn:
            return diagnose_conflicts(conn, library, markers)

    @server.tool()
    def db_stats() -> dict[str, int]:
        """Return row counts for core tables."""
        with session() as conn:
            return Repo(conn).stats()

    return server


def run(db_path: str | None = None) -> None:
    create_server(db_path).run(transport="stdio")
