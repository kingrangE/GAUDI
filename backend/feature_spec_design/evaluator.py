"""Orchestration: instruction -> N hot samples -> requirement+decision analysis -> score.

Generator and judge clients are injectable so unit tests mock the LLM. The whole flow is
async because the N generations and N judgements each run concurrently.
"""

from __future__ import annotations

from feature_spec_design.analyzer import (
    DEFAULT_DIVERGENCE_THRESHOLD,
    DEFAULT_OVERENGINEERING_THRESHOLD,
    DEFAULT_REQUIREMENT_THRESHOLD,
    analyze,
)
from feature_spec_design.generator import generate_samples
from feature_spec_design.models import EvaluationResult, SpecTask
from feature_spec_design.scorer import score_spec
from llm.client import LLMClient, get_gen_client, get_judge_client
from llm.config import get_gen_settings, get_sample_count


async def evaluate(
    task: SpecTask,
    instruction: str,
    *,
    gen_client: LLMClient | None = None,
    judge_client: LLMClient | None = None,
    n: int | None = None,
    temperature: float | None = None,
    divergence_threshold: float = DEFAULT_DIVERGENCE_THRESHOLD,
    requirement_threshold: float = DEFAULT_REQUIREMENT_THRESHOLD,
    overengineering_threshold: float = DEFAULT_OVERENGINEERING_THRESHOLD,
) -> EvaluationResult:
    """Run the full spec-design evaluation for one instruction."""

    gen_client = gen_client or get_gen_client()
    judge_client = judge_client or get_judge_client()
    n = n if n is not None else get_sample_count()
    temperature = temperature if temperature is not None else get_gen_settings().temperature

    samples = await generate_samples(
        gen_client, task, instruction, n=n, temperature=temperature
    )
    requirements, dimensions, overengineering = await analyze(
        samples,
        task,
        judge_client,
        divergence_threshold=divergence_threshold,
        requirement_threshold=requirement_threshold,
        overengineering_threshold=overengineering_threshold,
    )
    score = score_spec(requirements, dimensions, overengineering)

    return EvaluationResult(
        task_id=task.id,
        instruction=instruction,
        total_score=score.total,
        score=score,
        requirements=requirements,
        dimensions=dimensions,
        overengineering=overengineering,
        samples=samples,
    )
