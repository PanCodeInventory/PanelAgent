import json
import random
from pathlib import Path

import pytest

from data_preprocessing import aggregate_antibodies_by_marker, load_antibody_data


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def fixtures_dir(project_root: Path) -> Path:
    return project_root / "tests" / "fixtures"


@pytest.fixture(scope="session")
def channel_map(project_root: Path) -> dict:
    with open(project_root / "channel_mapping.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def brightness_data(project_root: Path) -> dict:
    with open(project_root / "fluorochrome_brightness.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def small_inventory_csv_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "small_inventory.csv"


@pytest.fixture(scope="session")
def panel_inventory_csv_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "panel_inventory.csv"


@pytest.fixture(scope="session")
def alias_inventory_csv_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "alias_inventory.csv"


@pytest.fixture(scope="session")
def antibody_df(project_root: Path, panel_inventory_csv_path: Path):
    return load_antibody_data(
        str(panel_inventory_csv_path),
        mapping_file=str(project_root / "channel_mapping.json"),
    )


@pytest.fixture(scope="session")
def alias_antibody_df(project_root: Path, alias_inventory_csv_path: Path):
    return load_antibody_data(
        str(alias_inventory_csv_path),
        mapping_file=str(project_root / "channel_mapping.json"),
    )


@pytest.fixture(scope="session")
def antibodies_by_marker(antibody_df, brightness_data: dict):
    by_marker, _ = aggregate_antibodies_by_marker(antibody_df, brightness_data)
    return by_marker


@pytest.fixture(scope="session")
def impossible_case(fixtures_dir: Path) -> dict:
    with open(fixtures_dir / "impossible_markers.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def deterministic_random_seed():
    random.seed(42)
