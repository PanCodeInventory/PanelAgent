"""Unit tests for static data path resolution helpers in config.py."""

import pytest
from pathlib import Path

from backend.app.core.config import project_root, resolve_static_data_path


class TestProjectRoot:
    """Tests for project_root() function."""

    def test_returns_absolute_path(self):
        """project_root() should return an absolute Path."""
        root = project_root()
        assert root.is_absolute()

    def test_contains_backend_directory(self):
        """project_root() should contain the backend directory."""
        root = project_root()
        assert (root / "backend").exists()
        assert (root / "backend").is_dir()

    def test_contains_tests_directory(self):
        """project_root() should contain the tests directory."""
        root = project_root()
        assert (root / "tests").exists()
        assert (root / "tests").is_dir()


class TestResolveStaticDataPath:
    """Tests for resolve_static_data_path() function."""

    def test_resolve_channel_mapping(self):
        """resolve_static_data_path('channel_mapping') should point to channel_mapping.json."""
        path = resolve_static_data_path("channel_mapping")
        assert path.name == "channel_mapping.json"
        assert path.exists()
        assert path.is_file()

    def test_resolve_brightness_mapping(self):
        """resolve_static_data_path('brightness_mapping') should point to fluorochrome_brightness.json."""
        path = resolve_static_data_path("brightness_mapping")
        assert path.name == "fluorochrome_brightness.json"
        assert path.exists()
        assert path.is_file()

    def test_resolve_spectral_data(self):
        """resolve_static_data_path('spectral_data') should point to spectral_data.json."""
        path = resolve_static_data_path("spectral_data")
        assert path.name == "spectral_data.json"
        assert path.exists()
        assert path.is_file()

    def test_returns_absolute_paths(self):
        """All resolved paths should be absolute."""
        for name in ["channel_mapping", "brightness_mapping", "spectral_data"]:
            path = resolve_static_data_path(name)
            assert path.is_absolute()

    def test_raises_key_error_for_unknown_name(self):
        """resolve_static_data_path should raise KeyError for unknown names."""
        with pytest.raises(KeyError):
            resolve_static_data_path("unknown_file")

        with pytest.raises(KeyError):
            resolve_static_data_path("")

        with pytest.raises(KeyError):
            resolve_static_data_path("channel")
