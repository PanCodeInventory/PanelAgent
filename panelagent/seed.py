"""Load immutable package seed data into SQLite."""

from __future__ import annotations

import json
import sqlite3
from importlib.resources import files

from .models import ImportReport


def _load(name: str) -> dict:
    resource = files("panelagent.data.seed").joinpath(name)
    return json.loads(resource.read_text(encoding="utf-8"))


def infer_laser(channel: str) -> str | None:
    prefix = channel.split("_", 1)[0]
    if prefix.startswith("UV"):
        return "UV"
    return {"B": "Blue", "Y": "Yellow", "R": "Red", "V": "Violet"}.get(prefix[:1])


def seed_database(conn: sqlite3.Connection) -> ImportReport:
    spectra = _load("spectra.json")
    brightness = _load("brightness.json")
    aliases = _load("aliases.json")
    instrument = _load("instruments.json")
    report = ImportReport()
    with conn:
        for name, item in spectra.items():
            conn.execute(
                "INSERT INTO fluorochrome_spectra(name,peak_nm,sigma,color,category) "
                "VALUES(?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET "
                "peak_nm=excluded.peak_nm,sigma=excluded.sigma,color=excluded.color,category=excluded.category",
                (name, item.get("peak"), item.get("sigma"), item.get("color"), item.get("category")),
            )
            report.spectra += 1
        for alias, canonical in aliases.items():
            if alias.startswith("_"):
                continue
            conn.execute(
                "INSERT INTO fluorochrome_aliases VALUES(?,?) "
                "ON CONFLICT(alias) DO UPDATE SET canonical=excluded.canonical",
                (alias, canonical),
            )
            report.aliases += 1
        spectrum_names = set(spectra)
        for name, value in brightness.items():
            canonical = name if name in spectrum_names else aliases.get(name)
            resolved_name = canonical or name
            if canonical is None:
                report.warnings.append(f"Brightness seed has no spectrum or alias: {name}")
            conn.execute(
                "INSERT INTO fluorochrome_brightness VALUES(?,?) "
                "ON CONFLICT(name) DO UPDATE SET brightness=excluded.brightness",
                (resolved_name, value),
            )
            report.brightness += 1
        cursor = conn.execute(
            "INSERT INTO instruments(vendor,model) VALUES(?,?) "
            "ON CONFLICT(vendor,model) DO UPDATE SET vendor=excluded.vendor RETURNING id",
            (instrument["vendor"], instrument["model"]),
        )
        instrument_id = cursor.fetchone()[0]
        report.instruments = 1
        for fluorochrome, channel in instrument["channel_mapping"].items():
            conn.execute(
                "INSERT OR IGNORE INTO channels VALUES(?,?,?)",
                (instrument_id, channel, infer_laser(channel)),
            )
            conn.execute(
                "INSERT INTO channel_mapping VALUES(?,?,?) "
                "ON CONFLICT(instrument_id,fluorochrome) DO UPDATE SET channel=excluded.channel",
                (instrument_id, fluorochrome, channel),
            )
            report.channel_mappings += 1
        report.channels = conn.execute(
            "SELECT count(*) FROM channels WHERE instrument_id=?", (instrument_id,)
        ).fetchone()[0]
    return report
