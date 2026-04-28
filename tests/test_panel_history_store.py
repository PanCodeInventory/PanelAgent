"""Tests for panel_history_store: create/list/get."""

from pathlib import Path

import pytest

from backend.app.services.panel_history_store import PanelHistoryEntry, PanelHistoryStore


def _make_entry(**overrides) -> PanelHistoryEntry:
    defaults = dict(
        species="Human",
        requested_markers=["CD3", "CD4", "CD8"],
        missing_markers=["CXCR5"],
        selected_panel=[{"marker": "CD3", "fluorochrome": "FITC"}],
        rationale="Test rationale",
        model_name="test-model",
        api_base="http://localhost:1234/v1",
    )
    defaults.update(overrides)
    return PanelHistoryEntry(**defaults)


class TestCreateEntry:
    def test_insert_and_return(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = PanelHistoryStore(str(db))
        entry = _make_entry()
        result = store.create_entry(entry)
        assert result.id == entry.id
        assert result.created_at == entry.created_at
        assert result.species == "Human"

    def test_auto_generated_id_is_uuid(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = PanelHistoryStore(str(db))
        entry = _make_entry()
        result = store.create_entry(entry)
        import uuid

        uuid.UUID(result.id)

    def test_auto_generated_timestamp(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = PanelHistoryStore(str(db))
        entry = _make_entry()
        result = store.create_entry(entry)
        assert result.created_at is not None
        assert "T" in result.created_at


class TestListEntries:
    def test_empty_list(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = PanelHistoryStore(str(db))
        entries = store.list_entries()
        assert entries == []

    def test_returns_entries_descending(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = PanelHistoryStore(str(db))
        e1 = _make_entry(species="Human")
        e2 = _make_entry(species="Mouse")
        store.create_entry(e1)
        store.create_entry(e2)
        entries = store.list_entries()
        assert len(entries) == 2
        assert entries[0].created_at >= entries[1].created_at

    def test_pagination(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = PanelHistoryStore(str(db))
        for i in range(5):
            store.create_entry(_make_entry(species=f"Species-{i}"))
        page1 = store.list_entries(limit=2, offset=0)
        page2 = store.list_entries(limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id


class TestGetEntry:
    def test_returns_entry_by_id(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = PanelHistoryStore(str(db))
        entry = _make_entry()
        store.create_entry(entry)
        result = store.get_entry(entry.id)
        assert result is not None
        assert result.id == entry.id
        assert result.species == "Human"
        assert result.requested_markers == ["CD3", "CD4", "CD8"]
        assert result.missing_markers == ["CXCR5"]
        assert result.selected_panel == [{"marker": "CD3", "fluorochrome": "FITC"}]

    def test_returns_none_for_missing(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = PanelHistoryStore(str(db))
        result = store.get_entry("nonexistent-id")
        assert result is None

    def test_json_fields_roundtrip(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = PanelHistoryStore(str(db))
        entry = _make_entry(
            requested_markers=["CD3", "CD4"],
            missing_markers=["CXCR5", "CCR6"],
            selected_panel=[
                {"marker": "CD3", "fluorochrome": "FITC"},
                {"marker": "CD4", "fluorochrome": "PE"},
            ],
        )
        store.create_entry(entry)
        result = store.get_entry(entry.id)
        assert result is not None
        assert result.requested_markers == ["CD3", "CD4"]
        assert result.missing_markers == ["CXCR5", "CCR6"]
        assert len(result.selected_panel) == 2
        assert result.selected_panel[0]["marker"] == "CD3"
