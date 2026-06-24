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

    Defaults pick a *small, fixed* OpenAI model for the dev-prompting solver so the
    evaluation measures prompting skill rather than raw model capability.
    """

    return LLMSettings(
        provider=os.getenv("LLM_PROVIDER", "openai"),
        model=os.getenv("SOLVER_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("SOLVER_TEMPERATURE", "0.2")),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
