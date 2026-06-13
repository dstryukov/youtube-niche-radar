from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pytest

from app.services.llm_client import (
    GROQ_URL,
    GeminiClient,
    GroqClient,
    LLMResult,
    get_llm_client,
)

SAMPLE_GROQ_RESPONSE = {
    "choices": [{"message": {"content": '{"format_label": "tutorial / guide"}'}}],
    "usage": {"prompt_tokens": 100, "completion_tokens": 20},
}
SAMPLE_GEMINI_RESPONSE = {
    "candidates": [{"content": {"parts": [{"text": '{"format_label": "quiz"}'}]}}],
    "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 20},
}


class TestGroqClient:
    def test_groq_client_creates_correct_request(self):
        client = GroqClient(model="llama-3.3-70b-versatile", api_key="test-key")
        with patch.object(httpx, "post") as mock_post:
            mock_post.return_value = httpx.Response(
                200,
                json=SAMPLE_GROQ_RESPONSE,
                request=httpx.Request("POST", GROQ_URL),
            )
            result = client.chat_structured(
                system_prompt="system",
                user_prompt="user",
                response_model=None,
            )
            mock_post.assert_called_once()
            call_args, call_kwargs = mock_post.call_args
            assert call_args[0] == GROQ_URL
            assert call_kwargs["headers"]["Authorization"] == "Bearer test-key"
            assert call_kwargs["headers"]["Content-Type"] == "application/json"
            assert call_kwargs["json"]["model"] == "llama-3.3-70b-versatile"
            assert call_kwargs["json"]["response_format"] == {"type": "json_object"}
            assert len(call_kwargs["json"]["messages"]) == 2
            assert call_kwargs["json"]["messages"][0]["role"] == "system"
            assert call_kwargs["json"]["messages"][1]["role"] == "user"
            assert isinstance(result, dict)
            assert result["content"] == '{"format_label": "tutorial / guide"}'

    def test_groq_client_parses_response(self):
        client = GroqClient(model="llama-3.3-70b-versatile", api_key="test-key")
        with patch.object(httpx, "post") as mock_post:
            mock_post.return_value = httpx.Response(
                200,
                json=SAMPLE_GROQ_RESPONSE,
                request=httpx.Request("POST", GROQ_URL),
            )
            result = client.chat_structured(
                system_prompt="system",
                user_prompt="user",
                response_model=None,
            )
            assert result["model"] == "llama-3.3-70b-versatile"
            assert result["usage"] == {"prompt_tokens": 100, "completion_tokens": 20}
            parsed = json.loads(result["content"])
            assert parsed["format_label"] == "tutorial / guide"

    def test_groq_client_handles_api_error(self):
        client = GroqClient(model="llama-3.3-70b-versatile", api_key="test-key")
        with patch.object(httpx, "post") as mock_post:
            mock_post.return_value = httpx.Response(
                401,
                json={"error": "unauthorized"},
                request=httpx.Request("POST", GROQ_URL),
            )
            with pytest.raises(httpx.HTTPStatusError):
                client.chat_structured(
                    system_prompt="system",
                    user_prompt="user",
                    response_model=None,
                )


class TestGeminiClient:
    def test_gemini_client_creates_correct_request(self):
        client = GeminiClient(model="gemini-2.0-flash", api_key="gem-key")
        expected_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=gem-key"
        with patch.object(httpx, "post") as mock_post:
            mock_post.return_value = httpx.Response(
                200,
                json=SAMPLE_GEMINI_RESPONSE,
                request=httpx.Request("POST", expected_url),
            )
            result = client.chat_structured(
                system_prompt="system",
                user_prompt="user",
                response_model=None,
            )
            mock_post.assert_called_once()
            call_args, call_kwargs = mock_post.call_args
            assert call_args[0] == expected_url
            body = call_kwargs["json"]
            assert body["contents"][0]["role"] == "user"
            assert "system" in body["contents"][0]["parts"][0]["text"]
            assert body["generationConfig"]["response_mime_type"] == "application/json"
            assert isinstance(result, dict)

    def test_gemini_client_parses_response(self):
        client = GeminiClient(model="gemini-2.0-flash", api_key="gem-key")
        with patch.object(httpx, "post") as mock_post:
            mock_post.return_value = httpx.Response(
                200,
                json=SAMPLE_GEMINI_RESPONSE,
                request=httpx.Request("POST", "http://example.com"),
            )
            result = client.chat_structured(
                system_prompt="system",
                user_prompt="user",
                response_model=None,
            )
            assert result["model"] == "gemini-2.0-flash"
            assert result["usage"] is not None
            parsed = json.loads(result["content"])
            assert parsed["format_label"] == "quiz"

    def test_gemini_client_handles_api_error(self):
        client = GeminiClient(model="gemini-2.0-flash", api_key="gem-key")
        with patch.object(httpx, "post") as mock_post:
            mock_post.return_value = httpx.Response(
                403,
                json={"error": "forbidden"},
                request=httpx.Request("POST", "http://example.com"),
            )
            with pytest.raises(httpx.HTTPStatusError):
                client.chat_structured(
                    system_prompt="system",
                    user_prompt="user",
                    response_model=None,
                )


class TestLLMFactory:
    def test_llm_factory_default_groq(self):
        with patch("app.services.llm_client.settings") as mock_settings:
            mock_settings.llm_provider = "groq"
            mock_settings.llm_model = "llama-3.3-70b-versatile"
            mock_settings.groq_api_key = "groq-key"
            mock_settings.llm_api_key = None
            client = get_llm_client()
            assert isinstance(client, GroqClient)
            assert client.model == "llama-3.3-70b-versatile"
            assert client.api_key == "groq-key"

    def test_llm_factory_gemini(self):
        with patch("app.services.llm_client.settings") as mock_settings:
            mock_settings.llm_provider = "gemini"
            mock_settings.llm_model = "gemini-2.0-flash"
            mock_settings.gemini_api_key = "gem-key"
            mock_settings.llm_api_key = None
            client = get_llm_client()
            assert isinstance(client, GeminiClient)
            assert client.model == "gemini-2.0-flash"
            assert client.api_key == "gem-key"

    def test_llm_factory_with_overrides(self):
        with patch("app.services.llm_client.settings") as mock_settings:
            mock_settings.llm_provider = "groq"
            mock_settings.groq_api_key = "groq-key"
            client = get_llm_client(provider="gemini", model="gemini-2.0-flash")
            assert isinstance(client, GeminiClient)
            assert client.model == "gemini-2.0-flash"
