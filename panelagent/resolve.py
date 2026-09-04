"""Exact fluorochrome and alias resolution."""

from __future__ import annotations

import sqlite3

from .models import Fluorochrome


def resolve_fluorochrome(conn: sqlite3.Connection, name: str) -> Fluorochrome | None:
    alias = conn.execute("SELECT canonical FROM fluorochrome_aliases WHERE alias = ?", (name,)).fetchone()
    canonical = alias["canonical"] if alias else name
    spectrum = conn.execute("SELECT * FROM fluorochrome_spectra WHERE name = ?", (canonical,)).fetchone()
    brightness = conn.execute(
        "SELECT b.brightness FROM fluorochrome_brightness b "
        "LEFT JOIN fluorochrome_aliases a ON a.alias=b.name "
        "WHERE b.name IN (?, ?) OR a.canonical=? "
        "ORDER BY CASE b.name WHEN ? THEN 0 WHEN ? THEN 1 ELSE 2 END LIMIT 1",
        (name, canonical, canonical, name, canonical),
    ).fetchone()
    mapping = conn.execute(
        "SELECT cm.channel, c.laser FROM channel_mapping cm "
        "LEFT JOIN channels c ON c.instrument_id=cm.instrument_id AND c.channel=cm.channel "
        "WHERE cm.fluorochrome IN (?, ?) "
        "ORDER BY CASE cm.fluorochrome WHEN ? THEN 0 ELSE 1 END LIMIT 1",
        (name, canonical, name),
    ).fetchone()
    if not spectrum and not brightness and not mapping:
        return None
    return Fluorochrome(
        name=name,
        canonical_name=canonical,
        peak_nm=spectrum["peak_nm"] if spectrum else None,
        sigma=spectrum["sigma"] if spectrum else None,
        color=spectrum["color"] if spectrum else None,
        category=spectrum["category"] if spectrum else None,
        brightness=brightness["brightness"] if brightness else None,
        channel=mapping["channel"] if mapping else None,
        laser=mapping["laser"] if mapping else None,
    )
