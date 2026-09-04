from __future__ import annotations

import json
from pathlib import Path

from panelagent.cli import main

ROOT = Path(__file__).resolve().parents[2]


def _run(capsys, *args):
    assert main(list(args)) == 0
    return json.loads(capsys.readouterr().out)


def test_json_cli_smoke(tmp_path, capsys):
    db = str(tmp_path / "cli.db")
    init = _run(
        capsys,
        "init",
        "--db",
        db,
        "--config-dir",
        str(ROOT / "config"),
        "--csv",
        f"Mouse={ROOT / 'inventory/panel_inventory.csv'}",
        "--json",
    )
    assert init["antibodies"] == 5
    assert _run(capsys, "dye", "show", "PE", "--db", db, "--json")["name"] == "PE"
    assert len(_run(capsys, "antibody", "list", "--library", "Mouse", "--db", db, "--json")) == 5
    panel = _run(
        capsys,
        "panel",
        "generate",
        "--library",
        "Mouse",
        "--markers",
        "CD3,CD4,CD8",
        "--db",
        db,
        "--json",
    )
    assert panel["status"] == "success"


def test_panel_plain_text_rendering(tmp_path, capsys):
    db = str(tmp_path / "plain.db")
    _run(
        capsys,
        "init",
        "--db",
        db,
        "--csv",
        f"Mouse={ROOT / 'inventory/panel_inventory.csv'}",
        "--json",
    )

    assert main(["panel", "generate", "--library", "Mouse", "--markers", "CD3,CD4,CD8", "--db", db]) == 0
    generated = capsys.readouterr().out
    assert "候选 Panel 1" in generated
    assert "marker | clone" in generated
    assert "CD3" in generated
    assert "APC" in generated
    assert "R1_APC" in generated
    assert "亮度摘要: ≤2 级暗染料: 无" in generated
    assert "质量警告: 无" in generated
    assert "{'status':" not in generated

    assert main(["panel", "diagnose", "--library", "Mouse", "--markers", "Unknown", "--db", db]) == 0
    diagnosed = capsys.readouterr().out
    assert "Panel 诊断结果" in diagnosed
    assert "无可用抗体的 Marker: Unknown" in diagnosed
    assert "以下 Marker 没有可用的有效抗体" in diagnosed
    assert "{'status':" not in diagnosed


def test_inventory_dir_recognizes_isotype_and_skips_unknown(tmp_path, capsys):
    inventory_dir = tmp_path / "inventory"
    inventory_dir.mkdir()
    source = (ROOT / "inventory/impossible_inventory.csv").read_text(encoding="utf-8")
    (inventory_dir / "lab-ISOTYPE.csv").write_text(source, encoding="utf-8")
    (inventory_dir / "reagents.csv").write_text(source, encoding="utf-8")
    db = str(tmp_path / "libraries.db")

    result = _run(capsys, "init", "--inventory-dir", str(inventory_dir), "--db", db, "--json")
    assert result["antibodies"] == 3
    assert "Skipped reagents.csv: library not identifiable" in result["warnings"]
    antibodies = _run(capsys, "antibody", "list", "--library", "Isotype", "--db", db, "--json")
    assert len(antibodies) == 3
    assert all(item["library"] == "Isotype" for item in antibodies)
