import json
import importlib
from pathlib import Path

import numpy as np
from fastapi import APIRouter, HTTPException

from ....core.config import get_settings

_spectra_schemas = importlib.import_module("backend.app.schemas.spectra")
SpectraRenderRequest = _spectra_schemas.SpectraRenderRequest
SpectraRenderResponse = _spectra_schemas.SpectraRenderResponse
SpectraSeries = _spectra_schemas.SpectraSeries

router = APIRouter(prefix="/spectra")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _load_spectral_db() -> dict:
    """Load spectral_data.json from project root."""
    settings = get_settings()
    root = _project_root()
    filepath = root / settings.SPECTRAL_DATA_FILE
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _resolve_fluor_data(name: str, db: dict) -> dict | None:
    """Resolve fluorochrome name with same strategy as spectral_viewer.py."""
    # 1. Direct match
    if name in db:
        return db[name]
    # 2. Case-insensitive match
    for k, v in db.items():
        if k.lower() == name.lower():
            return v
    return None


def _compute_gaussian(peak: int, sigma: float, x_range: np.ndarray) -> list[float]:
    """Gaussian curve normalized to peak=100, matching spectral_viewer.py semantics."""
    spectral_viewer = importlib.import_module("spectral_viewer")
    y = spectral_viewer.get_gaussian_curve(peak, sigma, x_range)
    return y.tolist()


@router.post("/render-data", response_model=SpectraRenderResponse)
async def render_spectra(payload: SpectraRenderRequest) -> SpectraRenderResponse:
    db = _load_spectral_db()
    x_range = np.linspace(350, 900, 550)

    series: list[SpectraSeries] = []
    warnings: list[str] = []

    for name in payload.fluorochromes:
        data = _resolve_fluor_data(name, db)
        if data is None:
            warnings.append(f"Unknown fluorochrome: {name}")
            continue

        peak = data.get("peak", 500)
        sigma = data.get("sigma", 20)
        color = data.get("color", "#888888")
        category = data.get("category")

        y = _compute_gaussian(peak, sigma, x_range)

        series.append(
            SpectraSeries(
                fluorochrome=name,
                peak=peak,
                sigma=sigma,
                color=color,
                category=category,
                x=x_range.tolist(),
                y=y,
            )
        )

    if not payload.fluorochromes:
        return SpectraRenderResponse(
            status="success",
            series=[],
            warnings=[],
            message="No fluorochromes requested.",
        )

    if warnings and not series:
        raise HTTPException(
            status_code=400,
            detail="No valid fluorochromes found in request.",
        )

    return SpectraRenderResponse(
        status="success",
        series=series,
        warnings=warnings if warnings else [],
        message=None,
    )
