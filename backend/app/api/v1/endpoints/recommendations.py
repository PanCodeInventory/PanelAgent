import importlib
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ....core.config import get_settings, project_root, resolve_static_data_path
from ....services.inventory_loader import load_inventory

_recommendations_schemas = importlib.import_module("backend.app.schemas.recommendations")
MarkerRecommendationRequest = _recommendations_schemas.MarkerRecommendationRequest
MarkerRecommendationResponse = _recommendations_schemas.MarkerRecommendationResponse

router = APIRouter(prefix="/recommendations")


def _load_domain_modules():
    data_preprocessing = importlib.import_module("data_preprocessing")
    panel_generator = importlib.import_module("panel_generator")
    return data_preprocessing, panel_generator


def _resolve_inventory_path(inventory_file: str | None, species: str | None) -> Path | None:
    settings = get_settings()
    root = project_root()
    inventory_dir = root / settings.INVENTORY_DIR

    if inventory_file:
        if "/" in inventory_file or "\\" in inventory_file or ".." in inventory_file:
            return None
        return inventory_dir / inventory_file

    if species:
        if "/" in species or "\\" in species or ".." in species:
            return None
        mapping = settings.SPECIES_INVENTORY_MAP
        filename = mapping.get(species)
        if not filename:
            for key, val in mapping.items():
                if key.lower() == species.lower():
                    filename = val
                    break
        if not filename:
            species_english = species.split("(")[0].split("（")[0].strip()
            filename = mapping.get(species_english)
            if not filename:
                for key, val in mapping.items():
                    if key.lower() == species_english.lower():
                        filename = val
                        break
        if filename:
            return inventory_dir / filename
        return inventory_dir / f"{species}.csv"

    if inventory_dir.exists():
        csv_files = sorted(inventory_dir.glob("*.csv"))
        if len(csv_files) == 1:
            return csv_files[0]

    return None


def _load_inventory_df(inventory_path: Path):
    return load_inventory(inventory_path, include_viability=False)


def _extract_available_targets(antibody_df) -> list[str]:
    targets: set[str] = set()
    if "Target" not in antibody_df.columns:
        return []

    for target in antibody_df["Target"].dropna():
        clean_name = re.sub(r"\s*\(.*?\)", "", str(target)).strip()
        if clean_name:
            targets.add(clean_name)
    return sorted(targets)


@router.post("/markers", response_model=MarkerRecommendationResponse)
async def recommend_markers(payload: MarkerRecommendationRequest) -> MarkerRecommendationResponse:
    inventory_path = _resolve_inventory_path(payload.inventory_file, payload.species)
    if inventory_path is None:
        raise HTTPException(
            status_code=400,
            detail="Could not resolve inventory file. Provide inventory_file or a species-mapped CSV.",
        )

    if not inventory_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Inventory file not found: {inventory_path}",
        )

    antibody_df = _load_inventory_df(inventory_path)
    if antibody_df is None or antibody_df.empty:
        raise HTTPException(
            status_code=400,
            detail="Inventory file is empty or invalid.",
        )

    available_targets = _extract_available_targets(antibody_df)
    if not available_targets:
        raise HTTPException(
            status_code=400,
            detail="No available targets found in inventory.",
        )

    _, panel_generator = _load_domain_modules()
    try:
        result = panel_generator.recommend_markers_from_inventory(
            payload.experimental_goal,
            payload.num_colors,
            available_targets,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"LLM recommendation failed: {exc}",
        )

    if result.get("status") != "success":
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to recommend markers."),
        )

    return MarkerRecommendationResponse(
        status="success",
        selected_markers=result.get("selected_markers", []),
        markers_detail=result.get("markers_detail", []),
        message=result.get("message"),
    )
