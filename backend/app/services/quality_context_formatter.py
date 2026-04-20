"""Prompt-ready quality context formatter with budget guardrails.

Transforms antibody-level projections into deterministic, sanitized context
blocks suitable for injection into LLM prompts.  Hard token budget enforced
via character-count truncation at line boundaries.

Design choices:
- Deterministic output: stable sort by (issue_count desc, marker asc)
- Markdown-safe: strips dangerous formatting chars from free text
- Budget-guarded: truncates at last complete line boundary when over budget
"""

from __future__ import annotations

import re

from backend.app.schemas.quality_registry import (
    AntibodyQualityProjection,
    QualityPromptContext,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_QUALITY_CONTEXT_CHARS: int = 2000

QUALITY_CONTEXT_HEADER: str = (
    "## 抗体质量上下文\n\n"
    "以下抗体有已报告的质量问题：\n\n"
)

QUALITY_CONTEXT_EMPTY: str = ""

_TRUNCATION_MARKER: str = "\n\n> [Quality context truncated due to length limit]"

_MAX_ISSUE_TEXT_LENGTH: int = 200


# ---------------------------------------------------------------------------
# Sanitisation
# ---------------------------------------------------------------------------

# Patterns that could break markdown formatting or act as prompt injection
_MARKDOWN_DANGEROUS_RE = re.compile(r"[#*`]")
_INSTRUCTION_LIKE_RE = re.compile(
    r"(?i)(ignore\s+(previous|all|above)\s+(instructions?|prompts?|context))"
    r"|(system\s*:\s*)"
    r"|(you\s+are\s+now)",
)


def sanitize_for_markdown(text: str) -> str:
    """Strip markdown-dangerous characters and enforce length limit.

    - Strip leading / trailing whitespace
    - Remove ``#``, ``*``, backtick characters
    - Remove instruction-like prompt injection patterns
    - Remove control characters (except newline, tab)
    - Collapse internal multiple spaces that may result from removal
    - Limit result to ``_MAX_ISSUE_TEXT_LENGTH`` chars
    """
    text = text.strip()
    text = _MARKDOWN_DANGEROUS_RE.sub("", text)
    text = _INSTRUCTION_LIKE_RE.sub("[filtered]", text)
    # Remove control characters except newline and tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Collapse internal multiple spaces that may result from removal
    text = re.sub(r"  +", " ", text)
    if len(text) > _MAX_ISSUE_TEXT_LENGTH:
        text = text[:_MAX_ISSUE_TEXT_LENGTH]
    return text


# ---------------------------------------------------------------------------
# Entry formatting
# ---------------------------------------------------------------------------

def _format_entry(proj: AntibodyQualityProjection) -> str:
    """Build a single formatted entry string for one antibody projection."""
    ek = proj.entity_key
    marker = ek.normalized_marker
    brand = ek.brand
    clone = ek.clone

    lines: list[str] = [
        f"### {marker} ({brand}, {clone})",
        f"- Status: {proj.aggregate_status}",
        f"- Issues ({proj.issue_count} reported):",
    ]

    for issue_text in proj.latest_issues:
        safe = sanitize_for_markdown(issue_text)
        lines.append(f"  - {safe}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def format_quality_context(
    projections: list[AntibodyQualityProjection],
    max_chars: int = MAX_QUALITY_CONTEXT_CHARS,
) -> QualityPromptContext:
    """Transform projections into a prompt-ready quality context block.

    Returns a ``QualityPromptContext`` with:
    - ``entries``: list of individual formatted entry strings
    - ``total_chars``: character length of the full concatenated output
    - ``truncated``: whether the output was cut to fit the budget
    """
    if not projections:
        return QualityPromptContext(entries=[], total_chars=0, truncated=False)

    # Deterministic sort key function applied to projections, but we need
    # the sort to be on the *projections*, then map to formatted entries.
    # Re-sort projections and rebuild entries in sorted order.
    sorted_projections = sorted(
        projections,
        key=lambda p: (-p.issue_count, p.entity_key.normalized_marker),
    )
    sorted_entries: list[str] = [_format_entry(p) for p in sorted_projections]

    # Concatenate: header + entries
    full_text = QUALITY_CONTEXT_HEADER + "\n".join(sorted_entries)

    # Budget enforcement
    truncated = False
    if len(full_text) > max_chars:
        # Truncate at last complete line boundary within budget
        # Reserve space for truncation marker
        budget = max_chars - len(_TRUNCATION_MARKER)
        if budget < len(QUALITY_CONTEXT_HEADER):
            budget = len(QUALITY_CONTEXT_HEADER)

        truncated_text = full_text[:budget]
        # Find last newline to break cleanly
        last_nl = truncated_text.rfind("\n")
        if last_nl > len(QUALITY_CONTEXT_HEADER):
            truncated_text = truncated_text[:last_nl]

        full_text = truncated_text + _TRUNCATION_MARKER
        truncated = True

        # Rebuild entries list: only entries fully included before truncation
        included_body = truncated_text[len(QUALITY_CONTEXT_HEADER):]
        sorted_entries = [e for e in sorted_entries if e in included_body]

        # Append truncation marker as a final entry so callers can reconstruct
        # the full output from entries alone: HEADER + join(entries).
        sorted_entries.append(_TRUNCATION_MARKER.strip())

    return QualityPromptContext(
        entries=sorted_entries,
        total_chars=len(full_text),
        truncated=truncated,
    )
