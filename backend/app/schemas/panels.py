from pydantic import BaseModel, Field, RootModel


class PanelGenerateRequest(BaseModel):
    markers: list[str] = Field(min_length=1)
    species: str | None = None
    max_solutions: int = Field(default=10, ge=1, le=100)
    inventory_file: str | None = None


class AntibodyInfo(BaseModel):
    system_code: str
    fluorochrome: str
    brightness: int
    clone: str | None = None
    brand: str | None = None
    catalog_number: str | None = None
    target: str | None = None


class PanelCandidate(RootModel[dict[str, AntibodyInfo]]):
    pass


class PanelGenerateResponse(BaseModel):
    status: str
    candidates: list[PanelCandidate] = Field(default_factory=list)
    missing_markers: list[str] = Field(default_factory=list)
    message: str | None = None


class DiagnoseRequest(BaseModel):
    markers: list[str] = Field(min_length=1)
    inventory_file: str | None = None


class DiagnoseResponse(BaseModel):
    status: str
    diagnosis: str
