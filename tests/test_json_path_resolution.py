"""Regression test for CWD dependency in generate_candidate_panels().

This test proves that panel_generator.generate_candidate_panels() fails when CWD
is NOT the project root because it uses bare relative path 'fluorochrome_brightness.json'
at line 272.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from data_preprocessing import load_antibody_data
import panel_generator


MOCK_LLM_RESPONSE = {
    "status": "success",
    "candidates": [
        {
            "CD3": {"fluorochrome": "PE", "system_code": "B", "brightness": 5},
            "CD4": {"fluorochrome": "APC", "system_code": "C", "brightness": 4},
        }
    ],
    "rationale": "Test rationale",
    "gating_detail": [],
}


@pytest.fixture
def mock_consult_gpt_oss():
    return MagicMock(return_value=MOCK_LLM_RESPONSE)


@pytest.fixture
def brightness_data(project_root: Path):
    with open(project_root / "fluorochrome_brightness.json", "r") as f:
        return json.load(f)


def test_generate_candidate_panels_is_cwd_independent(
    tmp_path,
    monkeypatch,
    project_root: Path,
    panel_inventory_csv_path: Path,
    mock_consult_gpt_oss,
    brightness_data: dict,
):
    antibody_df = load_antibody_data(
        str(panel_inventory_csv_path),
        mapping_file=str(project_root / "channel_mapping.json"),
    )

    assert antibody_df is not None and not antibody_df.empty, "Antibody data should load"
    assert brightness_data, "Brightness data should be loaded from project root"

    # Verify brightness file cannot be found from temp CWD
    monkeypatch.chdir(tmp_path)

    assert not Path.cwd().samefile(project_root), "CWD should be temp dir"
    assert not Path("fluorochrome_brightness.json").exists(), (
        "fluorochrome_brightness.json should NOT exist in temp CWD"
    )

    # Track what brightness data is used
    with patch.object(panel_generator, "consult_gpt_oss", mock_consult_gpt_oss), \
         patch("llm_api_client.consult_gpt_oss", mock_consult_gpt_oss), \
         patch("panel_generator.aggregate_antibodies_by_marker") as mock_aggregate:

        def aggregate_side_effect(df, brightness):
            mock_aggregate.brightness_received = brightness
            return {}, {}

        mock_aggregate.side_effect = aggregate_side_effect

        result = panel_generator.generate_candidate_panels(
            user_markers=["CD3", "CD4"],
            antibody_df=antibody_df,
            max_solutions=1,
        )

        # When bug exists (CWD is wrong):
        # - open('fluorochrome_brightness.json') raises FileNotFoundError
        # - Code catches it and sets brightness_data = {}
        # - mock_aggregate receives empty brightness_data
        #
        # When bug is fixed (CWD-independent):
        # - Brightness file is loaded using project-relative or absolute path
        # - mock_aggregate receives the actual brightness_data from project root
        #
        # THIS ASSERTION SHOULD FAIL when bug exists (RED state)
        # because brightness_data will be empty dict {}
        assert mock_aggregate.brightness_received, (
            "Brightness data should be loaded even from non-root CWD. "
            "FAILURE proves the bug: panel_generator.py line 272 uses "
            "open('fluorochrome_brightness.json', 'r') which is CWD-dependent. "
            f"Got brightness: {mock_aggregate.brightness_received}"
        )
        assert mock_aggregate.brightness_received == brightness_data, (
            f"Brightness data should match project root data. "
            f"Expected {brightness_data}, got {mock_aggregate.brightness_received}"
        )


def test_generate_candidate_panels_missing_brightness_fallback_contract(
    monkeypatch,
    project_root: Path,
    panel_inventory_csv_path: Path,
    mock_consult_gpt_oss,
):
    """Verify that when brightness JSON is missing, function falls back to {} gracefully."""
    antibody_df = load_antibody_data(
        str(panel_inventory_csv_path),
        mapping_file=str(project_root / "channel_mapping.json"),
    )

    assert antibody_df is not None and not antibody_df.empty, "Antibody data should load"

    # Monkeypatch resolve_static_data_path to return a non-existent file path
    non_existent_path = "/tmp/non_existent_brightness_file_12345.json"

    def mock_resolve_static_data_path(name):
        return non_existent_path

    monkeypatch.setattr(panel_generator, "resolve_static_data_path", mock_resolve_static_data_path)

    # Track what brightness data is used
    with patch.object(panel_generator, "consult_gpt_oss", mock_consult_gpt_oss), \
         patch("llm_api_client.consult_gpt_oss", mock_consult_gpt_oss), \
         patch("panel_generator.aggregate_antibodies_by_marker") as mock_aggregate:

        def aggregate_side_effect(df, brightness):
            mock_aggregate.brightness_received = brightness
            return {}, {}

        mock_aggregate.side_effect = aggregate_side_effect

        result = panel_generator.generate_candidate_panels(
            user_markers=["CD3", "CD4"],
            antibody_df=antibody_df,
            max_solutions=1,
        )

        # When brightness file is missing (FileNotFoundError):
        # - Code catches exception and sets brightness_data = {}
        # - mock_aggregate should receive empty dict
        assert mock_aggregate.brightness_received == {}, (
            f"When brightness file is missing, fallback should be empty dict. "
            f"Got: {mock_aggregate.brightness_received}"
        )
        assert isinstance(mock_aggregate.brightness_received, dict), (
            f"Fallback must be dict instance, got {type(mock_aggregate.brightness_received)}"
        )
        assert len(mock_aggregate.brightness_received) == 0, (
            "Fallback dict must be empty"
        )
