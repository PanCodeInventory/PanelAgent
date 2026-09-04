"""Tests for llm_settings_store: pure env-defaults, no DB persistence."""

from pathlib import Path

from backend.app.services.llm_settings_store import LlmSettingsStore


class TestGetEffectiveSettings:
    def test_returns_env_defaults(self, tmp_path: Path):
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
        assert result.provider == "lmstudio"

    def test_does_not_access_database(self, tmp_path: Path):
        """No DB file is created and no DB is read for a settings lookup."""
        db = tmp_path / "test.sqlite3"
        store = LlmSettingsStore(str(db))
        result = store.get_effective_settings(
            env_api_base="http://env-host:1234/v1",
            env_api_key="env-key",
            env_model_name="env-model",
        )
        assert result.api_base == "http://env-host:1234/v1"
        assert not db.exists()

    def test_no_upsert_method(self, tmp_path: Path):
        """The runtime write path has been removed."""
        assert not hasattr(LlmSettingsStore(str(tmp_path)), "upsert")
