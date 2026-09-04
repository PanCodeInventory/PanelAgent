"""Settings endpoints — global singleton LLM configuration (read-only, env-sourced)."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.core.config import get_settings
from backend.app.schemas.settings import (
    LlmSettingsResponse,
    ProviderPreset,
)
from backend.app.services.llm_providers import PROVIDERS
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


def _build_response(settings) -> LlmSettingsResponse:
    return LlmSettingsResponse(
        api_base=settings.api_base,
        model_name=settings.model_name,
        has_api_key=settings.api_key is not None and settings.api_key != "",
        api_key_masked=_mask_api_key(settings.api_key),
        provider=settings.provider,
        source="env-default",
    )


@router.get("/providers", response_model=list[ProviderPreset])
async def list_providers() -> list[ProviderPreset]:
    """Return the static catalog of LLM provider presets."""
    return [ProviderPreset(**preset) for preset in PROVIDERS]


@router.get("/llm", response_model=LlmSettingsResponse)
async def get_llm_settings() -> LlmSettingsResponse:
    cfg = get_settings()
    settings = _store().get_effective_settings(
        env_api_base=cfg.OPENAI_API_BASE,
        env_api_key=cfg.OPENAI_API_KEY,
        env_model_name=cfg.OPENAI_MODEL_NAME,
    )
    return _build_response(settings)
