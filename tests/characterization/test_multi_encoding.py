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
