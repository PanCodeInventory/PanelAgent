from panelagent.db import SCHEMA_VERSION, ensure_schema, schema_version
from panelagent.resolve import resolve_fluorochrome
from panelagent.seed import seed_database


def test_schema_is_idempotent_and_wal_enabled(seeded_conn):
    ensure_schema(seeded_conn)
    ensure_schema(seeded_conn)
    assert schema_version(seeded_conn) == SCHEMA_VERSION
    assert seeded_conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    antibody_columns = {row["name"] for row in seeded_conn.execute("PRAGMA table_info(antibodies)")}
    assert "library" in antibody_columns


def test_seed_counts_and_all_mapping_names_resolve(seeded_conn):
    expected = {
        "fluorochrome_spectra": 49,
        "fluorochrome_brightness": 34,
        "instruments": 1,
        "channel_mapping": 57,
    }
    for table, count in expected.items():
        assert seeded_conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == count
    assert seeded_conn.execute("SELECT count(*) FROM channels").fetchone()[0] == 14
    names = [row[0] for row in seeded_conn.execute("SELECT fluorochrome FROM channel_mapping")]
    assert all(resolve_fluorochrome(seeded_conn, name) is not None for name in names)


def test_resolution_exact_alias_and_unknown(seeded_conn):
    assert resolve_fluorochrome(seeded_conn, "PE").canonical_name == "PE"
    af488 = resolve_fluorochrome(seeded_conn, "AF488")
    assert af488.canonical_name == "Alexa Fluor® 488"
    assert af488.brightness == 3
    assert resolve_fluorochrome(seeded_conn, "does-not-exist") is None


def test_real_spellings_resolve_existing_brightness(seeded_conn):
    expected = {
        "PE/Cyanine7": 5,
        "PerCP/Cyanine5.5": 3,
        "APC/Cyanine7": 4,
        "Brilliant Violet 421™": 2,
        "Brilliant Violet 605™": 4,
        "Brilliant Violet 785™": 4,
        "Brilliant Violet 786™": 4,
        "Alexa Fluor® 594": 4,
        "Alexa Fluor® 647": 4,
        "APC/Fire™ 750": 4,
        "KIRAVIA Blue 520™": 2,
    }
    for name, brightness in expected.items():
        assert resolve_fluorochrome(seeded_conn, name).brightness == brightness


def test_brightness_seed_normalizes_keys_and_reports_true_orphans(seeded_conn):
    report = seed_database(seeded_conn)
    orphan_names = {warning.rsplit(": ", 1)[1] for warning in report.warnings}
    assert orphan_names == {
        "V450",
        "V500",
        "AmCyan",
        "BUV395",
        "BUV496",
        "BUV563",
        "BUV661",
        "BUV737",
        "BUV805",
    }
    names = {row[0] for row in seeded_conn.execute("SELECT name FROM fluorochrome_brightness")}
    assert "Alexa Fluor 647" not in names
    assert "Alexa Fluor® 647" in names
