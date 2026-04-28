from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "docs" / "route-ownership-matrix.md"


def _extract_table(section_heading: str) -> tuple[list[str], list[dict[str, str]]]:
    lines = MATRIX_PATH.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index(section_heading)
    except ValueError as exc:
        raise AssertionError(f"Missing section heading: {section_heading}") from exc

    table_lines: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if line.startswith("|"):
            table_lines.append(line)

    assert len(table_lines) >= 3, f"Section {section_heading} must contain a markdown table"

    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        assert len(cells) == len(headers), f"Malformed row in {section_heading}: {line}"
        rows.append(dict(zip(headers, cells, strict=True)))

    return headers, rows


def test_route_ownership_matrix_exists_and_parses_correctly() -> None:
    assert MATRIX_PATH.exists(), "route ownership matrix file must exist"

    browser_headers, browser_rows = _extract_table("## Browser Page Ownership")
    api_headers, api_rows = _extract_table("## API Endpoint Ownership")
    redirect_headers, redirect_rows = _extract_table("## Legacy Browser Redirect Table")

    assert browser_headers == ["Browser Path", "Owner", "Notes"]
    assert api_headers == ["API Path", "Method", "Owner", "Migration Notes"]
    assert redirect_headers == [
        "Old Browser Path",
        "New Browser Path",
        "Redirect Type",
        "Stable Strategy",
    ]

    assert browser_rows, "browser ownership table cannot be empty"
    assert api_rows, "api ownership table cannot be empty"
    assert redirect_rows, "redirect table cannot be empty"


def test_browser_paths_have_unique_ownership_entries() -> None:
    _, browser_rows = _extract_table("## Browser Page Ownership")
    paths = [row["Browser Path"] for row in browser_rows]
    assert len(paths) == len(set(paths)), "browser path ownership entries must be unique"


def test_api_paths_do_not_appear_in_browser_redirect_table() -> None:
    _, redirect_rows = _extract_table("## Legacy Browser Redirect Table")
    redirect_paths = [row["Old Browser Path"] for row in redirect_rows]
    assert all(not path.startswith("`/api/") for path in redirect_paths), (
        "browser redirect table must not contain API endpoints"
    )
