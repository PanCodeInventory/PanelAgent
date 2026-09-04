"""Argparse command-line interface for PanelAgent."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .db import connect, default_db_path, ensure_schema
from .engine import diagnose_conflicts, generate_candidates
from .importers import import_antibody_csv, import_instrument_config
from .repo import Repo
from .resolve import resolve_fluorochrome
from .seed import seed_database


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pa")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--config-dir")
    init.add_argument("--csv", action="append", default=[], metavar="SPECIES=PATH")
    init.add_argument("--inventory-dir")
    db = sub.add_parser("db")
    db_sub = db.add_subparsers(dest="action", required=True)
    db_sub.add_parser("path")
    db_sub.add_parser("stats")
    dye = sub.add_parser("dye")
    dye_sub = dye.add_subparsers(dest="action", required=True)
    dye_list = dye_sub.add_parser("list")
    dye_list.add_argument("--laser")
    dye_show = dye_sub.add_parser("show")
    dye_show.add_argument("name")
    alias = dye_sub.add_parser("alias-add")
    alias.add_argument("alias")
    alias.add_argument("canonical")
    channel = sub.add_parser("channel")
    channel_list = channel.add_subparsers(dest="action", required=True).add_parser("list")
    channel_list.add_argument("--laser")
    antibody = sub.add_parser("antibody")
    antibody_sub = antibody.add_subparsers(dest="action", required=True)
    antibody_list = antibody_sub.add_parser("list")
    antibody_list.add_argument("--library")
    antibody_list.add_argument("--target")
    antibody_list.add_argument("--flag")
    antibody_search = antibody_sub.add_parser("search")
    antibody_search.add_argument("keyword")
    annotate = antibody_sub.add_parser("annotate")
    annotate.add_argument("id", type=int)
    annotate.add_argument("--library")
    annotate.add_argument("--flag", required=True)
    annotate.add_argument("--note")
    panel = sub.add_parser("panel")
    panel_sub = panel.add_subparsers(dest="action", required=True)
    for name in ("generate", "diagnose"):
        command = panel_sub.add_parser(name)
        command.add_argument("--library", required=True)
        command.add_argument("--markers", required=True)
        command.add_argument("--include-bad", action="store_true")
        if name == "generate":
            command.add_argument("--max", type=int, default=10)
    sub.add_parser("mcp")
    return parser


def _extract_global(argv: list[str]) -> tuple[list[str], bool, str | None]:
    args = list(argv)
    json_output = False
    db_path = None
    while "--json" in args:
        args.remove("--json")
        json_output = True
    if "--db" in args:
        index = args.index("--db")
        try:
            db_path = args[index + 1]
        except IndexError as exc:
            raise SystemExit("--db requires a path") from exc
        del args[index : index + 2]
    return args, json_output, db_path


def _print(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2, default=str))
        return
    if isinstance(value, list):
        for item in value:
            print(" | ".join(f"{key}={val}" for key, val in item.items() if val is not None))
    elif isinstance(value, dict):
        for key, val in value.items():
            print(f"{key}: {val}")
    else:
        print(value)


def _print_panel_generate(result: dict[str, Any]) -> None:
    if result.get("status") != "success":
        print("Panel 生成失败")
        print("=" * 16)
        diagnosis = result.get("diagnosis")
        if diagnosis:
            print("\n诊断结果")
            print("-" * 16)
            print(diagnosis["message"])
        else:
            print(result.get("message", "未找到候选 Panel。"))
        return

    columns = ("marker", "clone", "fluorochrome", "channel", "brightness", "quality")
    for index, candidate in enumerate(result["candidates"], start=1):
        print(f"候选 Panel {index}")
        print("=" * 16)
        rows = []
        for marker, assignment in candidate["markers"].items():
            quality = assignment.get("quality_flag") or "-"
            if assignment.get("quality_notes"):
                quality += f": {assignment['quality_notes']}"
            rows.append(
                {
                    "marker": marker,
                    "clone": assignment.get("clone") or "-",
                    "fluorochrome": assignment["fluorochrome"],
                    "channel": assignment["channel"],
                    "brightness": assignment.get("brightness") or "-",
                    "quality": quality,
                }
            )
        widths = {column: max(len(column), *(len(str(row[column])) for row in rows)) for column in columns}
        print(" | ".join(column.ljust(widths[column]) for column in columns))
        print("-+-".join("-" * widths[column] for column in columns))
        for row in rows:
            print(" | ".join(str(row[column]).ljust(widths[column]) for column in columns))
        dim = candidate["brightness_summary"]["dim_fluorochromes"]
        print(f"亮度摘要: ≤2 级暗染料: {', '.join(dim) if dim else '无'}")
        warnings = candidate.get("warnings") or []
        print(f"质量警告: {'; '.join(warnings) if warnings else '无'}")
        if index < len(result["candidates"]):
            print()


def _print_panel_diagnosis(result: dict[str, Any]) -> None:
    print("Panel 诊断结果")
    print("=" * 16)
    if result.get("dead_markers"):
        print(f"\n无可用抗体的 Marker: {', '.join(result['dead_markers'])}")
    if result.get("conflict_groups"):
        print("\n通道冲突")
        print("-" * 16)
    print(result["message"])


def _init(conn, args: argparse.Namespace) -> dict:
    report = seed_database(conn)
    if args.config_dir:
        report.merge(import_instrument_config(conn, args.config_dir))
    for spec in args.csv:
        if "=" not in spec:
            raise ValueError("--csv must use Library=path.csv")
        library, path = spec.split("=", 1)
        report.merge(import_antibody_csv(conn, path, library))
    if args.inventory_dir:
        for path in sorted(Path(args.inventory_dir).glob("*.csv")):
            if "isotype" in path.name.lower():
                library = "Isotype"
            elif "小鼠" in path.name:
                library = "Mouse"
            elif "人" in path.name:
                library = "Human"
            else:
                report.warnings.append(f"Skipped {path.name}: library not identifiable")
                continue
            report.merge(import_antibody_csv(conn, path, library))
    return report.to_dict()


def main(argv: list[str] | None = None) -> int:
    args_list, json_output, db_override = _extract_global(list(argv) if argv is not None else sys.argv[1:])
    args = _parser().parse_args(args_list)
    if args.command == "mcp":
        from .mcp import run

        run(db_override)
        return 0
    path = Path(db_override).expanduser() if db_override else default_db_path()
    if args.command == "db" and args.action == "path":
        _print({"path": str(path)}, json_output)
        return 0
    conn = connect(path)
    ensure_schema(conn)
    repo = Repo(conn)
    try:
        if args.command == "init":
            result = _init(conn, args)
        elif args.command == "db":
            result = repo.stats()
        elif args.command == "dye" and args.action == "list":
            result = repo.list_dyes(args.laser)
        elif args.command == "dye" and args.action == "show":
            dye = resolve_fluorochrome(conn, args.name)
            result = asdict(dye) if dye else None
        elif args.command == "dye" and args.action == "alias-add":
            with conn:
                conn.execute(
                    "INSERT INTO fluorochrome_aliases VALUES(?,?) ON CONFLICT(alias) DO UPDATE SET canonical=excluded.canonical",
                    (args.alias, args.canonical),
                )
            result = {"alias": args.alias, "canonical": args.canonical}
        elif args.command == "channel":
            result = repo.list_channels(args.laser)
        elif args.command == "antibody" and args.action == "list":
            result = repo.antibodies(args.library, args.target, args.flag)
        elif args.command == "antibody" and args.action == "search":
            result = repo.antibodies(keyword=args.keyword)
        elif args.command == "antibody":
            result = repo.annotate(args.id, args.flag, args.note, args.library)
            if result is None:
                raise ValueError(f"Antibody {args.id} not found")
        else:
            markers = [item.strip() for item in args.markers.split(",") if item.strip()]
            if args.action == "generate":
                result = generate_candidates(conn, args.library, markers, args.max, args.include_bad)
            else:
                result = diagnose_conflicts(conn, args.library, markers, args.include_bad)
        if args.command == "panel" and not json_output:
            if args.action == "generate":
                _print_panel_generate(result)
            else:
                _print_panel_diagnosis(result)
        else:
            _print(result, json_output)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
