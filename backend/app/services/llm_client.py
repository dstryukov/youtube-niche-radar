from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, TypedDict

import httpx
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

TIMEOUT_SECONDS = 30


class LLMResult(TypedDict):
    content: str
    model: str
    usage: dict | None


def _resolve_api_key(*, provider: str) -> str | None:
    if provider == "gemini":
        return settings.gemini_api_key or settings.llm_api_key
    return settings.groq_api_key or settings.llm_api_key


class LLMClient(ABC):
    def __init__(self, model: str, api_key: str | None) -> None:
        self.model = model
        self.api_key = api_key

    @abstractmethod
    def chat_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> LLMResult: ...


class GroqClient(LLMClient):
    def chat_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel] | None = None,
    ) -> LLMResult:
        if not self.api_key:
            raise ValueError(f"Groq API key is not set (model: {self.model})")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": settings.llm_temperature,
        }

        for attempt in range(settings.llm_max_retries + 1):
            try:
                resp = httpx.post(
                    GROQ_URL,
                    headers=headers,
                    json=body,
                    timeout=TIMEOUT_SECONDS,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage")
                return LLMResult(content=content, model=self.model, usage=usage)
            except Exception as exc:
                logger.warning("GroqClient attempt %d failed: %s", attempt + 1, exc)
                if attempt < settings.llm_max_retries:
                    time.sleep(2 ** attempt)
                else:
                    raise


class GeminiClient(LLMClient):
    def chat_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel] | None = None,
    ) -> LLMResult:
        if not self.api_key:
            raise ValueError(f"Gemini API key is not set (model: {self.model})")
        url = f"{GEMINI_URL.format(model=self.model)}?key={self.api_key}"
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        body: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": combined_prompt}],
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": settings.llm_temperature,
            },
        }

        for attempt in range(settings.llm_max_retries + 1):
            try:
                resp = httpx.post(url, json=body, timeout=TIMEOUT_SECONDS)
                resp.raise_for_status()
                data = resp.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                usage = data.get("usageMetadata")
                return LLMResult(content=content, model=self.model, usage=usage)
            except Exception as exc:
                logger.warning("GeminiClient attempt %d failed: %s", attempt + 1, exc)
                if attempt < settings.llm_max_retries:
                    time.sleep(2 ** attempt)
                else:
                    raise


def get_llm_client(provider: str | None = None, model: str | None = None) -> LLMClient:
    resolved_provider = (provider or settings.llm_provider).lower()
    resolved_model = model or settings.llm_model
    api_key = _resolve_api_key(provider=resolved_provider)

    if resolved_provider == "gemini":
        return GeminiClient(model=resolved_model, api_key=api_key)
    return GroqClient(model=resolved_model, api_key=api_key)
