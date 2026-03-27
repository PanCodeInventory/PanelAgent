from panel_generator import find_valid_panels


def test_find_valid_panels_no_duplicate_system_codes(antibodies_by_marker):
    markers = ["cd3", "cd4", "cd8"]
    panels = find_valid_panels(markers, antibodies_by_marker, max_solutions=5)

    assert panels
    for panel in panels:
        system_codes = [ab["system_code"] for ab in panel.values()]
        assert len(system_codes) == len(set(system_codes))


def test_find_valid_panels_uses_scarcity_first_marker_order(antibodies_by_marker):
    markers = ["cd8", "cd4", "cd3"]
    panels = find_valid_panels(markers, antibodies_by_marker, max_solutions=1)

    assert panels
    first_panel = panels[0]
    assert list(first_panel.keys())[0] == "cd3"


def test_find_valid_panels_respects_max_solutions_cap(antibodies_by_marker):
    markers = ["cd3", "cd4", "cd8"]
    panels = find_valid_panels(markers, antibodies_by_marker, max_solutions=2)

    assert len(panels) <= 2
    assert len(panels) == 2
