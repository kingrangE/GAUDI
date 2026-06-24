"""Central LLM settings, read from environment (never hardcode secrets/model IDs)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMSettings:
    """Resolved LLM configuration for a call site."""

    provider: str
    model: str
    temperature: float
    api_key: str | None


def get_settings() -> LLMSettings:
    """Build settings from environment variables.

    Defaults to a small OpenAI model at temperature 0 so LLM-as-judge scoring is as
    reproducible as possible.
    """

    return LLMSettings(
        provider=os.getenv("LLM_PROVIDER", "openai"),
        model=os.getenv("JUDGE_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("JUDGE_TEMPERATURE", "0")),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
