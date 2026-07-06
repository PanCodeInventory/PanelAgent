"""Inventory file endpoints — list available files and accept uploads.

Uploaded antibody inventories (.csv / .xlsx) are stored flat in the
``inventory/`` directory alongside the bundled CSVs, so the existing
``_resolve_inventory_path`` resolution (and its path-traversal guard) in
``panels.py`` / ``recommendations.py`` works unchanged.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from ....core.config import get_settings, project_root

router = APIRouter(prefix="/inventory")

# Allowed inventory extensions and max upload size (10 MB).
_ALLOWED_EXT = {".csv", ".xlsx", ".xls"}
_MAX_BYTES = 10 * 1024 * 1024

# Files shipped with the project that should not be listed as selectable
# inventories (auxiliary data, not antibody tables).
_HIDDEN_FILES = {
    "viability_dyes.csv",
    "Flourence_List.csv",
    "Isotype.csv",
    "Others.csv",
    "impossible_inventory.csv",
}


class InventoryFile(BaseModel):
    filename: str
    uploaded: bool


class InventoryUploadResponse(BaseModel):
    filename: str
    rows: int
    species_hint: str | None


def _inventory_dir() -> Path:
    """Resolve the inventory directory.

    Bundled CSVs live under the project root / PyInstaller bundle. When
    ``PANELAGENT_DATA_DIR`` is set (single-exe mode, where the bundle is
    read-only), uploaded files are written to an ``inventory/`` subfolder
    under that user-writable directory instead, and is also where we look
    first so uploads persist across runs.
    """
    settings = get_settings()
    data_dir = os.environ.get("PANELAGENT_DATA_DIR", "").strip()
    if data_dir:
        return Path(data_dir) / settings.INVENTORY_DIR
    return project_root() / settings.INVENTORY_DIR


def _sanitize(name: str) -> str:
    """Strip path separators and unsafe characters, keep extension."""
    # Take only the basename in case the client sent a path.
    name = Path(name).name
    # Replace any character that is not word/dot/dash/underscore/Chinese.
    name = re.sub(r"[^\w.\-\u4e00-\u9fff]", "_", name)
    return name


@router.get("/files", response_model=list[InventoryFile])
async def list_inventory_files() -> list[InventoryFile]:
    """List antibody inventory files available for panel generation.

    Bundled CSVs in ``inventory/`` plus any previously uploaded files are
    returned. Auxiliary data files (viability dyes, isotype controls) are
    hidden from this list.
    """
    inv_dir = _inventory_dir()
    if not inv_dir.exists():
        return []

    files: list[InventoryFile] = []
    for entry in sorted(inv_dir.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_file():
            continue
        if entry.name.startswith("."):
            continue
        if entry.suffix.lower() not in _ALLOWED_EXT:
            continue
        if entry.name in _HIDDEN_FILES:
            continue
        files.append(InventoryFile(filename=entry.name, uploaded=False))
    return files


@router.post("/upload", response_model=InventoryUploadResponse)
async def upload_inventory(file: UploadFile) -> InventoryUploadResponse:
    """Accept an uploaded ``.csv`` / ``.xlsx`` antibody inventory.

    The file is stored flat in ``inventory/`` (timestamp-prefixed to avoid
    clobbering bundled data) and immediately usable via the ``inventory_file``
    field on ``/panels/generate`` etc.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in _ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {sorted(_ALLOWED_EXT)}",
        )

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(raw) > _MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(raw)} bytes). Max {_MAX_BYTES} bytes.",
        )

    inv_dir = _inventory_dir()
    inv_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _sanitize(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stored_name = f"{timestamp}_{safe_name}"
    stored_path = inv_dir / stored_name
    stored_path.write_bytes(raw)

    # Best-effort row count + species hint for the UI.
    rows, species_hint = _inspect(stored_path)

    return InventoryUploadResponse(filename=stored_name, rows=rows, species_hint=species_hint)


def _inspect(path: Path) -> tuple[int, str | None]:
    """Return (row_count_excluding_header, species_hint) or (0, None)."""
    try:
        import importlib

        data_preprocessing = importlib.import_module("data_preprocessing")
        df = data_preprocessing.load_antibody_data(str(path))
        if df is None or df.empty:
            return 0, None
        species_hint = None
        if "Species" in df.columns:
            unique = df["Species"].dropna().astype(str).str.strip()
            unique = unique[unique != ""]
            if unique.nunique() == 1:
                species_hint = str(unique.iloc[0])
        return len(df), species_hint
    except Exception:
        return 0, None


@router.delete("/files/{filename}")
async def delete_inventory_file(filename: str) -> dict[str, bool]:
    """Delete an uploaded inventory file by name.

    Refuses path separators and only deletes files within ``inventory/``.
    """
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    target = _inventory_dir() / filename
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    # Guard against deleting bundled inventories.
    try:
        target.resolve().relative_to(_inventory_dir().resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path.") from None

    target.unlink()
    return {"ok": True}
