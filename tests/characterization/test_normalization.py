import pytest

from data_preprocessing import normalize_marker_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("CD96 (TACTILE)", "cd96"),
        ("CD 45-2", "cd452"),
        ("cd8a", "cd8"),
    ],
)
def test_normalize_marker_name_oracle_examples(raw, expected):
    assert normalize_marker_name(raw) == expected


def test_normalize_marker_name_non_string_returns_empty_string():
    assert normalize_marker_name(None) == ""
