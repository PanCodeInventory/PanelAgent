"""Tests for quality_context_formatter — prompt-ready context with budget guardrails.

TDD: these tests are written BEFORE the implementation.
"""

from backend.app.schemas.quality_registry import (
    AntibodyQualityProjection,
    EntityKey,
)
from backend.app.services.quality_context_formatter import (
    MAX_QUALITY_CONTEXT_CHARS,
    QUALITY_CONTEXT_EMPTY,
    QUALITY_CONTEXT_HEADER,
    format_quality_context,
    sanitize_for_markdown,
)


# -- Helpers ---------------------------------------------------------------

def _entity(
    marker: str = "cd3",
    brand: str = "BioLegend",
    clone: str = "UCHT1",
    catalog: str = "CAT-001",
    species: str = "human",
) -> EntityKey:
    return EntityKey(
        species=species,
        normalized_marker=marker,
        clone=clone,
        brand=brand,
        catalog_number=catalog,
    )


def _proj(
    marker: str = "cd3",
    brand: str = "BioLegend",
    clone: str = "UCHT1",
    issue_count: int = 2,
    latest_issues: list[str] | None = None,
    status: str = "flagged",
    catalog: str = "CAT-001",
) -> AntibodyQualityProjection:
    if latest_issues is None:
        latest_issues = ["Staining weak", "Lot variance high"]
    return AntibodyQualityProjection(
        entity_key=_entity(marker=marker, brand=brand, clone=clone, catalog=catalog),
        issue_count=issue_count,
        latest_issues=latest_issues,
        aggregate_status=status,
    )


# -- Tests -----------------------------------------------------------------

def test_empty_projections_returns_empty_context():
    ctx = format_quality_context([])
    assert ctx.entries == []
    assert ctx.total_chars == 0
    assert ctx.truncated is False


def test_single_projection_formats_correctly():
    proj = _proj(
        marker="cd3",
        brand="BioLegend",
        clone="UCHT1",
        issue_count=2,
        latest_issues=["Staining weak", "Lot variance high"],
        status="flagged",
    )
    ctx = format_quality_context([proj])

    # Should have 1 entry
    assert len(ctx.entries) == 1
    entry = ctx.entries[0]
    assert "### cd3 (BioLegend, UCHT1)" in entry
    assert "- Status: flagged" in entry
    assert "- Issues (2 reported):" in entry
    assert "Staining weak" in entry
    assert "Lot variance high" in entry


def test_multiple_projections_sorted_by_issue_count():
    proj_high = _proj(marker="cd4", issue_count=10, latest_issues=["Issue A"])
    proj_low = _proj(marker="cd8", issue_count=1, latest_issues=["Issue B"], catalog="CAT-002")
    proj_mid = _proj(marker="cd3", issue_count=5, latest_issues=["Issue C"], catalog="CAT-003")

    ctx = format_quality_context([proj_low, proj_mid, proj_high])

    # Entries should be sorted: cd4 (10) first, then cd3 (5), then cd8 (1)
    assert "cd4" in ctx.entries[0]
    assert "cd3" in ctx.entries[1]
    assert "cd8" in ctx.entries[2]


def test_sort_tiebreak_by_marker_name():
    proj_a = _proj(marker="cd8", issue_count=3, latest_issues=["X"], catalog="CAT-A")
    proj_b = _proj(marker="cd4", issue_count=3, latest_issues=["Y"], catalog="CAT-B")
    proj_c = _proj(marker="cd3", issue_count=3, latest_issues=["Z"], catalog="CAT-C")

    ctx = format_quality_context([proj_a, proj_b, proj_c])

    # All have same issue_count; alphabetical by marker: cd3, cd4, cd8
    assert "cd3" in ctx.entries[0]
    assert "cd4" in ctx.entries[1]
    assert "cd8" in ctx.entries[2]


def test_dedup_across_projections():
    """Identical issue texts in different antibodies are NOT deduped (per-antibody)."""
    shared_issue = "Same staining problem"
    proj_a = _proj(
        marker="cd3", issue_count=1,
        latest_issues=[shared_issue], catalog="CAT-A",
    )
    proj_b = _proj(
        marker="cd4", issue_count=1,
        latest_issues=[shared_issue], catalog="CAT-B",
    )

    ctx = format_quality_context([proj_a, proj_b])
    # Both entries should contain the shared issue text
    assert len(ctx.entries) == 2
    assert shared_issue in ctx.entries[0]
    assert shared_issue in ctx.entries[1]


def test_header_included_in_context():
    proj = _proj()
    ctx = format_quality_context([proj])

    # The header should appear in the formatted output
    # total_chars measures the full formatted string including header
    assert ctx.total_chars > 0
    # The header string should be part of the final context
    # We'll verify via the full concatenation logic
    full_text = QUALITY_CONTEXT_HEADER + "\n".join(ctx.entries)
    assert "## Antibody Quality Context" in full_text


def test_sanitization_strips_markdown_chars():
    text = "# Heading with **bold** and `code` blocks"
    result = sanitize_for_markdown(text)
    assert "#" not in result
    assert "**" not in result
    assert "`" not in result
    # The readable text should remain
    assert "Heading" in result


def test_sanitization_limits_issue_length():
    long_text = "A" * 500
    result = sanitize_for_markdown(long_text)
    assert len(result) <= 200


def test_within_budget_no_truncation():
    proj = _proj(
        issue_count=1,
        latest_issues=["Minor issue"],
    )
    ctx = format_quality_context([proj])

    # Small content should fit within budget
    assert ctx.total_chars <= MAX_QUALITY_CONTEXT_CHARS
    assert ctx.truncated is False


def test_over_budget_truncates_at_line_boundary():
    # Create many projections to exceed the 2000-char budget
    projs = []
    for i in range(50):
        projs.append(_proj(
            marker=f"marker{i:03d}",
            issue_count=i + 1,
            latest_issues=[f"Issue text {j} for marker {i:03d}" for j in range(5)],
            catalog=f"CAT-{i:04d}",
        ))

    ctx = format_quality_context(projs)

    # Should be truncated
    assert ctx.truncated is True
    # Must not exceed budget (approximately — truncation marker adds some chars)
    # The truncation marker itself should be included
    assert ctx.total_chars <= MAX_QUALITY_CONTEXT_CHARS + 200  # generous buffer for truncation marker


def test_over_budget_includes_truncation_marker():
    projs = []
    for i in range(50):
        projs.append(_proj(
            marker=f"marker{i:03d}",
            issue_count=i + 1,
            latest_issues=[f"Issue text {j} for marker {i:03d}" for j in range(5)],
            catalog=f"CAT-{i:04d}",
        ))

    ctx = format_quality_context(projs)
    assert ctx.truncated is True

    # The full text should contain truncation marker
    full_text = QUALITY_CONTEXT_HEADER + "\n".join(ctx.entries)
    # Truncation marker should be somewhere in the output
    assert "[Quality context truncated due to length limit]" in full_text


def test_truncated_flag_set_correctly():
    # Under budget → False
    proj_small = _proj(issue_count=1, latest_issues=["Minor"])
    ctx = format_quality_context([proj_small])
    assert ctx.truncated is False

    # Over budget → True
    projs = []
    for i in range(50):
        projs.append(_proj(
            marker=f"marker{i:03d}",
            issue_count=i + 1,
            latest_issues=[f"Issue text {j}" for j in range(5)],
            catalog=f"CAT-{i:04d}",
        ))
    ctx = format_quality_context(projs)
    assert ctx.truncated is True


def test_total_chars_reflects_actual_length():
    proj = _proj(issue_count=1, latest_issues=["Test issue"])
    ctx = format_quality_context([proj])

    # total_chars should match the length of the full formatted string
    full_text = QUALITY_CONTEXT_HEADER + "\n".join(ctx.entries)
    assert ctx.total_chars == len(full_text)


def test_deterministic_output():
    """Same input always produces identical output."""
    projs = [
        _proj(marker="cd8", issue_count=5, latest_issues=["A", "B"], catalog="CAT-1"),
        _proj(marker="cd3", issue_count=2, latest_issues=["C"], catalog="CAT-2"),
        _proj(marker="cd4", issue_count=5, latest_issues=["D", "E"], catalog="CAT-3"),
    ]

    ctx1 = format_quality_context(projs)
    ctx2 = format_quality_context(projs)

    assert ctx1.entries == ctx2.entries
    assert ctx1.total_chars == ctx2.total_chars
    assert ctx1.truncated == ctx2.truncated


def test_entity_key_fields_included():
    proj = _proj(
        marker="cd45",
        brand="BD Biosciences",
        clone="HI30",
        catalog="BD-12345",
    )
    ctx = format_quality_context([proj])

    entry = ctx.entries[0]
    assert "cd45" in entry
    assert "BD Biosciences" in entry
    assert "HI30" in entry
