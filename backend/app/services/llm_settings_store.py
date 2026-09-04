"""Pure environment-sourced LLM settings (no database persistence).

The previous implementation had a "SQLite-first / env-fallback" dual-track
behaviour, which caused settings written via the UI to be lost when a Docker
container was rebuilt (the DB file was not on a mounted volume).  All LLM
settings now come exclusively from environment variables (``config/.env``);
there is no runtime write path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class LlmSettings(BaseModel):
    api_base: str
    api_key: Optional[str] = None
    model_name: str
    provider: Optional[str] = None
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LlmSettingsStore:
    """Read-only LLM settings backed solely by environment defaults.

    There is no longer any database read or write path.  ``__init__`` does not
    touch the database, and :meth:`get_effective_settings` returns exactly the
    environment defaults it is given.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = db_path

    def get_effective_settings(
        self,
        env_api_base: str = "http://127.0.0.1:1234/v1",
        env_api_key: str | None = None,
        env_model_name: str = "Qwen3-14B",
        env_provider: str | None = "lmstudio",
    ) -> LlmSettings:
        """Return the effective settings directly from env defaults (no DB)."""
        return LlmSettings(
            api_base=env_api_base,
            api_key=env_api_key,
            model_name=env_model_name,
            provider=env_provider,
            updated_at=_now_iso(),
        )
