"""Tests for llm_settings_store: get/upsert with env fallback."""

from pathlib import Path

import pytest

from backend.app.services.llm_settings_store import LlmSettingsStore


class TestGetEffectiveSettings:
    def test_returns_env_defaults_when_db_empty(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = LlmSettingsStore(str(db))
        result = store.get_effective_settings(
            env_api_base="http://env-host:1234/v1",
            env_api_key="env-key",
            env_model_name="env-model",
        )
        assert result.api_base == "http://env-host:1234/v1"
        assert result.api_key == "env-key"
        assert result.model_name == "env-model"

    def test_returns_default_env_when_no_args(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = LlmSettingsStore(str(db))
        result = store.get_effective_settings()
        assert result.api_base == "http://127.0.0.1:1234/v1"
        assert result.api_key is None
        assert result.model_name == "Qwen3-14B"

    def test_returns_db_values_when_present(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = LlmSettingsStore(str(db))
        store.upsert(
            api_base="http://db-host:9999/v1",
            model_name="db-model",
            api_key="db-key",
        )
        result = store.get_effective_settings(
            env_api_base="http://env-host:1234/v1",
            env_model_name="env-model",
        )
        assert result.api_base == "http://db-host:9999/v1"
        assert result.api_key == "db-key"
        assert result.model_name == "db-model"


class TestUpsert:
    def test_insert_creates_singleton_row(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = LlmSettingsStore(str(db))
        result = store.upsert(
            api_base="http://host:1234/v1",
            model_name="model-a",
            api_key="key-a",
        )
        assert result.api_base == "http://host:1234/v1"
        assert result.model_name == "model-a"
        assert result.api_key == "key-a"
        assert result.updated_at is not None

    def test_update_overwrites_existing(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = LlmSettingsStore(str(db))
        store.upsert(
            api_base="http://old:1234/v1",
            model_name="old-model",
        )
        result = store.upsert(
            api_base="http://new:5678/v1",
            model_name="new-model",
            api_key="new-key",
        )
        assert result.api_base == "http://new:5678/v1"
        assert result.model_name == "new-model"
        assert result.api_key == "new-key"

        effective = store.get_effective_settings()
        assert effective.api_base == "http://new:5678/v1"

    def test_only_one_row_exists_after_multiple_upserts(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = LlmSettingsStore(str(db))
        import sqlite3

        for i in range(5):
            store.upsert(
                api_base=f"http://host-{i}:1234/v1",
                model_name=f"model-{i}",
            )

        conn = sqlite3.connect(str(db))
        count = conn.execute("SELECT COUNT(*) FROM llm_settings").fetchone()[0]
        conn.close()
        assert count == 1

    def test_api_key_can_be_null(self, tmp_path: Path):
        db = tmp_path / "test.sqlite3"
        store = LlmSettingsStore(str(db))
        result = store.upsert(
            api_base="http://host:1234/v1",
            model_name="model",
            api_key=None,
        )
        assert result.api_key is None
