import json
import importlib
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from ....core.config import get_settings, project_root, resolve_static_data_path

logger = logging.getLogger(__name__)

_panels_schemas = importlib.import_module("backend.app.schemas.panels")
DiagnoseRequest = _panels_schemas.DiagnoseRequest
DiagnoseResponse = _panels_schemas.DiagnoseResponse
PanelGenerateResponse = _panels_schemas.PanelGenerateResponse
PanelGenerateRequest = _panels_schemas.PanelGenerateRequest
PanelEvaluateRequest = _panels_schemas.PanelEvaluateRequest
PanelEvaluateResponse = _panels_schemas.PanelEvaluateResponse

router = APIRouter(prefix="/panels")


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
    data_preprocessing, _ = _load_domain_modules()
    mapping_file = resolve_static_data_path("channel_mapping")
    return data_preprocessing.load_antibody_data(str(inventory_path), mapping_file=str(mapping_file))


@router.post("/generate", response_model=PanelGenerateResponse)
async def generate_panels(payload: PanelGenerateRequest) -> PanelGenerateResponse:
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
    _, panel_generator = _load_domain_modules()
    result = panel_generator.generate_candidate_panels(
        user_markers=payload.markers,
        antibody_df=antibody_df,
        max_solutions=payload.max_solutions,
    )

    if result.get("status") != "success":
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to generate panel candidates."),
        )

    raw_candidates: Any = result.get("candidates", [])
    normalized_candidates = []
    for candidate in raw_candidates if isinstance(raw_candidates, list) else []:
        if not isinstance(candidate, dict):
            continue
        normalized_candidate = {}
        for marker, antibody in candidate.items():
            if not isinstance(antibody, dict):
                continue
            normalized_candidate[marker] = {
                "system_code": antibody.get("system_code", "UNKNOWN"),
                "fluorochrome": antibody.get("fluorochrome", "UNKNOWN"),
                "brightness": antibody.get("brightness", 3),
                "clone": antibody.get("clone"),
                "brand": antibody.get("brand"),
                "catalog_number": antibody.get("catalog_number"),
                "target": marker,
                "stock": antibody.get("stock"),
            }
        normalized_candidates.append(normalized_candidate)

    return PanelGenerateResponse(
        status="success",
        candidates=normalized_candidates,
        missing_markers=result.get("missing_markers", []),
        message=None,
    )


@router.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose_panels(payload: DiagnoseRequest) -> DiagnoseResponse:
    inventory_path = _resolve_inventory_path(payload.inventory_file, species=payload.species)
    if inventory_path is None:
        raise HTTPException(
            status_code=400,
            detail="Could not resolve inventory file. Provide inventory_file.",
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

    brightness_file = resolve_static_data_path("brightness_mapping")
    try:
        with open(brightness_file, "r", encoding="utf-8") as f:
            brightness_data = json.load(f)
    except FileNotFoundError:
        brightness_data = {}

    data_preprocessing, panel_generator = _load_domain_modules()
    antibodies_by_marker, _ = data_preprocessing.aggregate_antibodies_by_marker(antibody_df, brightness_data)
    normalized_markers = [data_preprocessing.normalize_marker_name(marker) for marker in payload.markers]
    diagnosis = panel_generator.diagnose_conflicts(normalized_markers, antibodies_by_marker)

    return DiagnoseResponse(status="success", diagnosis=diagnosis)


@router.post("/evaluate", response_model=PanelEvaluateResponse)
async def evaluate_panels(payload: PanelEvaluateRequest) -> PanelEvaluateResponse:
    _, panel_generator = _load_domain_modules()

    try:
        result = panel_generator.evaluate_candidates_with_llm(
            candidates=payload.candidates,
            missing_markers=payload.missing_markers,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"LLM evaluation failed: {exc}",
        )

    if result.get("status") != "success":
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to evaluate panel candidates."),
        )

    selected_panel: Any = result.get("selected_panel", {})
    if not isinstance(selected_panel, dict):
        selected_panel = {}

    gating_detail: Any = result.get("gating_detail", [])
    if not isinstance(gating_detail, list):
        gating_detail = []

    rationale = result.get("rationale", "")
    if not isinstance(rationale, str):
        rationale = str(rationale)

    response = PanelEvaluateResponse(
        status="success",
        selected_panel=selected_panel,
        rationale=rationale,
        gating_detail=gating_detail,
        message=None,
    )

    # Persist to panel history on success
    if selected_panel:
        try:
            _persist_evaluation_history(
                species=payload.species,
                inventory_file=payload.inventory_file,
                requested_markers=payload.markers or [],
                missing_markers=payload.missing_markers,
                selected_panel=selected_panel,
                rationale=rationale,
            )
        except Exception:
            logger.warning("Failed to persist panel history entry", exc_info=True)

    return response


def _persist_evaluation_history(
    species: str | None,
    inventory_file: str | None,
    requested_markers: list[str],
    missing_markers: list[str],
    selected_panel: dict[str, dict[str, Any]],
    rationale: str,
) -> None:
    """Write a PanelHistoryEntry after a successful evaluation."""
    from backend.app.services.panel_history_store import PanelHistoryEntry, PanelHistoryStore
    from backend.app.services.llm_settings_store import LlmSettingsStore

    settings = LlmSettingsStore().get_effective_settings()

    # Convert dict[str, dict] → list[dict] for storage
    panel_list = [{"marker": marker, **info} for marker, info in selected_panel.items()]

    entry = PanelHistoryEntry(
        species=species or "unknown",
        inventory_file=inventory_file,
        requested_markers=requested_markers,
        missing_markers=missing_markers,
        selected_panel=panel_list,
        rationale=rationale,
        model_name=settings.model_name,
        api_base=settings.api_base,
    )
    PanelHistoryStore().create_entry(entry)
