import pytest

from backend.app.core.config import resolve_static_data_path
from data_preprocessing import load_antibody_data


@pytest.mark.parametrize("encoding", ["utf-8", "gbk", "gb18030", "latin1"])
def test_load_antibody_data_supports_encoding(project_root, encoding, tmp_path):
    csv_path = tmp_path / f"test_{encoding}.csv"
    with open(csv_path, "w", encoding=encoding, newline="") as f:
        f.write("Target,Fluorescein,Clone,Brand,Catalog Number\n")
        f.write("CD3,APC,17A2,BioLegend,100235\n")

    result = load_antibody_data(
        str(csv_path),
        mapping_file=str(resolve_static_data_path("channel_mapping")),
    )

    assert result is not None
    assert not result.empty
    assert "CD3" in result["Target"].values


@pytest.mark.parametrize(
    ("fluorochrome", "expected_code"),
    [
        ("Brilliant Violet 785™", "V5_V780"),
        ("Brilliant Violet 786™", "V5_V780"),
        ("Alexa Fluor® 594", "Y2_ECD"),
        ("Alexa Fluor 594", "Y2_ECD"),
        ("KIRAVIA Blue 520™", "V2_KO525"),
        ("KIRAVIA Blue 520", "V2_KO525"),
    ],
)
def test_load_antibody_data_maps_cytoflex_s_detector_codes(fluorochrome, expected_code, tmp_path):
    csv_path = tmp_path / "mapping_check.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        f.write("Target,Fluorescein,Clone,Brand,Catalog Number\n")
        f.write(f"CD3,{fluorochrome},17A2,BioLegend,100235\n")

    result = load_antibody_data(
        str(csv_path),
        mapping_file=str(resolve_static_data_path("channel_mapping")),
    )

    assert result is not None
    assert not result.empty
    assert result.iloc[0]["System_Code"] == expected_code
