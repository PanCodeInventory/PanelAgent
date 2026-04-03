"""Application settings loaded from environment variables and .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration for the FlowCyt Panel API.

    Values are resolved in order: environment variables > .env file > defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # LLM / OpenAI-compatible API
    OPENAI_API_BASE: str = "http://127.0.0.1:1234/v1"
    OPENAI_API_KEY: str = "lm-studio"
    OPENAI_MODEL_NAME: str = "Qwen3-14B"

    # Static data file paths (relative to project root)
    CHANNEL_MAPPING_FILE: str = "channel_mapping.json"
    BRIGHTNESS_MAPPING_FILE: str = "fluorochrome_brightness.json"
    SPECTRAL_DATA_FILE: str = "spectral_data.json"

    # Inventory directory
    INVENTORY_DIR: str = "inventory"

    # Species-to-inventory filename mapping
    SPECIES_INVENTORY_MAP: dict[str, str] = {
        "Mouse": "流式抗体库-20250625小鼠.csv",
        "Human": "流式抗体库-20250625-人.csv",
    }


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


_NAME_MAP = {
    "channel_mapping": "CHANNEL_MAPPING_FILE",
    "brightness_mapping": "BRIGHTNESS_MAPPING_FILE",
    "spectral_data": "SPECTRAL_DATA_FILE",
}


def project_root() -> Path:
    """Return the absolute path to the project root.

    The config.py file is located at backend/app/core/config.py,
    so we use parents[3] to reach the project root.
    """
    return Path(__file__).resolve().parents[3]


def resolve_static_data_path(name: str) -> Path:
    """Resolve a static data file path by name.

    Args:
        name: One of "channel_mapping", "brightness_mapping", "spectral_data"

    Returns:
        Absolute Path to the requested static data file

    Raises:
        KeyError: If name is not recognized
    """
    settings = get_settings()
    attr = _NAME_MAP[name]
    return project_root() / getattr(settings, attr)
