"""Chat clients: Groq (free, OpenAI-compatible) and an offline stub."""

from __future__ import annotations

import time
from typing import Protocol

from redteam.config import Settings

Message = dict[str, str]


class QuotaExhaustedError(RuntimeError):
    """The provider's daily quota is used up — retrying now will not help."""


class ChatClient(Protocol):
    model: str

    def chat(self, messages: list[Message], json_mode: bool = False) -> str: ...


def _is_daily_limit(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(m in text for m in ("per day", "tokens per day", "requests per day", "(tpd)", "(rpd)"))


class GroqClient:
    def __init__(self, settings: Settings, model: str, max_retries: int = 6):
        if not settings.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your free key from https://console.groq.com"
            )
        from openai import OpenAI

        self.model = model
        self.max_retries = max_retries
        self._client = OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url)

    def chat(self, messages: list[Message], json_mode: bool = False) -> str:
        from openai import APIConnectionError, InternalServerError, RateLimitError

        kwargs: dict = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if self.model.startswith("openai/gpt-oss"):
            # Reasoning tokens count against the free quota; low effort is plenty here.
            kwargs["extra_body"] = {"reasoning_effort": "low"}
        for attempt in range(self.max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.model, temperature=0.0, messages=messages, **kwargs
                )
                return response.choices[0].message.content or ""
            except RateLimitError as exc:
                if _is_daily_limit(exc):
                    raise QuotaExhaustedError(
                        f"Groq daily limit reached for {self.model}; it resets within 24 hours."
                    ) from exc
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(min(30, 2 ** (attempt + 1)))
            except (APIConnectionError, InternalServerError):
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(min(30, 2 ** (attempt + 1)))
        raise RuntimeError("unreachable")


def get_client(settings: Settings, model: str) -> ChatClient:
    if settings.llm_provider == "groq":
        return GroqClient(settings, model)
    if settings.llm_provider == "stub":
        from redteam.stub import NaiveStub

        return NaiveStub()
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")
