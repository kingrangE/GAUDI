"""Central LLM settings, sourced from the one `.env`-backed config (`app.core.config`).

Two evaluation features share this seam:
- dev-prompting **solver** — a small, *fixed* model (`get_settings`).
- spec-design **generator/judge** — a generator run at *extreme temperature* so vague
  instructions diverge, plus a low-temperature judge (`get_gen_settings`,
  `get_judge_settings`).

Values come from `app.core.config.Settings`, which is the single place that reads `.env`.
We build a *fresh* `Settings()` per call (not the lru_cached `get_settings()`) so a test's
`monkeypatch.setenv(...)` is honored live — pydantic gives `os.environ` precedence over the
`.env` file, so an explicit env var always wins.
"""

from __future__ import annotations

from dataclasses import dataclass


def _app_settings():
    """Fresh central `Settings()` (the one `.env` reader).

    Imported lazily *inside* the call to avoid a circular import: `app/__init__`
    eagerly pulls in `app.main`, whose feature routers import `llm.client` ->
    `llm.config`. A module-level `from app.core.config import ...` would re-enter
    this module before it finishes defining `LLMSettings`. A fresh instance (not the
    lru_cached `get_settings()`) also lets tests toggle env vars via monkeypatch.
    """

    from app.core.config import Settings

    return Settings()


@dataclass(frozen=True)
class LLMSettings:
    """Resolved LLM configuration for a call site."""

    provider: str
    model: str
    temperature: float
    api_key: str | None
    max_tokens: int | None = None


def _provider() -> str:
    return _app_settings().llm_provider


def _api_key() -> str | None:
    # Empty string (the unset default) -> None, so callers can gate on truthiness.
    return _app_settings().openai_api_key or None


def get_settings() -> LLMSettings:
    """dev-prompting solver settings.

    Defaults pick a *small, fixed* OpenAI model so that evaluation measures prompting
    skill rather than raw model capability.
    """

    s = _app_settings()
    return LLMSettings(
        provider=s.llm_provider,
        model=s.solver_model,
        temperature=s.solver_temperature,
        api_key=s.openai_api_key or None,
    )


def get_gen_settings() -> LLMSettings:
    """spec-design generator settings.

    Temperature is intentionally *high* (default 1.3): when the candidate's instruction
    leaves a design decision unspecified, a hot model picks differently each run, so the
    samples diverge; a specific instruction pins the decision and they converge. Output is
    capped (default 800 tokens) so a hot model that rambles can't blow up call latency.
    """

    s = _app_settings()
    return LLMSettings(
        provider=s.llm_provider,
        model=s.spec_gen_model,
        temperature=s.spec_gen_temperature,
        api_key=s.openai_api_key or None,
        max_tokens=s.spec_gen_max_tokens,
    )


def get_judge_settings() -> LLMSettings:
    """spec-design judge settings — low temperature for stable decision extraction."""

    s = _app_settings()
    return LLMSettings(
        provider=s.llm_provider,
        # Judge stays on a strong, reliable model: a weak judge intermittently emits
        # malformed JSON under concurrency, which falsely tanks the score. Generation can
        # be nano. (gpt-5.x uses max_completion_tokens — handled in the client.)
        model=s.spec_judge_model,
        temperature=s.spec_judge_temperature,
        api_key=s.openai_api_key or None,
        max_tokens=s.spec_judge_max_tokens,
    )


def get_sample_count() -> int:
    """How many samples to generate per evaluation (default 10, per the spec)."""

    return _app_settings().spec_samples
