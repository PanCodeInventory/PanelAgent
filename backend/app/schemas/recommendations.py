from pydantic import BaseModel, Field


class MarkerDetail(BaseModel):
    marker: str
    type: str
    reason: str


class MarkerRecommendationRequest(BaseModel):
    experimental_goal: str = Field(min_length=1)
    num_colors: int = Field(default=10, ge=1, le=30)
    species: str | None = None
    inventory_file: str | None = None


class MarkerRecommendationResponse(BaseModel):
    status: str
    selected_markers: list[str] = Field(default_factory=list)
    markers_detail: list[MarkerDetail] = Field(default_factory=list)
    message: str | None = None
