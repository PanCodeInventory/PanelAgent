from typing import Any, Optional

from pydantic import BaseModel


class PanelHistorySummary(BaseModel):
    id: str
    created_at: str
    species: str
    inventory_file: Optional[str] = None
    requested_markers: list[str]
    missing_markers: list[str]
    model_name: str


class PanelHistoryDetail(BaseModel):
    id: str
    created_at: str
    species: str
    inventory_file: Optional[str] = None
    requested_markers: list[str]
    missing_markers: list[str]
    selected_panel: list[dict[str, Any]]
    rationale: str
    model_name: str
    api_base: str


class PanelHistoryListResponse(BaseModel):
    items: list[PanelHistorySummary]
    total: int


class PanelHistoryDetailResponse(BaseModel):
    item: PanelHistoryDetail
