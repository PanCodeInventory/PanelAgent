"""SQLite-backed, LLM-free flow cytometry panel core."""

from .db import connect, ensure_schema, schema_version
from .engine import diagnose_conflicts, find_valid_panels, generate_candidates
from .repo import Repo
from .resolve import resolve_fluorochrome

__version__ = "0.1.0"

__all__ = [
    "Repo",
    "connect",
    "diagnose_conflicts",
    "ensure_schema",
    "find_valid_panels",
    "generate_candidates",
    "resolve_fluorochrome",
    "schema_version",
]
