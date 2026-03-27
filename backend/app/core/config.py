"""Application settings loaded from environment variables and .env file."""

from functools import lru_cache

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

    # Species-to-inventory filename mapping (mirrors Streamlit INVENTORY_CONFIG)
    SPECIES_INVENTORY_MAP: dict[str, str] = {
        "Mouse": "Mouse_20250625_ZhengLab.csv",
        "Human": "Human_20250625_ZhengLab.csv",
    }


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
