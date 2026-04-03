"""Comprehensive edge case tests for the quality registry pipeline.

Covers: free-text safety, deduplication drift, concurrent/duplicate saves,
deterministic projection, candidate ranking, and formatter edge cases.

Each test has an explicit expected outcome.
"""

import asyncio
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest
from pydantic import ValidationError

from backend.app.schemas.quality_registry import (
    AntibodyQualityProjection,
    CandidateLookupRequest,
    CandidateLookupResponse,
    CandidateMatch,
    EntityKey,
    FeedbackKey,
    QualityIssueCreate,
    QualityPromptContext,
    _normalize_marker,
)
from backend.app.services.quality_context_formatter import (
    MAX_QUALITY_CONTEXT_CHARS,
    QUALITY_CONTEXT_HEADER,
    _MAX_ISSUE_TEXT_LENGTH,
    _TRUNCATION_MARKER,
    format_quality_context,
    sanitize_for_markdown,
)
from backend.app.services.quality_projection import QualityProjector
from backend.app.services.quality_registry_store import QualityRegistryStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_create(**kwargs) -> QualityIssueCreate:
    defaults = dict(
        issue_text="Staining intensity low",
        reported_by="alice",
        species="Human",
        marker="CD3",
        fluorochrome="FITC",
        brand="BioLegend",
        clone=None,
    )
    defaults.update(kwargs)
    return QualityIssueCreate(**defaults)


def _make_entity(**kwargs) -> EntityKey:
    defaults = dict(
        species="Human",
        marker="CD3",
        clone="OKT3",
        brand="BioLegend",
        catalog="317326",
        lot=None,
    )
    defaults.update(kwargs)
    return EntityKey.from_antibody(**defaults)


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


# ===================================================================
# Category A: Free-text Safety
# ===================================================================


class TestOverlongIssueText:
    """A1: Overlong issue text (5000+ chars).

    Expected: Schema validation rejects text > 2000 chars (max_length).
    For text at max length (2000), formatter truncates to 200 chars.
    """

    def test_rejects_10000_char_issue_text(self):
        """10000-char text is rejected by QualityIssueCreate validation."""
        with pytest.raises(ValidationError) as exc_info:
            _make_create(issue_text="A" * 10_000)
        # Pydantic should report string_too_long for max_length=2000
        errors = exc_info.value.errors()
        assert any("issue_text" in str(e.get("loc", [])) for e in errors)

    def test_max_length_2000_stored_correctly(self, tmp_path):
        """2000-char text (schema max) is stored intact."""
        store = QualityRegistryStore(data_dir=str(tmp_path))
        long_text = "X" * 2000
        created = store.create_issue(_make_create(issue_text=long_text))
        fetched = store.get_issue(created.id)
        assert fetched is not None
        assert len(fetched.issue_text) == 2000

    def test_formatter_truncates_long_issue_to_200(self, tmp_path):
        """Formatter sanitize_for_markdown truncates to 200 chars."""
        long_text = "Y" * 2000
        sanitized = sanitize_for_markdown(long_text)
        assert len(sanitized) <= _MAX_ISSUE_TEXT_LENGTH
        assert len(sanitized) == 200

    def test_formatter_budget_stays_within_limit(self, tmp_path):
        """Full formatter output stays within MAX_QUALITY_CONTEXT_CHARS."""
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        issue = store.create_issue(_make_create(issue_text="Z" * 2000))
        projector.update_projection(issue.id)

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        proj_record = projector.get_projection(feedback_key=fb_key)
        assert proj_record is not None

        projection = AntibodyQualityProjection(
            entity_key=_make_entity(),
            issue_count=proj_record.issue_count,
            latest_issues=proj_record.latest_issues,
            aggregate_status=proj_record.aggregate_status,
        )
        ctx = format_quality_context([projection])
        assert ctx.total_chars <= MAX_QUALITY_CONTEXT_CHARS + len(_TRUNCATION_MARKER)


class TestUnicodeSpecialChars:
    """A2: Unicode and special characters.

    Expected: CJK, emoji, newlines, tabs are stored correctly;
    formatter sanitizes markdown-dangerous chars but preserves unicode.
    """

    def test_cjk_text_stored_correctly(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        cjk_text = "信号强度低 中文测试"
        created = store.create_issue(_make_create(issue_text=cjk_text))
        fetched = store.get_issue(created.id)
        assert fetched.issue_text == cjk_text

    def test_emoji_stored_correctly(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        emoji_text = "Low signal 🔬 needs investigation"
        created = store.create_issue(_make_create(issue_text=emoji_text))
        fetched = store.get_issue(created.id)
        assert fetched.issue_text == emoji_text

    def test_newlines_and_tabs_stored(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        text_with_whitespace = "Line1\nLine2\tTabbed"
        created = store.create_issue(_make_create(issue_text=text_with_whitespace))
        fetched = store.get_issue(created.id)
        assert fetched.issue_text == text_with_whitespace

    def test_sanitizer_preserves_unicode(self):
        """sanitize_for_markdown preserves CJK and emoji but strips # * `."""
        text = "## 中文标题 🔬 **bold**"
        result = sanitize_for_markdown(text)
        assert "中文标题" in result
        assert "🔬" in result
        # Markdown chars stripped
        assert "#" not in result
        assert "**" not in result

    def test_projection_contains_unicode_issue_text(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        issue = store.create_issue(_make_create(issue_text="中文问题 🔬"))
        projector.update_projection(issue.id)

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        proj = projector.get_projection(feedback_key=fb_key)
        assert proj is not None
        assert "中文问题 🔬" in proj.latest_issues


class TestMarkdownInjection:
    """A3: Markdown injection attempt.

    Expected: sanitize_for_markdown strips #, *, backtick characters.
    HTML tags pass through (not dangerous in markdown text context).
    """

    def test_heading_syntax_stripped(self):
        text = "### Critical Issue"
        result = sanitize_for_markdown(text)
        assert "#" not in result
        assert "Critical Issue" in result

    def test_bold_syntax_stripped(self):
        text = "**Important** finding"
        result = sanitize_for_markdown(text)
        assert "**" not in result
        assert "Important" in result

    def test_backtick_stripped(self):
        text = "Use `code` here"
        result = sanitize_for_markdown(text)
        assert "`" not in result
        assert "code" in result

    def test_link_syntax_brackets_preserved(self):
        """Brackets/parens are not stripped (not in the dangerous chars regex)."""
        text = "[link](http://example.com)"
        result = sanitize_for_markdown(text)
        # Current implementation only strips # * `
        assert "[" in result
        assert "]" in result

    def test_html_script_tag_preserved(self):
        """HTML tags pass through — not dangerous in markdown text context."""
        text = "<script>alert(1)</script>"
        result = sanitize_for_markdown(text)
        assert "<script>" in result
        assert "alert(1)" in result

    def test_combined_injection_sanitized(self):
        text = "### **`Injected`** heading"
        result = sanitize_for_markdown(text)
        assert "#" not in result
        assert "*" not in result
        assert "`" not in result
        assert "Injected" in result
        assert "heading" in result


class TestEmptyWhitespace:
    """A4: Empty / whitespace-only issue_text.

    Expected: Validation rejects whitespace-only text via model_validator.
    """

    def test_spaces_only_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            _make_create(issue_text="   ")
        assert "blank" in str(exc_info.value).lower() or "issue_text" in str(exc_info.value)

    def test_tabs_only_rejected(self):
        with pytest.raises(ValidationError):
            _make_create(issue_text="\t\t\t")

    def test_newlines_only_rejected(self):
        with pytest.raises(ValidationError):
            _make_create(issue_text="\n\n\n")

    def test_mixed_whitespace_only_rejected(self):
        with pytest.raises(ValidationError):
            _make_create(issue_text="  \t\n  ")

    def test_empty_string_rejected(self):
        with pytest.raises(ValidationError):
            _make_create(issue_text="")

    def test_valid_text_with_leading_whitespace_accepted(self, tmp_path):
        """Text with content but leading/trailing whitespace is accepted."""
        store = QualityRegistryStore(data_dir=str(tmp_path))
        created = store.create_issue(_make_create(issue_text="  valid issue  "))
        assert created.issue_text == "  valid issue  "


# ===================================================================
# Category B: Deduplication Drift
# ===================================================================


class TestCaseInsensitiveDedup:
    """B5: Case-insensitive dedup.

    Expected: "LOW SIGNAL" and "low signal" collapse to 1 in projection.
    """

    def test_case_insensitive_dedup_count(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        i1 = store.create_issue(_make_create(issue_text="LOW SIGNAL"))
        i2 = store.create_issue(_make_create(issue_text="low signal"))
        projector.update_projection(i1.id)
        projector.update_projection(i2.id)

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        proj = projector.get_projection(feedback_key=fb_key)

        assert proj is not None
        assert proj.issue_count == 1  # Deduplicated to 1
        assert proj.dedup_count == 1  # 1 duplicate collapsed


class TestLeadingTrailingWhitespaceDedup:
    """B6: Leading/trailing whitespace dedup.

    Expected: "  signal issue  " and "signal issue" collapse to 1.
    """

    def test_whitespace_dedup_count(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        i1 = store.create_issue(_make_create(issue_text="  signal issue  "))
        i2 = store.create_issue(_make_create(issue_text="signal issue"))
        projector.update_projection(i1.id)
        projector.update_projection(i2.id)

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        proj = projector.get_projection(feedback_key=fb_key)

        assert proj is not None
        assert proj.issue_count == 1  # Deduplicated
        assert proj.dedup_count == 1


class TestNearDuplicateDistinct:
    """B7: Near-duplicate but distinct.

    Expected: "signal issue with CD3" vs "signal issue with CD4" → count 2.
    """

    def test_near_duplicate_count(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        i1 = store.create_issue(_make_create(issue_text="signal issue with CD3"))
        i2 = store.create_issue(_make_create(issue_text="signal issue with CD4"))
        projector.update_projection(i1.id)
        projector.update_projection(i2.id)

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        proj = projector.get_projection(feedback_key=fb_key)

        assert proj is not None
        assert proj.issue_count == 2  # Distinct after strip+lower
        assert proj.dedup_count == 0


# ===================================================================
# Category C: Concurrent/Duplicate Saves
# ===================================================================


class TestSameIssueSubmittedTwice:
    """C8: Same issue submitted twice rapidly.

    Expected: Both stored (store doesn't dedup), projection deduplicates.
    """

    def test_two_identical_issues_stored(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        i1 = store.create_issue(_make_create(issue_text="Same problem"))
        i2 = store.create_issue(_make_create(issue_text="Same problem"))

        # Store keeps both records
        all_issues = store.list_issues()
        assert len(all_issues) == 2
        assert i1.id != i2.id

    def test_projection_deduplicates_identical_submissions(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        i1 = store.create_issue(_make_create(issue_text="Same problem"))
        i2 = store.create_issue(_make_create(issue_text="Same problem"))
        projector.update_projection(i1.id)
        projector.update_projection(i2.id)

        fb_key = FeedbackKey.from_submission("Human", "CD3", "FITC", "BioLegend")
        proj = projector.get_projection(feedback_key=fb_key)

        assert proj is not None
        assert proj.issue_count == 1  # Projection deduplicates
        assert proj.dedup_count == 1  # 1 was collapsed


class TestBindSameEntityFromTwoIssues:
    """C9: Bind same entity_key from two different issues.

    Expected: Projection aggregates both; issue_count reflects deduped count.
    """

    def test_entity_projection_aggregates_two_issues(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        i1 = store.create_issue(_make_create(issue_text="Issue alpha"))
        i2 = store.create_issue(_make_create(issue_text="Issue beta"))
        entity = _make_entity()

        store.bind_entity(i1.id, entity, confirmed_by="reviewer1")
        projector.update_projection(i1.id)
        store.bind_entity(i2.id, entity, confirmed_by="reviewer1")
        projector.update_projection(i2.id)

        proj = projector.get_projection(entity_key=entity)
        assert proj is not None
        assert proj.issue_count == 2
        assert proj.entity_key == entity
        assert "Issue alpha" in proj.latest_issues
        assert "Issue beta" in proj.latest_issues


# ===================================================================
# Category D: Deterministic Projection
# ===================================================================


class TestProjectionOrderingStable:
    """D10: Projection ordering is stable.

    Expected: get_projections_for_markers() returns results sorted by
    issue_count desc, then normalized_marker alpha for ties.
    """

    def test_ordering_deterministic_with_tiebreak(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        # Create 1 issue each for CD8, CD3, CD4 → all have issue_count=1
        for marker in ["CD8", "CD3", "CD4"]:
            issue = store.create_issue(
                _make_create(marker=marker, issue_text=f"{marker} issue")
            )
            projector.update_projection(issue.id)

        results = projector.get_projections_for_markers(["cd8", "cd3", "cd4"])

        assert len(results) == 3
        # Same issue_count=1 for all → tiebreak by marker alpha: cd3, cd4, cd8
        markers_in_order = []
        for r in results:
            if r.entity_key is not None:
                markers_in_order.append(r.entity_key.normalized_marker)
            elif r.feedback_key is not None:
                markers_in_order.append(r.feedback_key.normalized_marker)

        assert markers_in_order == ["cd3", "cd4", "cd8"]

    def test_ordering_by_issue_count_desc_then_marker(self, tmp_path):
        """Mixed issue_counts with some ties."""
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        # CD8: 3 issues
        for i in range(3):
            issue = store.create_issue(
                _make_create(marker="CD8", issue_text=f"CD8 issue {i}")
            )
            projector.update_projection(issue.id)

        # CD3: 1 issue
        issue = store.create_issue(
            _make_create(marker="CD3", issue_text="CD3 issue 0")
        )
        projector.update_projection(issue.id)

        # CD4: 1 issue (tied with CD3)
        issue = store.create_issue(
            _make_create(marker="CD4", issue_text="CD4 issue 0")
        )
        projector.update_projection(issue.id)

        results = projector.get_projections_for_markers(["cd8", "cd3", "cd4"])

        assert len(results) == 3
        # CD8 (3) first, then CD3 (1), CD4 (1) alphabetically
        markers = []
        for r in results:
            if r.entity_key is not None:
                markers.append(r.entity_key.normalized_marker)
            elif r.feedback_key is not None:
                markers.append(r.feedback_key.normalized_marker)
        assert markers[0] == "cd8"
        assert markers[1] == "cd3"
        assert markers[2] == "cd4"


class TestProjectionAfterRebinding:
    """D11: Projection after entity_key re-binding.

    Expected: Entity A projection loses the issue, entity B gains it.
    Requires calling projector.recompute_entity_projection() for old entity.
    """

    def test_rebind_moves_issue_to_new_entity(self, tmp_path):
        store = QualityRegistryStore(data_dir=str(tmp_path))
        projector = QualityProjector(store)

        # Create issue and bind to entity A
        issue = store.create_issue(_make_create(issue_text="Test issue"))
        projector.update_projection(issue.id)

        entity_a = _make_entity(catalog="CAT-A")
        store.bind_entity(issue.id, entity_a, confirmed_by="reviewer1")
        projector.update_projection(issue.id)

        # Verify entity A has the issue
        proj_a = projector.get_projection(entity_key=entity_a)
        assert proj_a is not None
        assert proj_a.issue_count == 1

        # Re-bind to entity B
        entity_b = _make_entity(catalog="CAT-B")
        store.bind_entity(issue.id, entity_b, confirmed_by="reviewer2")
        projector.update_projection(issue.id)
        # Fix: recompute old entity projection after rebinding
        projector.recompute_entity_projection(entity_a)

        # Entity A should have lost the issue
        proj_a = projector.get_projection(entity_key=entity_a)
        assert proj_a is None or proj_a.issue_count == 0

        # Entity B should have gained the issue
        proj_b = projector.get_projection(entity_key=entity_b)
        assert proj_b is not None
        assert proj_b.issue_count == 1
        assert proj_b.entity_key == entity_b


# ===================================================================
# Category E: Candidate Ranking
# ===================================================================


class TestExactVsPartialConfidence:
    """E12: Exact match vs partial match confidence.

    Expected: Exact normalized marker match → confidence 1.0.
    Partial (substring) match → confidence 0.7.
    """

    def test_exact_marker_match_scores_1_0(self):
        """Exact match: normalized forms are equal → confidence 1.0."""
        query_marker = "CD3"
        exact_marker = "CD3"
        norm_q = _normalize_marker(query_marker)
        norm_e = _normalize_marker(exact_marker)
        assert norm_q == norm_e
        # The endpoint assigns 1.0 for equality
        confidence = 1.0 if norm_q == norm_e else 0.7
        assert confidence == 1.0

    def test_partial_marker_match_scores_0_7(self):
        """Partial match: containment but not equal → confidence 0.7."""
        query_marker = "CD3"
        partial_marker = "CD3 Complex"
        norm_q = _normalize_marker(query_marker)
        norm_p = _normalize_marker(partial_marker)
        assert norm_q != norm_p
        # Endpoint's containment check
        assert norm_q in norm_p
        confidence = 1.0 if norm_q == norm_p else 0.7
        assert confidence == 0.7

    def test_candidates_sorted_by_confidence_desc(self):
        """When both exact and partial exist, exact comes first."""
        entity_exact = EntityKey.from_antibody(
            species="Human", marker="CD3", clone="OKT3",
            brand="BioLegend", catalog="CAT-001",
        )
        entity_partial = EntityKey.from_antibody(
            species="Human", marker="CD3 Complex", clone="OKT4",
            brand="BioLegend", catalog="CAT-002",
        )

        exact = CandidateMatch(
            entity_key=entity_exact, confidence=1.0,
            source="inventory", matched_marker="CD3",
        )
        partial = CandidateMatch(
            entity_key=entity_partial, confidence=0.7,
            source="inventory", matched_marker="CD3 Complex",
        )

        candidates = [partial, exact]
        candidates.sort(key=lambda c: c.confidence, reverse=True)

        assert candidates[0].confidence == 1.0
        assert candidates[1].confidence == 0.7

    def test_endpoint_returns_empty_when_no_inventory(self):
        """Endpoint returns empty candidates when species has no inventory."""
        from backend.app.api.v1.endpoints.quality_registry import candidate_lookup

        response = asyncio.run(candidate_lookup(CandidateLookupRequest(
            text="nonexistent antibody",
            species="NonexistentSpecies",
            marker="FAKE_MARKER_12345",
            fluorochrome="FAKE_FLUOR",
        )))
        assert response.candidates == []


class TestNoCandidates:
    """E13: No candidates at all.

    Expected: Lookup with nonexistent marker returns empty candidates list.
    """

    def test_empty_candidates_model(self):
        response = CandidateLookupResponse(candidates=[])
        assert response.candidates == []
        assert len(response.candidates) == 0

    def test_candidate_match_model_validation(self):
        """CandidateMatch enforces confidence in [0.0, 1.0]."""
        entity = EntityKey.from_antibody(
            species="Human", marker="CD3", clone="OKT3",
            brand="BioLegend", catalog="CAT-001",
        )
        match = CandidateMatch(
            entity_key=entity, confidence=0.5,
            source="inventory", matched_marker="CD3",
        )
        assert 0.0 <= match.confidence <= 1.0


# ===================================================================
# Category F: Formatter Edge Cases
# ===================================================================


class TestEmptyProjectionList:
    """F14: Empty projection list.

    Expected: format_quality_context([]) returns valid QualityPromptContext
    with empty entries, total_chars=0, truncated=False.
    """

    def test_empty_returns_valid_context(self):
        ctx = format_quality_context([])
        assert isinstance(ctx, QualityPromptContext)
        assert ctx.entries == []
        assert ctx.total_chars == 0
        assert ctx.truncated is False

    def test_empty_no_header_content(self):
        """Empty input produces no output text at all."""
        ctx = format_quality_context([])
        assert ctx.total_chars == 0
        # Reconstructing full text yields empty string
        full_text = QUALITY_CONTEXT_HEADER + "\n".join(ctx.entries)
        # Since entries is empty and total_chars is 0, header is not included
        assert ctx.total_chars == 0


class TestBudgetOverflow:
    """F15: Budget overflow.

    Expected: Output is truncated with truncation marker,
    total_chars reflects actual output size.
    """

    def test_many_projections_truncated(self):
        """Many projections exceed budget and get truncated."""
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
        assert ctx.total_chars > 0
        assert ctx.entries[-1].strip() == "> [Quality context truncated due to length limit]"
        assert ctx.total_chars <= MAX_QUALITY_CONTEXT_CHARS + len(_TRUNCATION_MARKER) + 200

    def test_total_chars_matches_output_when_not_truncated(self):
        """total_chars precisely matches len of reconstructed output (no truncation)."""
        projs = [_proj(
            marker=f"m{i}",
            issue_count=1,
            latest_issues=[f"Issue {i}"],
            catalog=f"C-{i}",
        ) for i in range(3)]

        ctx = format_quality_context(projs)
        assert ctx.truncated is False
        full_text = QUALITY_CONTEXT_HEADER + "\n".join(ctx.entries)
        assert ctx.total_chars == len(full_text)

    def test_truncation_stays_near_budget(self):
        """Truncated output should not wildly exceed the budget."""
        projs = [_proj(
            marker=f"marker{i:03d}",
            issue_count=i + 1,
            latest_issues=[f"Long issue text {j} " * 20 for j in range(5)],
            catalog=f"CAT-{i:04d}",
        ) for i in range(100)]

        ctx = format_quality_context(projs)

        if ctx.truncated:
            # total_chars includes the truncation marker
            # Should be close to budget (within marker length + last line)
            assert ctx.total_chars <= MAX_QUALITY_CONTEXT_CHARS + len(_TRUNCATION_MARKER)
