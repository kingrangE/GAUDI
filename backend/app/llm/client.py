"""OpenAI client accessor.

The client is created lazily so importing this module (and running the test
suite, which mocks the LLM) never requires a real API key.
"""

from functools import lru_cache

from openai import AsyncOpenAI

from app.core.config import get_settings


@lru_cache
def get_client() -> AsyncOpenAI:
    settings = get_settings()
    # Bounded timeout + retries so a stuck call fails fast instead of hanging the
    # request (and the UI) for the SDK's 600s default. See Settings.llm_timeout_seconds.
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )
