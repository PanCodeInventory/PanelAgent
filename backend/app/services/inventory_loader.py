"""Inventory loading service — single source of truth for CSV loading."""

import importlib
from pathlib import Path

import pandas as pd

from backend.app.core.config import project_root, resolve_static_data_path


def _load_domain_modules():
    data_preprocessing = importlib.import_module("data_preprocessing")
    return data_preprocessing


def load_inventory(inventory_path: Path, include_viability: bool = True):
    """Load antibody inventory, optionally merging viability dyes.

    Args:
        inventory_path: Path to the main species inventory CSV
        include_viability: If True, also load and merge viability_dyes.csv

    Returns:
        pandas DataFrame with antibody data, or None if loading fails
    """
    data_preprocessing = _load_domain_modules()
    mapping_file = resolve_static_data_path("channel_mapping")

    main_df = data_preprocessing.load_antibody_data(
        str(inventory_path), mapping_file=str(mapping_file)
    )

    if main_df is None or main_df.empty:
        return main_df

    if not include_viability:
        return main_df

    viability_path = project_root() / "inventory" / "viability_dyes.csv"
    if not viability_path.exists():
        return main_df

    viability_df = data_preprocessing.load_antibody_data(
        str(viability_path), mapping_file=str(mapping_file)
    )

    if viability_df is None or viability_df.empty:
        return main_df

    combined = pd.concat([main_df, viability_df], ignore_index=True)
    # pandas reads pure-numeric catalog_number as int — coerce to str
    if "catalog_number" in combined.columns:
        combined["catalog_number"] = combined["catalog_number"].astype(str)
    return combined
