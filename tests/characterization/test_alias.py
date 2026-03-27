from data_preprocessing import aggregate_antibodies_by_marker, parse_target_aliases


def _signature_set(antibody_records):
    return {
        (ab["clone"], ab["fluorochrome"], ab["system_code"], ab["catalog_number"])
        for ab in antibody_records
    }


def test_parse_target_aliases_extracts_expected_aliases():
    aliases = set(parse_target_aliases("CD274 (B7-H1, PD-L1)"))
    assert {"cd274", "b7h1", "pdl1"}.issubset(aliases)


def test_parse_target_aliases_supports_comma_and_slash_separator():
    aliases = set(parse_target_aliases("CD45 (LCA/T200)"))
    assert {"cd45", "lc", "t200"}.issubset(aliases)


def test_aggregate_antibodies_indexes_all_aliases(alias_antibody_df, brightness_data):
    by_marker, _ = aggregate_antibodies_by_marker(alias_antibody_df, brightness_data)

    cd274_set = _signature_set(by_marker["cd274"])
    b7h1_set = _signature_set(by_marker["b7h1"])
    pdl1_set = _signature_set(by_marker["pdl1"])

    assert cd274_set == b7h1_set
    assert cd274_set == pdl1_set


def test_aggregate_antibodies_slash_aliases_share_same_antibody_set(alias_antibody_df, brightness_data):
    by_marker, _ = aggregate_antibodies_by_marker(alias_antibody_df, brightness_data)

    cd45_set = _signature_set(by_marker["cd45"])
    lca_set = _signature_set(by_marker["lc"])
    t200_set = _signature_set(by_marker["t200"])

    assert cd45_set == lca_set
    assert cd45_set == t200_set
