"""LLM client interface + OpenAI implementation.

The single `complete()` method is the patchable seam: unit tests inject a fake client so they
never hit the network or need an API key.
"""

from __future__ import annotations

from typing import Protocol

from llm.config import LLMSettings, get_settings


class LLMClient(Protocol):
    """Minimal chat-completion contract used across the backend."""

    def complete(self, system: str, user: str) -> str: ...


class OpenAIClient:
    """Thin OpenAI wrapper. The `openai` package is imported lazily so importing this module
    (and running mocked unit tests) never requires the dependency or a key."""

    def __init__(self, settings: LLMSettings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._settings.api_key)
        return self._client

    def complete(self, system: str, user: str) -> str:
        resp = self._ensure_client().chat.completions.create(
            model=self._settings.model,
            temperature=self._settings.temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""


def get_llm_client(settings: LLMSettings | None = None) -> LLMClient:
    """Factory for the configured LLM client."""

    return OpenAIClient(settings)
