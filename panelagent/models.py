"""Core value objects for PanelAgent."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Fluorochrome:
    name: str
    canonical_name: str | None = None
    peak_nm: float | None = None
    sigma: float | None = None
    color: str | None = None
    category: str | None = None
    brightness: int | None = None
    channel: str | None = None
    laser: str | None = None


@dataclass(slots=True)
class ChannelInfo:
    channel: str
    laser: str | None
    vendor: str
    model: str


@dataclass(slots=True)
class Antibody:
    id: int
    library: str
    target: str
    fluorochrome: str
    clone_name: str | None
    brand: str | None
    catalog_number: str | None
    channel: str | None = None
    brightness: int | None = None
    quality_flag: str | None = None
    quality_notes: str | None = None


@dataclass(slots=True)
class ImportReport:
    spectra: int = 0
    brightness: int = 0
    aliases: int = 0
    instruments: int = 0
    channels: int = 0
    channel_mappings: int = 0
    antibodies: int = 0
    warnings: list[str] = field(default_factory=list)

    def merge(self, other: ImportReport) -> None:
        for name in (
            "spectra",
            "brightness",
            "aliases",
            "instruments",
            "channels",
            "channel_mappings",
            "antibodies",
        ):
            setattr(self, name, getattr(self, name) + getattr(other, name))
        self.warnings.extend(other.warnings)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PanelAssignment:
    antibody_id: int
    marker: str
    clone: str | None
    fluorochrome: str
    channel: str
    brightness: int | None
    quality_flag: str | None = None
    quality_notes: str | None = None


@dataclass(slots=True)
class PanelCandidate:
    assignments: dict[str, PanelAssignment]
    dim_fluorochromes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "markers": {key: asdict(value) for key, value in self.assignments.items()},
            "brightness_summary": {"dim_fluorochromes": self.dim_fluorochromes},
            "warnings": self.warnings,
        }
