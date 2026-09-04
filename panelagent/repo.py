"""Database repository with no global state."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone


class Repo:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def stats(self) -> dict[str, int]:
        tables = (
            "instruments",
            "channels",
            "channel_mapping",
            "fluorochrome_spectra",
            "fluorochrome_aliases",
            "fluorochrome_brightness",
            "antibodies",
        )
        return {table: self.connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables}

    def list_dyes(self, laser: str | None = None) -> list[dict]:
        sql = """SELECT DISTINCT s.*, b.brightness, cm.channel, c.laser
                 FROM fluorochrome_spectra s
                 LEFT JOIN fluorochrome_brightness b ON b.name=s.name
                 LEFT JOIN channel_mapping cm ON cm.fluorochrome=s.name
                 LEFT JOIN channels c ON c.instrument_id=cm.instrument_id AND c.channel=cm.channel"""
        params: tuple = ()
        if laser:
            sql += " WHERE c.laser=?"
            params = (laser,)
        return [dict(row) for row in self.connection.execute(sql + " ORDER BY s.name", params)]

    def list_channels(self, laser: str | None = None) -> list[dict]:
        sql = "SELECT c.*, i.vendor, i.model FROM channels c JOIN instruments i ON i.id=c.instrument_id"
        params: tuple = ()
        if laser:
            sql += " WHERE c.laser=?"
            params = (laser,)
        return [dict(row) for row in self.connection.execute(sql + " ORDER BY c.channel", params)]

    def antibodies(
        self, library: str | None = None, target: str | None = None, flag: str | None = None, keyword: str | None = None
    ) -> list[dict]:
        clauses, params = [], []
        if library:
            clauses.append("a.library=?")
            params.append(library)
        if target:
            clauses.append("lower(COALESCE(a.target,''))=lower(?)")
            params.append(target)
        if flag:
            clauses.append("a.quality_flag=?")
            params.append(flag)
        if keyword:
            clauses.append(
                "(COALESCE(a.target,'') LIKE ? OR COALESCE(a.fluorochrome,'') LIKE ? "
                "OR COALESCE(a.clone_name,'') LIKE ? OR COALESCE(a.brand,'') LIKE ?)"
            )
            params.extend([f"%{keyword}%"] * 4)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = "SELECT a.* FROM antibodies a" + where + " ORDER BY a.library,a.target,a.id"
        results = [dict(row) for row in self.connection.execute(sql, params)]
        for row in results:
            row["target"] = row["target"] or "-"
            row["fluorochrome"] = row["fluorochrome"] or "-"
        return results

    def annotate(self, antibody_id: int, flag: str, note: str | None, library: str | None = None) -> dict | None:
        if flag not in {"good", "warn", "bad"}:
            raise ValueError("flag must be good, warn, or bad")
        where = "id=? AND library=?" if library else "id=?"
        params = (flag, note, datetime.now(timezone.utc).isoformat(), antibody_id)
        if library:
            params += (library,)
        with self.connection:
            self.connection.execute(
                f"UPDATE antibodies SET quality_flag=?,quality_notes=?,quality_updated_at=? WHERE {where}",
                params,
            )
        row = self.connection.execute(
            f"SELECT * FROM antibodies WHERE {where}", (antibody_id, library) if library else (antibody_id,)
        ).fetchone()
        return dict(row) if row else None
