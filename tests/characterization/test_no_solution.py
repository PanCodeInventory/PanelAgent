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


def test_diagnose_conflicts_treats_blocked_channels_as_unavailable():
    markers = ["cd3"]
    antibodies_by_marker = {
        "cd3": [
            {"fluorochrome": "BV650", "system_code": "V4_V660"},
        ]
    }

    panels = find_valid_panels(markers, antibodies_by_marker, max_solutions=1)
    assert panels == []

    diagnosis = diagnose_conflicts(markers, antibodies_by_marker)
    assert "没有可用的有效抗体" in diagnosis
    assert "cd3" in diagnosis
