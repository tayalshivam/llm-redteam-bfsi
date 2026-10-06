"""Settings from environment variables (and a local .env file)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _env(name: str, default: str) -> str:
    return os.getenv(name, "").strip() or default


@dataclass(frozen=True)
class Settings:
    groq_api_key: str = field(default_factory=lambda: _env("GROQ_API_KEY", ""))
    groq_base_url: str = field(default_factory=lambda: _env("GROQ_BASE_URL", "https://api.groq.com/openai/v1"))
    target_model: str = field(default_factory=lambda: _env("TARGET_MODEL", "openai/gpt-oss-20b"))
    judge_model: str = field(default_factory=lambda: _env("JUDGE_MODEL", "openai/gpt-oss-120b"))
    # "groq" for real runs; "stub" is a deliberately naive offline model for unit tests.
    llm_provider: str = field(default_factory=lambda: _env("LLM_PROVIDER", "groq"))


def get_settings() -> Settings:
    return Settings()
