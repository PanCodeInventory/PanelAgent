"""Persistence layer for LLM settings with DB-over-env fallback."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from backend.app.services.admin_database import get_connection, init_db


class LlmSettings(BaseModel):
    api_base: str
    api_key: Optional[str] = None
    model_name: str
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LlmSettingsStore:
    """Read / write the singleton LLM settings row (id = 1).

    When the database row is absent, :meth:`get_effective_settings` falls
    back to caller-supplied environment defaults.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = db_path
        init_db(db_path)

    def get_effective_settings(
        self,
        env_api_base: str = "http://127.0.0.1:1234/v1",
        env_api_key: str | None = None,
        env_model_name: str = "Qwen3-14B",
    ) -> LlmSettings:
        """Return settings from DB if present, otherwise fall back to env defaults."""
        conn = get_connection(self._db_path)
        try:
            row = conn.execute(
                "SELECT api_base, api_key, model_name, updated_at "
                "FROM llm_settings WHERE id = 1"
            ).fetchone()
        finally:
            conn.close()

        if row is not None:
            return LlmSettings(
                api_base=row["api_base"],
                api_key=row["api_key"],
                model_name=row["model_name"],
                updated_at=row["updated_at"],
            )

        return LlmSettings(
            api_base=env_api_base,
            api_key=env_api_key,
            model_name=env_model_name,
            updated_at=_now_iso(),
        )

    def upsert(
        self,
        api_base: str,
        model_name: str,
        api_key: str | None = None,
    ) -> LlmSettings:
        """Create or update the singleton row (id = 1).

        Returns the resulting :class:`LlmSettings`.
        """
        now = _now_iso()
        conn = get_connection(self._db_path)
        try:
            existing = conn.execute(
                "SELECT id FROM llm_settings WHERE id = 1"
            ).fetchone()

            if existing is None:
                conn.execute(
                    "INSERT INTO llm_settings (id, api_base, api_key, model_name, updated_at) "
                    "VALUES (1, ?, ?, ?, ?)",
                    (api_base, api_key, model_name, now),
                )
            else:
                conn.execute(
                    "UPDATE llm_settings "
                    "SET api_base = ?, api_key = ?, model_name = ?, updated_at = ? "
                    "WHERE id = 1",
                    (api_base, api_key, model_name, now),
                )
            conn.commit()
        finally:
            conn.close()

        return LlmSettings(
            api_base=api_base,
            api_key=api_key,
            model_name=model_name,
            updated_at=now,
        )
