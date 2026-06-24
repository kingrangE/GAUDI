"""Judge each sample, then aggregate into requirement coverage + decision quality.

The judge (low temperature) reads one sample and reports, against the task's explicit
spec: which functional requirements it satisfies, and which graded option it chose for
each decision dimension. Aggregation turns N judgements into per-requirement satisfaction
rates and per-dimension `agreement × quality(modal)` scores.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections import Counter

from feature_spec_design.models import (
    QUALITY_SCORES,
    UNSPECIFIED,
    DecisionDimension,
    DimensionResult,
    RequirementResult,
    Sample,
    SampleJudgement,
    SpecTask,
)
from llm.client import LLMClient

DEFAULT_DIVERGENCE_THRESHOLD = 0.7
DEFAULT_REQUIREMENT_THRESHOLD = 0.7

JUDGE_SYSTEM = (
    "You audit a backend implementation against an explicit spec. You are given the "
    "implementation text, a list of functional REQUIREMENTS (id + text), and a list of "
    "decision DIMENSIONS (key + allowed values). Respond with ONLY a JSON object: "
    '{"requirements_met": [<requirement ids clearly satisfied>], '
    '"decisions": {<dimension key>: <one allowed value, or "unspecified" if not addressed>}}. '
    "Use only the allowed values for decisions. No prose."
)

_FENCE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL)


def quality_of(dim: DecisionDimension, value: str) -> tuple[str, float]:
    """Grade label + numeric score for a chosen value (unknown/unspecified -> 0)."""

    grades = {opt.value: opt.quality for opt in dim.options}
    grade = grades.get(value)
    if grade is not None:
        return grade, QUALITY_SCORES[grade]
    return (UNSPECIFIED if value == UNSPECIFIED else "unknown"), 0.0


def build_judge_prompt(task: SpecTask, sample: Sample) -> str:
    reqs = "\n".join(f"- {r.id}: {r.text}" for r in task.requirements)
    dims = "\n".join(
        f"- {d.key} (allowed: {', '.join(o.value for o in d.options)}, or unspecified)"
        for d in task.dimensions
    )
    return (
        f"# Requirements\n{reqs}\n\n# Dimensions\n{dims}\n\n# Implementation\n{sample.content}"
    )


def parse_judgement(raw: str, task: SpecTask, index: int) -> SampleJudgement:
    """Parse the judge's JSON, defaulting/validating against the task spec."""

    match = _FENCE.search(raw)
    payload = (match.group(1) if match else raw).strip()
    try:
        data = json.loads(payload)
        if not isinstance(data, dict):
            data = {}
    except (json.JSONDecodeError, ValueError):
        data = {}

    valid_req_ids = {r.id for r in task.requirements}
    met_raw = data.get("requirements_met", [])
    met = [str(r) for r in met_raw] if isinstance(met_raw, list) else []
    requirements_met = [r for r in met if r in valid_req_ids]

    decisions_raw = data.get("decisions", {})
    if not isinstance(decisions_raw, dict):
        decisions_raw = {}
    decisions: dict[str, str] = {}
    for dim in task.dimensions:
        value = decisions_raw.get(dim.key, UNSPECIFIED)
        text = str(value).strip().lower() if value is not None else UNSPECIFIED
        decisions[dim.key] = text or UNSPECIFIED

    return SampleJudgement(index=index, requirements_met=requirements_met, decisions=decisions)


def judge_sample(client: LLMClient, task: SpecTask, sample: Sample) -> SampleJudgement:
    raw = client.complete(JUDGE_SYSTEM, build_judge_prompt(task, sample), temperature=0.0)
    return parse_judgement(raw, task, sample.index)


async def judge_all(
    client: LLMClient, task: SpecTask, samples: list[Sample]
) -> list[SampleJudgement]:
    async def one(s: Sample) -> SampleJudgement:
        return await asyncio.to_thread(judge_sample, client, task, s)

    return list(await asyncio.gather(*(one(s) for s in samples)))


def aggregate_requirements(
    judgements: list[SampleJudgement], task: SpecTask, threshold: float
) -> list[RequirementResult]:
    n = len(judgements) or 1
    results: list[RequirementResult] = []
    for req in task.requirements:
        met = sum(1 for j in judgements if req.id in j.requirements_met)
        satisfaction = met / n
        results.append(
            RequirementResult(
                id=req.id,
                text=req.text,
                met_count=met,
                total=n,
                satisfaction=round(satisfaction, 4),
                satisfied=satisfaction >= threshold,
            )
        )
    return results


def aggregate_dimensions(
    judgements: list[SampleJudgement], task: SpecTask, threshold: float
) -> list[DimensionResult]:
    n = len(judgements) or 1
    results: list[DimensionResult] = []
    for dim in task.dimensions:
        values = [j.decisions.get(dim.key, UNSPECIFIED) for j in judgements]
        counts = Counter(values)
        top_value, top_count = counts.most_common(1)[0]
        agreement = top_count / n
        grade, qscore = quality_of(dim, top_value)
        results.append(
            DimensionResult(
                key=dim.key,
                label=dim.label,
                distribution=dict(counts),
                top_value=top_value,
                agreement=round(agreement, 4),
                quality=grade,
                quality_score=qscore,
                score=round(agreement * qscore, 4),
                diverged=agreement < threshold,
            )
        )
    return results


async def analyze(
    samples: list[Sample],
    task: SpecTask,
    client: LLMClient,
    *,
    divergence_threshold: float = DEFAULT_DIVERGENCE_THRESHOLD,
    requirement_threshold: float = DEFAULT_REQUIREMENT_THRESHOLD,
) -> tuple[list[RequirementResult], list[DimensionResult]]:
    """Judge every sample concurrently, then aggregate requirements + dimensions."""

    judgements = await judge_all(client, task, samples)
    requirements = aggregate_requirements(judgements, task, requirement_threshold)
    dimensions = aggregate_dimensions(judgements, task, divergence_threshold)
    return requirements, dimensions
