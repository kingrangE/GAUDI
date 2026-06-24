"""Benefit-driven composite scorer (SPEC §5).

Combines four axes — grounding + conciseness (deterministic, always run) and coverage +
boundary (LLM, run only when a client is available) — into one weighted EvaluationReport.
The split follows the research: deterministic/judge signals are cheap and low-noise, while
behavioral correctness/efficiency deltas are too noisy for a single live run (kept offline).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from feature_context_engineering.judge import (
    COVERAGE_WEIGHT,
    DEFAULT_COVERAGE_RUNS,
    coverage_consensus,
)
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
    coverage_runs: int = DEFAULT_COVERAGE_RUNS,
) -> EvaluationReport:
    """Score the submission across the four axes and return the weighted composite.

    When a client is available the coverage judge runs ``coverage_runs`` times and each
    criterion's verdict is a majority vote (see ``coverage_consensus``), so a noisy judge
    can't swing a borderline criterion on a single roll.
    """

    grounding = grounding_dimension(project, submission)
    efficiency = efficiency_dimension(submission)

    results: list[CriterionResult] = []
    if client is not None:
        # Coverage (several judge calls) and boundary (one probe call) are independent —
        # run them concurrently so the boundary call overlaps the coverage calls instead of
        # waiting for them to finish. Combined with the parallel runs inside
        # coverage_consensus, this collapses ~4 sequential LLM round-trips into ~1.
        with ThreadPoolExecutor(max_workers=2) as pool:
            coverage_future = pool.submit(
                coverage_consensus, client, project, submission, runs=coverage_runs
            )
            boundary_future = pool.submit(boundary_dimension, client, project, submission)
            coverage, results = coverage_future.result()
            boundary = boundary_future.result()
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
