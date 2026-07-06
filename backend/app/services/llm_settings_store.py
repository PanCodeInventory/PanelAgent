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
    provider: Optional[str] = None
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
        env_provider: str | None = "lmstudio",
    ) -> LlmSettings:
        """Return settings from DB if present, otherwise fall back to env defaults."""
        conn = get_connection(self._db_path)
        try:
            row = conn.execute(
                "SELECT api_base, api_key, model_name, provider, updated_at "
                "FROM llm_settings WHERE id = 1"
            ).fetchone()
        finally:
            conn.close()

        if row is not None:
            # A DB row may have been saved with blank fields (e.g. an admin
            # update that cleared model_name). Treat any *blank* DB field as
            # "unset" and fall back to the env default so the LLM call still
            # has valid credentials/model. Non-blank DB values always win.
            def _pick(db_val: str | None, env_val: str | None) -> str | None:
                return db_val if (db_val and db_val.strip()) else env_val

            def _pick_provider(db_val: str | None) -> str | None:
                # Empty provider is meaningful (e.g. "custom"); only fall back
                # when the column is truly absent (None). A blank string is
                # preserved as-is.
                return db_val if db_val is not None else env_provider

            return LlmSettings(
                api_base=_pick(row["api_base"], env_api_base) or env_api_base,
                api_key=_pick(row["api_key"], env_api_key),
                model_name=_pick(row["model_name"], env_model_name) or env_model_name,
                provider=_pick_provider(row["provider"]),
                updated_at=row["updated_at"],
            )

        return LlmSettings(
            api_base=env_api_base,
            api_key=env_api_key,
            model_name=env_model_name,
            provider=env_provider,
            updated_at=_now_iso(),
        )

    def upsert(
        self,
        api_base: str,
        model_name: str,
        api_key: str | None = None,
        provider: str | None = None,
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
                    "INSERT INTO llm_settings (id, api_base, api_key, model_name, provider, updated_at) "
                    "VALUES (1, ?, ?, ?, ?, ?)",
                    (api_base, api_key, model_name, provider, now),
                )
            else:
                conn.execute(
                    "UPDATE llm_settings "
                    "SET api_base = ?, api_key = ?, model_name = ?, provider = ?, updated_at = ? "
                    "WHERE id = 1",
                    (api_base, api_key, model_name, provider, now),
                )
            conn.commit()
        finally:
            conn.close()

        return LlmSettings(
            api_base=api_base,
            api_key=api_key,
            model_name=model_name,
            provider=provider,
            updated_at=now,
        )
