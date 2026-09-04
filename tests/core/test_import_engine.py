from __future__ import annotations

import csv
import json
from pathlib import Path

from panelagent.engine import diagnose_conflicts, generate_candidates
from panelagent.importers import import_antibody_csv, import_instrument_config
from panelagent.repo import Repo

ROOT = Path(__file__).resolve().parents[2]


def test_config_and_inventory_import_is_idempotent(seeded_conn):
    import_instrument_config(seeded_conn, ROOT / "config")
    brightness_names = {row[0] for row in seeded_conn.execute("SELECT name FROM fluorochrome_brightness")}
    assert "Alexa Fluor 647" not in brightness_names
    assert "Alexa Fluor® 647" in brightness_names
    first = import_antibody_csv(seeded_conn, ROOT / "inventory/panel_inventory.csv", "Mouse")
    second = import_antibody_csv(seeded_conn, ROOT / "inventory/panel_inventory.csv", "Mouse")
    with (ROOT / "inventory/panel_inventory.csv").open(encoding="utf-8") as handle:
        expected = sum(1 for _ in csv.DictReader(handle))
    assert first.antibodies == second.antibodies == expected
    assert seeded_conn.execute("SELECT count(*) FROM antibodies").fetchone()[0] == expected


def test_generate_quality_filter_and_brightness_summary(seeded_conn):
    import_antibody_csv(seeded_conn, ROOT / "inventory/panel_inventory.csv", "Mouse")
    repo = Repo(seeded_conn)
    cd3_id = repo.antibodies(library="Mouse", target="CD3")[0]["id"]
    assert repo.annotate(cd3_id, "bad", "failed QC", library="Isotype") is None
    repo.annotate(cd3_id, "bad", "failed QC", library="Mouse")
    assert repo.antibodies(flag="bad")[0]["id"] == cd3_id
    assert generate_candidates(seeded_conn, "Mouse", ["CD3", "CD4", "CD8"])["status"] == "error"
    result = generate_candidates(seeded_conn, "Mouse", ["CD3", "CD4", "CD8"], include_bad=True)
    assert result["status"] == "success"
    for candidate in result["candidates"]:
        assignments = candidate["markers"]
        assert len({item["channel"] for item in assignments.values()}) == 3
        assert candidate["brightness_summary"]["dim_fluorochromes"] == []


def test_diagnose_pigeonhole_and_dead_marker(seeded_conn):
    import_antibody_csv(seeded_conn, ROOT / "inventory/impossible_inventory.csv", "Mouse")
    conflict = diagnose_conflicts(seeded_conn, "Mouse", ["pd1", "ctla4", "lag3"])
    assert conflict["conflict_groups"]
    assert conflict["conflict_groups"][0]["shortage"] == 2
    dead = diagnose_conflicts(seeded_conn, "Mouse", ["unknown"])
    assert dead["dead_markers"] == ["unknown"]


def test_arbitrary_library_names_are_isolated(seeded_conn):
    import_antibody_csv(seeded_conn, ROOT / "inventory/panel_inventory.csv", "Controls")
    repo = Repo(seeded_conn)
    assert len(repo.antibodies(library="Controls")) == 5
    assert repo.antibodies(library="Mouse") == []
    assert generate_candidates(seeded_conn, "Mouse", ["CD3"])["status"] == "error"


def test_import_nullable_fields_name_fallback_and_null_safe_upsert(seeded_conn, tmp_path):
    csv_path = tmp_path / "mixed.csv"
    csv_path.write_text(
        "\ufeffName,Target,Fluorescein,Clone,Catalog Number,Quantity,,\r\n"
        "Zombie Aqua,,,,423102,2,,\r\n"
        ",,FITC,GK1.5,100406,4,,\r\n"
        ",Biotin anti-mouse CD3,,,100243,1,,\r\n"
        ",,,,,,,\r\n",
        encoding="utf-8",
    )
    first = import_antibody_csv(seeded_conn, csv_path, "Mixed")
    second = import_antibody_csv(seeded_conn, csv_path, "Mixed")
    assert first.antibodies == second.antibodies == 3
    assert first.warnings == second.warnings == []
    rows = Repo(seeded_conn).antibodies(library="Mixed")
    assert len(rows) == 3
    assert {row["target"] for row in rows} == {"Zombie Aqua", "Biotin anti-mouse CD3", "-"}
    assert sum(row["fluorochrome"] == "-" for row in rows) == 2
    assert all("" not in json.loads(row["extra"]) for row in rows)
    assert all(None not in json.loads(row["extra"]) for row in rows)
    assert json.loads(rows[0]["extra"])["Quantity"] in {"1", "2", "4"}
    raw = seeded_conn.execute(
        "SELECT target,fluorochrome,clone_name FROM antibodies WHERE library='Mixed' AND catalog_number='423102'"
    ).fetchone()
    assert raw["fluorochrome"] is None


def test_dash_placeholders_are_stored_as_null(seeded_conn, tmp_path):
    csv_path = tmp_path / "dash.csv"
    csv_path.write_text("Target,Fluorescein,Clone,Catalog Number\nCD3,-,-,1\n-,FITC,-,2\n", encoding="utf-8")
    import_antibody_csv(seeded_conn, csv_path, "Dash")
    rows = seeded_conn.execute(
        "SELECT target,fluorochrome,clone_name FROM antibodies WHERE library='Dash' ORDER BY catalog_number"
    ).fetchall()
    assert tuple(rows[0]) == ("CD3", None, None)
    assert tuple(rows[1]) == (None, "FITC", None)


def test_hidden_appledouble_file_is_ignored(seeded_conn, tmp_path):
    hidden = tmp_path / "._inventory.csv"
    hidden.write_bytes(b"not a csv")
    report = import_antibody_csv(seeded_conn, hidden, "Mouse")
    assert report.antibodies == 0
    assert report.warnings == []


def test_real_antibody_vault_imports_all_nonempty_rows_idempotently(seeded_conn):
    vault = ROOT / "antibody_vault"
    files = {
        "Mouse": vault / "流式抗体库-20260413小鼠.csv",
        "Human": vault / "流式抗体库-20260413-人.csv",
        "Isotype": vault / "流式抗体库-Isotype.csv",
        "Others": vault / "流式抗体库-Others.csv",
    }
    reports = [import_antibody_csv(seeded_conn, path, library) for library, path in files.items()]
    first_count = seeded_conn.execute("SELECT count(*) FROM antibodies").fetchone()[0]
    assert sum(report.antibodies for report in reports) == 438
    assert not any(report.warnings for report in reports)
    for library, path in files.items():
        import_antibody_csv(seeded_conn, path, library)
    assert seeded_conn.execute("SELECT count(*) FROM antibodies").fetchone()[0] == first_count
    others = Repo(seeded_conn).antibodies(library="Others")
    assert len(others) == 12
    assert all(row["target"] != "-" and row["fluorochrome"] == "-" for row in others)
    mouse = Repo(seeded_conn).antibodies(library="Mouse")
    assert any(row["target"] == "-" for row in mouse)
