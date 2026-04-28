"""Settings endpoints — global singleton LLM configuration."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.core.config import get_settings
from backend.app.schemas.settings import LlmSettingsResponse, LlmSettingsUpdate
from backend.app.services.llm_settings_store import LlmSettingsStore

router = APIRouter(prefix="/settings")


def _mask_api_key(key: str | None) -> str | None:
    if not key:
        return None
    if len(key) >= 8:
        return key[:3] + "****" + key[-4:]
    return "****"


def _store() -> LlmSettingsStore:
    return LlmSettingsStore()


def _build_response(settings, *, is_runtime: bool) -> LlmSettingsResponse:
    return LlmSettingsResponse(
        api_base=settings.api_base,
        model_name=settings.model_name,
        has_api_key=settings.api_key is not None and settings.api_key != "",
        api_key_masked=_mask_api_key(settings.api_key),
        source="runtime" if is_runtime else "env-default",
    )


@router.get("/llm", response_model=LlmSettingsResponse)
async def get_llm_settings() -> LlmSettingsResponse:
    cfg = get_settings()
    store = _store()
    settings = store.get_effective_settings(
        env_api_base=cfg.OPENAI_API_BASE,
        env_api_key=cfg.OPENAI_API_KEY,
        env_model_name=cfg.OPENAI_MODEL_NAME,
    )

    conn = store._db_path  # check if DB row exists to determine source
    from backend.app.services.admin_database import get_connection

    db_conn = get_connection(store._db_path)
    try:
        row = db_conn.execute(
            "SELECT id FROM llm_settings WHERE id = 1"
        ).fetchone()
        is_runtime = row is not None
    finally:
        db_conn.close()

    return _build_response(settings, is_runtime=is_runtime)


@router.put("/llm", response_model=LlmSettingsResponse)
async def put_llm_settings(body: LlmSettingsUpdate) -> LlmSettingsResponse:
    cfg = get_settings()
    store = _store()
    current = store.get_effective_settings(
        env_api_base=cfg.OPENAI_API_BASE,
        env_api_key=cfg.OPENAI_API_KEY,
        env_model_name=cfg.OPENAI_MODEL_NAME,
    )

    api_base = body.api_base if body.api_base is not None else current.api_base
    model_name = body.model_name if body.model_name is not None else current.model_name

    if body.api_key is not None:
        api_key = None if body.api_key == "" else body.api_key
    else:
        api_key = current.api_key

    updated = store.upsert(api_base=api_base, model_name=model_name, api_key=api_key)
    return _build_response(updated, is_runtime=True)
