"""Central LLM settings, read from environment (never hardcode secrets/model IDs).

Two evaluation features share this seam:
- dev-prompting **solver** — a small, *fixed* model (`get_settings`).
- spec-design **generator/judge** — a generator run at *extreme temperature* so vague
  instructions diverge, plus a low-temperature judge (`get_gen_settings`,
  `get_judge_settings`).
"""

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
    max_tokens: int | None = None


def _provider() -> str:
    return os.getenv("LLM_PROVIDER", "openai")


def _api_key() -> str | None:
    return os.getenv("OPENAI_API_KEY")


def get_settings() -> LLMSettings:
    """dev-prompting solver settings.

    Defaults pick a *small, fixed* OpenAI model so that evaluation measures prompting
    skill rather than raw model capability.
    """

    return LLMSettings(
        provider=_provider(),
        model=os.getenv("SOLVER_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("SOLVER_TEMPERATURE", "0.2")),
        api_key=_api_key(),
    )


def get_gen_settings() -> LLMSettings:
    """spec-design generator settings.

    Temperature is intentionally *high* (default 1.3): when the candidate's instruction
    leaves a design decision unspecified, a hot model picks differently each run, so the
    samples diverge; a specific instruction pins the decision and they converge. Output is
    capped (default 800 tokens) so a hot model that rambles can't blow up call latency.
    """

    return LLMSettings(
        provider=_provider(),
        model=os.getenv("SPEC_GEN_MODEL", "gpt-4.1-nano"),
        temperature=float(os.getenv("SPEC_GEN_TEMPERATURE", "1.3")),
        api_key=_api_key(),
        max_tokens=int(os.getenv("SPEC_GEN_MAX_TOKENS", "800")),
    )


def get_judge_settings() -> LLMSettings:
    """spec-design judge settings — low temperature for stable decision extraction."""

    return LLMSettings(
        provider=_provider(),
        # Judge stays on a strong, reliable model: a weak judge intermittently emits
        # malformed JSON under concurrency, which falsely tanks the score. Generation can
        # be nano. (gpt-5.x uses max_completion_tokens — handled in the client.)
        model=os.getenv("SPEC_JUDGE_MODEL", "gpt-5.4"),
        temperature=float(os.getenv("SPEC_JUDGE_TEMPERATURE", "0.0")),
        api_key=_api_key(),
        max_tokens=int(os.getenv("SPEC_JUDGE_MAX_TOKENS", "500")),
    )


def get_sample_count() -> int:
    """How many samples to generate per evaluation (default 10, per the spec)."""

    return int(os.getenv("SPEC_SAMPLES", "10"))
