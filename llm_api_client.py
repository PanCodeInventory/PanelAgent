from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

from backend.app.services.llm_settings_store import LlmSettingsStore

load_dotenv()  # Load environment variables from .env file


def _get_effective_settings() -> tuple[str, str, str]:
    """Return (api_base, api_key, model_name) from DB or env fallback."""
    store = LlmSettingsStore()
    env_api_base = os.getenv("OPENAI_API_BASE", "http://127.0.0.1:1234/v1")
    env_api_key = os.getenv("OPENAI_API_KEY", "lm-studio")
    env_model_name = os.getenv("OPENAI_MODEL_NAME", "Qwen3-14B")
    settings = store.get_effective_settings(
        env_api_base=env_api_base,
        env_api_key=env_api_key,
        env_model_name=env_model_name,
    )
    return settings.api_base, settings.api_key, settings.model_name


def consult_gpt_oss(prompt):
    """
    发送请求给本地的 GPT-OSS-20B
    """
    try:
        api_base, api_key, model_name = _get_effective_settings()
        client = OpenAI(base_url=api_base, api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个流式细胞术专家，请以 JSON 格式输出。所有文本内容请使用中文回答。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # 低温度保证逻辑稳定性
            response_format={"type": "json_object"}  # Explicitly request JSON object
        )
        llm_output = response.choices[0].message.content
        print(f"Raw LLM Response: {llm_output}")  # Debug print
        return llm_output
    except Exception as e:
        return f"连接错误: {e}"

