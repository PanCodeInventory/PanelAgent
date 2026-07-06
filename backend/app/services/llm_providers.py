"""Static catalog of LLM provider presets.

Each preset is an OpenAI-compatible endpoint with a suggested default model.
The provider id is stored on the singleton ``llm_settings`` row purely as a
UI hint — ``api_base`` / ``model_name`` remain the authoritative values used
by the LLM client, so changing provider only prefills those fields.
"""

from __future__ import annotations

from typing import TypedDict


class ProviderPreset(TypedDict):
    id: str
    label: str
    api_base: str
    default_model: str
    key_hint: str


PROVIDERS: list[ProviderPreset] = [
    {
        "id": "lmstudio",
        "label": "LM Studio (本地)",
        "api_base": "http://127.0.0.1:1234/v1",
        "default_model": "Qwen3-14B",
        "key_hint": "lm-studio",
    },
    {
        "id": "openai",
        "label": "OpenAI",
        "api_base": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "key_hint": "sk-...",
    },
    {
        "id": "deepseek",
        "label": "DeepSeek",
        "api_base": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "key_hint": "sk-...",
    },
    {
        "id": "zhipu",
        "label": "智谱 AI (GLM)",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-plus",
        "key_hint": "...",
    },
    {
        "id": "moonshot",
        "label": "Moonshot (Kimi)",
        "api_base": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "key_hint": "sk-...",
    },
    {
        "id": "qwen",
        "label": "通义千问 (DashScope)",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "key_hint": "sk-...",
    },
    {
        "id": "aihubmix",
        "label": "AiHubMix",
        "api_base": "https://aihubmix.com/v1",
        "default_model": "gpt-4o",
        "key_hint": "sk-...",
    },
    {
        "id": "custom",
        "label": "自定义",
        "api_base": "",
        "default_model": "",
        "key_hint": "",
    },
]


def get_provider_by_id(provider_id: str | None) -> ProviderPreset | None:
    """Return the preset matching ``provider_id`` or ``None``."""
    if not provider_id:
        return None
    for preset in PROVIDERS:
        if preset["id"] == provider_id:
            return preset
    return None
