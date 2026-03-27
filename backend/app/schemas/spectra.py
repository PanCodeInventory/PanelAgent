from pydantic import BaseModel, Field


class SpectraRenderRequest(BaseModel):
    fluorochromes: list[str] = Field(
        default_factory=list,
        description="List of fluorochrome names to render emission spectra for.",
    )


class SpectraSeries(BaseModel):
    fluorochrome: str
    peak: int
    sigma: float
    color: str
    category: str | None = None
    x: list[float] = Field(description="Wavelength values (nm).")
    y: list[float] = Field(description="Normalized intensity values (0–100).")


class SpectraRenderResponse(BaseModel):
    status: str
    series: list[SpectraSeries] = Field(default_factory=list)
    warnings: list[str] = Field(
        default_factory=list,
        description="Fluorochrome names that were not found in spectral_data.json.",
    )
    message: str | None = None
