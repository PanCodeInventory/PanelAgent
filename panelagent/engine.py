"""Deterministic, LLM-free panel generation and conflict diagnosis."""

from __future__ import annotations

import re
import sqlite3
from collections import defaultdict

from .models import PanelAssignment, PanelCandidate

BLOCKED_CHANNELS = {"V4_V660"}


def _normalize_marker(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _options(
    conn: sqlite3.Connection, library: str, markers: list[str], include_bad: bool
) -> dict[str, list[PanelAssignment]]:
    rows = conn.execute(
        """SELECT a.id,a.target,a.clone_name,a.fluorochrome,a.quality_flag,a.quality_notes,
                  cm.channel,COALESCE(b.brightness,bc.brightness) brightness
           FROM antibodies a
           JOIN channel_mapping cm ON cm.fluorochrome=a.fluorochrome
           LEFT JOIN fluorochrome_aliases fa ON fa.alias=a.fluorochrome
           LEFT JOIN fluorochrome_brightness b ON b.name=a.fluorochrome
           LEFT JOIN fluorochrome_brightness bc ON bc.name=fa.canonical
           WHERE a.library=? ORDER BY a.id,cm.instrument_id""",
        (library,),
    ).fetchall()
    wanted = {_normalize_marker(marker): marker for marker in markers}
    result: dict[str, list[PanelAssignment]] = {marker: [] for marker in markers}
    seen: set[tuple[str, int, str]] = set()
    for row in rows:
        if row["target"] is None:
            continue
        marker = wanted.get(_normalize_marker(row["target"]))
        if marker is None or row["channel"] in BLOCKED_CHANNELS:
            continue
        if row["quality_flag"] == "bad" and not include_bad:
            continue
        identity = (marker, row["id"], row["channel"])
        if identity in seen:
            continue
        seen.add(identity)
        result[marker].append(
            PanelAssignment(
                antibody_id=row["id"],
                marker=marker,
                clone=row["clone_name"],
                fluorochrome=row["fluorochrome"],
                channel=row["channel"],
                brightness=row["brightness"],
                quality_flag=row["quality_flag"],
                quality_notes=row["quality_notes"],
            )
        )
    return result


def find_valid_panels(
    markers: list[str], options: dict[str, list[PanelAssignment]], max_solutions: int = 10
) -> list[PanelCandidate]:
    solutions: list[PanelCandidate] = []
    ordered = sorted(markers, key=lambda marker: (len(options.get(marker, [])), marker))

    def backtrack(index: int, current: dict[str, PanelAssignment], used: set[str]) -> None:
        if len(solutions) >= max_solutions:
            return
        if index == len(ordered):
            assignments = current.copy()
            dim = sorted(
                {
                    item.fluorochrome
                    for item in assignments.values()
                    if item.brightness is not None and item.brightness <= 2
                }
            )
            warnings = [
                f"{marker}: {item.quality_notes or 'quality warning'}"
                for marker, item in assignments.items()
                if item.quality_flag == "warn"
            ]
            solutions.append(PanelCandidate(assignments, dim, warnings))
            return
        marker = ordered[index]
        for antibody in options.get(marker, []):
            if antibody.channel in used:
                continue
            current[marker] = antibody
            used.add(antibody.channel)
            backtrack(index + 1, current, used)
            used.remove(antibody.channel)
            del current[marker]

    backtrack(0, {}, set())
    return solutions


def _diagnose_options(markers: list[str], options: dict[str, list[PanelAssignment]]) -> dict:
    marker_channels = {marker: sorted({item.channel for item in options.get(marker, [])}) for marker in markers}
    dead = [marker for marker, channels in marker_channels.items() if not channels]
    if dead:
        return {
            "status": "conflict",
            "dead_markers": dead,
            "conflict_groups": [],
            "message": f"以下 Marker 没有可用的有效抗体 (No valid antibodies): {', '.join(dead)}。请检查库存或拼写。",
        }
    groups: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for marker, channels in marker_channels.items():
        groups[tuple(channels)].append(marker)
    conflicts = []
    for channels, claimants in groups.items():
        if len(claimants) > len(channels):
            conflicts.append(
                {"markers": claimants, "channels": list(channels), "shortage": len(claimants) - len(channels)}
            )
    if conflicts:
        details = []
        for item in conflicts:
            details.append(
                f"❌ **冲突组 (Conflict Group)**:\n   - Markers: **{', '.join(item['markers'])}** "
                f"({len(item['markers'])} 个)\n   - 只能争夺以下 {len(item['channels'])} 个通道: "
                f"**[{', '.join(item['channels'])}]**\n   - 坑位不足，必然冲突。"
            )
        return {"status": "conflict", "dead_markers": [], "conflict_groups": conflicts, "message": "\n\n".join(details)}
    return {
        "status": "ok",
        "dead_markers": [],
        "conflict_groups": [],
        "message": "未发现明显的硬性死锁。",
    }


def diagnose_conflicts(conn: sqlite3.Connection, library: str, markers: list[str], include_bad: bool = False) -> dict:
    return _diagnose_options(markers, _options(conn, library, markers, include_bad))


def generate_candidates(
    conn: sqlite3.Connection, library: str, markers: list[str], max_solutions: int = 10, include_bad: bool = False
) -> dict:
    options = _options(conn, library, markers, include_bad)
    candidates = find_valid_panels(markers, options, max_solutions)
    if not candidates:
        diagnosis = _diagnose_options(markers, options)
        return {
            "status": "error",
            "message": "无法找到无冲突的 Panel 组合。\n\n" + diagnosis["message"],
            "diagnosis": diagnosis,
            "candidates": [],
        }
    return {"status": "success", "candidates": [item.to_dict() for item in candidates], "missing_markers": []}
