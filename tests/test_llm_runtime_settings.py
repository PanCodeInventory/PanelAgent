"""Tests for llm_api_client runtime settings switching and env fallback."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _fake_choice(content: str) -> MagicMock:
    choice = MagicMock()
    choice.message.content = content
    return choice


def _fake_response(content: str) -> MagicMock:
    resp = MagicMock()
    resp.choices = [_fake_choice(content)]
    return resp


class TestRuntimeSettingsSwitch:
    """When DB settings change between calls, consult_gpt_oss uses the new values."""

    @patch("llm_api_client.OpenAI")
    @patch("llm_api_client.LlmSettingsStore")
    def test_second_call_uses_updated_settings(self, MockStore, MockOpenAI):
        settings_a = MagicMock()
        settings_a.api_base = "http://host-a:1234/v1"
        settings_a.api_key = "key-a"
        settings_a.model_name = "Model-A"

        settings_b = MagicMock()
        settings_b.api_base = "http://host-b:4567/v1"
        settings_b.api_key = "key-b"
        settings_b.model_name = "Model-B"

        store_instance = MockStore.return_value
        store_instance.get_effective_settings.side_effect = [settings_a, settings_b]

        client_a = MagicMock()
        client_b = MagicMock()
        MockOpenAI.side_effect = [client_a, client_b]

        client_a.chat.completions.create.return_value = _fake_response('{"result": "a"}')
        client_b.chat.completions.create.return_value = _fake_response('{"result": "b"}')

        from llm_api_client import consult_gpt_oss

        result_a = consult_gpt_oss("prompt-a")
        result_b = consult_gpt_oss("prompt-b")

        assert result_a == '{"result": "a"}'
        assert result_b == '{"result": "b"}'

        MockOpenAI.assert_any_call(base_url="http://host-a:1234/v1", api_key="key-a")
        MockOpenAI.assert_any_call(base_url="http://host-b:4567/v1", api_key="key-b")

        client_a.chat.completions.create.assert_called_once_with(
            model="Model-A",
            messages=[
                {"role": "system", "content": "你是一个流式细胞术专家，请以 JSON 格式输出。所有文本内容请使用中文回答。"},
                {"role": "user", "content": "prompt-a"},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        client_b.chat.completions.create.assert_called_once_with(
            model="Model-B",
            messages=[
                {"role": "system", "content": "你是一个流式细胞术专家，请以 JSON 格式输出。所有文本内容请使用中文回答。"},
                {"role": "user", "content": "prompt-b"},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )


class TestEnvFallback:
    """When DB has no settings row, env defaults are used."""

    @patch("llm_api_client.OpenAI")
    @patch("llm_api_client.LlmSettingsStore")
    def test_env_defaults_used_when_db_empty(self, MockStore, MockOpenAI):
        from backend.app.services.llm_settings_store import LlmSettings

        store_instance = MockStore.return_value
        store_instance.get_effective_settings.return_value = LlmSettings(
            api_base="http://127.0.0.1:1234/v1",
            api_key="lm-studio",
            model_name="Qwen3-14B",
        )

        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_client.chat.completions.create.return_value = _fake_response('{"ok": true}')

        from llm_api_client import consult_gpt_oss

        result = consult_gpt_oss("test")

        assert result == '{"ok": true}'
        MockOpenAI.assert_called_once_with(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio",
        )
        mock_client.chat.completions.create.assert_called_once_with(
            model="Qwen3-14B",
            messages=[
                {"role": "system", "content": "你是一个流式细胞术专家，请以 JSON 格式输出。所有文本内容请使用中文回答。"},
                {"role": "user", "content": "test"},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )


class TestErrorHandling:
    """Exception during OpenAI call returns error string."""

    @patch("llm_api_client.OpenAI")
    @patch("llm_api_client.LlmSettingsStore")
    def test_returns_error_string_on_exception(self, MockStore, MockOpenAI):
        from backend.app.services.llm_settings_store import LlmSettings

        store_instance = MockStore.return_value
        store_instance.get_effective_settings.return_value = LlmSettings(
            api_base="http://127.0.0.1:1234/v1",
            api_key="lm-studio",
            model_name="Qwen3-14B",
        )

        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_client.chat.completions.create.side_effect = ConnectionError("refused")

        from llm_api_client import consult_gpt_oss

        result = consult_gpt_oss("test")
        assert result.startswith("连接错误:")
        assert "refused" in result

    @patch("llm_api_client.OpenAI")
    @patch("llm_api_client.LlmSettingsStore")
    def test_returns_error_on_settings_store_failure(self, MockStore, MockOpenAI):
        MockStore.return_value.get_effective_settings.side_effect = RuntimeError("db broken")

        from llm_api_client import consult_gpt_oss

        result = consult_gpt_oss("test")
        assert result.startswith("连接错误:")
        assert "db broken" in result
