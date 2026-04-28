import importlib

from fastapi import APIRouter, HTTPException

_history_schemas = importlib.import_module("backend.app.schemas.panel_history")
PanelHistoryListResponse = _history_schemas.PanelHistoryListResponse
PanelHistoryDetailResponse = _history_schemas.PanelHistoryDetailResponse
PanelHistorySummary = _history_schemas.PanelHistorySummary
PanelHistoryDetail = _history_schemas.PanelHistoryDetail

_history_store_mod = importlib.import_module("backend.app.services.panel_history_store")
PanelHistoryStore = _history_store_mod.PanelHistoryStore

router = APIRouter(prefix="/panel-history")


@router.get("", response_model=PanelHistoryListResponse)
async def list_history(limit: int = 50, offset: int = 0):
    store = PanelHistoryStore()
    entries = store.list_entries(limit=limit, offset=offset)
    summaries = [
        PanelHistorySummary(
            id=e.id,
            created_at=e.created_at,
            species=e.species,
            inventory_file=e.inventory_file,
            requested_markers=e.requested_markers,
            missing_markers=e.missing_markers,
            model_name=e.model_name,
        )
        for e in entries
    ]
    return PanelHistoryListResponse(items=summaries, total=len(summaries))


@router.get("/{entry_id}", response_model=PanelHistoryDetailResponse)
async def get_history_detail(entry_id: str):
    store = PanelHistoryStore()
    entry = store.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="History entry not found")
    detail = PanelHistoryDetail(
        id=entry.id,
        created_at=entry.created_at,
        species=entry.species,
        inventory_file=entry.inventory_file,
        requested_markers=entry.requested_markers,
        missing_markers=entry.missing_markers,
        selected_panel=entry.selected_panel,
        rationale=entry.rationale,
        model_name=entry.model_name,
        api_base=entry.api_base,
    )
    return PanelHistoryDetailResponse(item=detail)
