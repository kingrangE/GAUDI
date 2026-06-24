"""Helper for structured (JSON-schema-constrained) LLM completions.

Generation and judging both go through this single helper so the model ID and
the structured-output mechanism live in one place. Unit tests mock the feature
functions that call this, so this code path is not exercised offline.
"""

from typing import TypeVar

from pydantic import BaseModel

from app.core.config import get_settings
from app.llm.client import get_client

T = TypeVar("T", bound=BaseModel)


async def complete_structured(system: str, user: str, schema: type[T]) -> T:
    """Run a chat completion that is forced to match ``schema`` and return it parsed."""
    client = get_client()
    settings = get_settings()
    completion = await client.beta.chat.completions.parse(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=schema,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("LLM returned no structured output")
    return parsed
