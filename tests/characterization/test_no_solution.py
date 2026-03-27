from panel_generator import diagnose_conflicts, find_valid_panels


def test_diagnose_conflicts_reports_impossible_shared_channel_group(impossible_case):
    markers = impossible_case["markers"]
    antibodies_by_marker = impossible_case["antibodies_by_marker"]

    panels = find_valid_panels(markers, antibodies_by_marker, max_solutions=3)
    assert panels == []

    diagnosis = diagnose_conflicts(markers, antibodies_by_marker)
    assert diagnosis
    assert "冲突组" in diagnosis
    assert impossible_case["shared_channel"] in diagnosis
    for marker in markers:
        assert marker in diagnosis
