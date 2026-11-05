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


async def complete_structured(
    system: str,
    user: str,
    schema: type[T],
    model: str | None = None,
    *,
    temperature: float | None = None,
) -> T:
    """Run a chat completion that is forced to match ``schema`` and return it parsed.

    ``model`` defaults to the centralized ``settings.llm_model``; the offline
    judge-reliability harness passes an explicit model to sweep across the panel.
    ``temperature`` defaults to the centralized ``settings.judge_temperature`` (0.0): a
    judge must be reproducible, so structured judging runs COLD unless a caller overrides it.
    """
    client = get_client()
    settings = get_settings()
    from feature_demo import limits, meter

    selected = model or settings.llm_model
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    protected = limits.enabled()
    extra = {}
    cap = settings.demo_max_output_tokens
    call = None
    if protected:
        call = await meter.reserve(selected, messages, schema.model_json_schema(), cap)
        client = client.with_options(max_retries=0)
        extra["max_completion_tokens" if selected.startswith("gpt-5") else "max_tokens"] = cap
    usage = None
    try:
        completion = await client.beta.chat.completions.parse(
            model=selected,
            temperature=settings.judge_temperature if temperature is None else temperature,
            messages=messages,
            response_format=schema,
            **extra,
        )
        usage = getattr(completion, "usage", None)
    finally:
        if protected:
            await meter.settle(call, usage, cap)
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("LLM returned no structured output")
    return parsed
