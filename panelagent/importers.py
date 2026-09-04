"""Import user-maintained configuration and antibody inventories."""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import ImportReport
from .seed import infer_laser


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _nullable_cell(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return None if cleaned in {"", "-"} else cleaned


def import_instrument_config(conn: sqlite3.Connection, config_dir: str | Path) -> ImportReport:
    directory = Path(config_dir)
    mapping = json.loads((directory / "channel_mapping.json").read_text(encoding="utf-8"))
    spectra = json.loads((directory / "spectral_data.json").read_text(encoding="utf-8"))
    brightness = json.loads((directory / "fluorochrome_brightness.json").read_text(encoding="utf-8"))
    report = ImportReport()
    with conn:
        instrument_id = conn.execute(
            "INSERT INTO instruments(vendor,model) VALUES('Beckman','CytoFLEX') "
            "ON CONFLICT(vendor,model) DO UPDATE SET vendor=excluded.vendor RETURNING id"
        ).fetchone()[0]
        report.instruments = 1
        for name, item in spectra.items():
            if name.startswith("_"):
                continue
            conn.execute(
                "INSERT INTO fluorochrome_spectra VALUES(?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET "
                "peak_nm=excluded.peak_nm,sigma=excluded.sigma,color=excluded.color,category=excluded.category",
                (name, item.get("peak"), item.get("sigma"), item.get("color"), item.get("category")),
            )
            report.spectra += 1
        for name, value in brightness.items():
            spectrum = conn.execute("SELECT 1 FROM fluorochrome_spectra WHERE name=?", (name,)).fetchone()
            alias = (
                None
                if spectrum
                else conn.execute("SELECT canonical FROM fluorochrome_aliases WHERE alias=?", (name,)).fetchone()
            )
            resolved_name = name if spectrum else alias["canonical"] if alias else name
            if not spectrum and not alias:
                report.warnings.append(f"Brightness config has no spectrum or alias: {name}")
            conn.execute(
                "INSERT INTO fluorochrome_brightness VALUES(?,?) ON CONFLICT(name) DO UPDATE SET brightness=excluded.brightness",
                (resolved_name, value),
            )
            report.brightness += 1
        for fluorochrome, channel in mapping.items():
            conn.execute("INSERT OR IGNORE INTO channels VALUES(?,?,?)", (instrument_id, channel, infer_laser(channel)))
            conn.execute(
                "INSERT INTO channel_mapping VALUES(?,?,?) ON CONFLICT(instrument_id,fluorochrome) DO UPDATE SET channel=excluded.channel",
                (instrument_id, fluorochrome, channel),
            )
            report.channel_mappings += 1
        report.channels = conn.execute(
            "SELECT count(*) FROM channels WHERE instrument_id=?", (instrument_id,)
        ).fetchone()[0]
    return report


def import_antibody_csv(conn: sqlite3.Connection, csv_path: str | Path, library: str) -> ImportReport:
    path = Path(csv_path)
    report = ImportReport()
    if path.name.startswith("."):
        return report
    known = {"Target", "Name", "Fluorescein", "Clone", "Brand", "Catalog Number"}
    with path.open(newline="", encoding="utf-8-sig") as handle, conn:
        for row in csv.DictReader(handle):
            meaningful = {key: value for key, value in row.items() if key not in (None, "")}
            if not any((value or "").strip() for value in meaningful.values()):
                continue
            target = _nullable_cell(row.get("Target")) or _nullable_cell(row.get("Name"))
            fluorochrome = _nullable_cell(row.get("Fluorescein"))
            if target is None and fluorochrome is None:
                report.warnings.append(f"Skipped row without target or fluorochrome in {path}")
                continue
            clone_name = _nullable_cell(row.get("Clone"))
            catalog_number = (row.get("Catalog Number") or "").strip() or None
            brand = (row.get("Brand") or "").strip() or None
            extra = {key: value for key, value in meaningful.items() if key not in known}
            existing = conn.execute(
                "SELECT id FROM antibodies WHERE library=? AND catalog_number IS ? AND clone_name IS ? "
                "AND COALESCE(target,'')=COALESCE(?,'') AND COALESCE(fluorochrome,'')=COALESCE(?,'')",
                (library, catalog_number, clone_name, target, fluorochrome),
            ).fetchone()
            values = (
                library,
                target,
                fluorochrome,
                clone_name,
                brand,
                catalog_number,
                json.dumps(extra, ensure_ascii=False),
                str(path),
                _utc_now(),
            )
            if existing:
                conn.execute(
                    "UPDATE antibodies SET library=?,target=?,fluorochrome=?,clone_name=?,brand=?,catalog_number=?,"
                    "extra=?,source_file=?,imported_at=? WHERE id=?",
                    (*values, existing["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO antibodies(library,target,fluorochrome,clone_name,brand,catalog_number,extra,"
                    "source_file,imported_at) VALUES(?,?,?,?,?,?,?,?,?)",
                    values,
                )
            report.antibodies += 1
    return report
