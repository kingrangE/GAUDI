"""LLM client interface + OpenAI implementation.

The single `complete()` method is the patchable seam: unit tests inject a fake client
(see the test-writing skill) so they never hit the network or need an API key. A
per-call `temperature` override lets one client serve both hot generation and cold
judging; `max_tokens` (from settings or per call) bounds output so a hot model can't
ramble to the model's max length and stall the request.
"""

from __future__ import annotations

from typing import Protocol

from llm.config import (
    LLMSettings,
    get_gen_settings,
    get_judge_settings,
    get_settings,
)


class LLMClient(Protocol):
    """Minimal chat-completion contract used across the backend."""

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        ...


class OpenAIClient:
    """Thin OpenAI wrapper. The `openai` package is imported lazily so importing this
    module (and running mocked unit tests) never requires the dependency or a key."""

    def __init__(self, settings: LLMSettings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._settings.api_key)
        return self._client

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        limit = self._settings.max_tokens if max_tokens is None else max_tokens
        extra: dict = {}
        if limit is not None:
            # gpt-5.x renamed the output cap to max_completion_tokens; older models still
            # use max_tokens.
            if self._settings.model.startswith("gpt-5"):
                extra["max_completion_tokens"] = limit
            else:
                extra["max_tokens"] = limit
        resp = self._ensure_client().chat.completions.create(
            model=self._settings.model,
            temperature=self._settings.temperature if temperature is None else temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **extra,
        )
        return resp.choices[0].message.content or ""


def get_llm_client(settings: LLMSettings | None = None) -> LLMClient:
    """Factory for the configured LLM client."""

    return OpenAIClient(settings)


def get_gen_client() -> LLMClient:
    """spec-design generator client (hot model)."""

    return OpenAIClient(get_gen_settings())


def get_judge_client() -> LLMClient:
    """spec-design judge client (cold model)."""

    return OpenAIClient(get_judge_settings())
