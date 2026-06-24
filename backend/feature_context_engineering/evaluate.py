"""Benefit-driven composite scorer (SPEC §5).

Combines four axes — grounding + conciseness (deterministic, always run) and coverage +
boundary (LLM, run only when a client is available) — into one weighted EvaluationReport.
The split follows the research: deterministic/judge signals are cheap and low-noise, while
behavioral correctness/efficiency deltas are too noisy for a single live run (kept offline).
"""

from __future__ import annotations

from feature_context_engineering.judge import COVERAGE_WEIGHT, coverage_dimension
from feature_context_engineering.models import (
    CriterionResult,
    DimensionScore,
    EvaluationReport,
    Project,
    Submission,
)
from feature_context_engineering.probe import BOUNDARY_WEIGHT, boundary_dimension
from feature_context_engineering.static_checks import (
    efficiency_dimension,
    grounding_dimension,
)
from llm.client import LLMClient


def build_report(
    project: Project,
    submission: Submission,
    client: LLMClient | None = None,
) -> EvaluationReport:
    """Score the submission across the four axes and return the weighted composite."""

    grounding = grounding_dimension(project, submission)
    efficiency = efficiency_dimension(submission)

    results: list[CriterionResult] = []
    if client is not None:
        coverage, results = coverage_dimension(client, project, submission)
        boundary = boundary_dimension(client, project, submission)
    else:
        coverage = DimensionScore(
            key="coverage", label="컨벤션·모호성 커버리지", weight=COVERAGE_WEIGHT,
            available=False, detail="API 키 없음",
        )
        boundary = DimensionScore(
            key="boundary", label="경계·풋건 회피", weight=BOUNDARY_WEIGHT,
            available=False, detail="API 키 없음",
        )

    dimensions = [coverage, grounding, boundary, efficiency]
    available = [d for d in dimensions if d.available]
    weight_sum = sum(d.weight for d in available)
    total = round(sum(d.score * d.weight for d in available) / weight_sum, 1) if weight_sum else 0.0

    return EvaluationReport(
        project_id=project.id,
        scored=True,
        total=total,
        dimensions=dimensions,
        results=results,
    )
