"""Deterministic test-case grading.

Comparison and pass/fail counting are pure and fully testable with a fake
`CodeRunner`. `grade_submission` is the inline (synchronous) grading path used
in PR-A; PR-B extends it to also run the LLM judge and moves the call into an
RQ worker.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.coding_test.judge import judge_submission
from app.features.coding_test.models import Problem, Submission, TestCase
from app.features.coding_test.runner import (
    DEFAULT_MEM_LIMIT_MB,
    DEFAULT_TIMEOUT_S,
    CodeRunner,
)


@dataclass(frozen=True)
class CaseOutcome:
    passed: bool
    error: str | None = None


def _canon(value):
    """Order-insensitive canonical form: recursively sort lists by JSON key."""
    if isinstance(value, list):
        return sorted(
            (_canon(item) for item in value),
            key=lambda e: json.dumps(e, sort_keys=True),
        )
    return value


def compare(actual, expected, comparison: str) -> bool:
    if comparison == "unordered":
        return _canon(actual) == _canon(expected)
    return actual == expected


def run_test_cases(
    runner: CodeRunner,
    code: str,
    function_name: str,
    cases: list[tuple[list, object]],
    comparison: str,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    mem_limit_mb: int = DEFAULT_MEM_LIMIT_MB,
) -> list[CaseOutcome]:
    """Execute each (args, expected) case and classify the outcome.

    Blocking (the subprocess runner is synchronous); callers wrap this in a
    thread so the event loop is not blocked.
    """
    outcomes: list[CaseOutcome] = []
    for args, expected in cases:
        result = runner.execute(code, function_name, args, timeout_s, mem_limit_mb)
        if not result.ok:
            outcomes.append(CaseOutcome(passed=False, error=result.error))
        elif compare(result.value, expected, comparison):
            outcomes.append(CaseOutcome(passed=True))
        else:
            outcomes.append(CaseOutcome(passed=False, error="wrong_answer"))
    return outcomes


def _decode_cases(test_cases: list[TestCase]) -> list[tuple[list, object]]:
    return [(json.loads(tc.args_json), json.loads(tc.expected_json)) for tc in test_cases]


async def grade_submission(
    db: AsyncSession, submission_id: str, runner: CodeRunner
) -> None:
    """Run hidden grading cases, write the deterministic test score.

    PR-B extends this to also populate the LLM-judge fields. On any runner
    failure the submission is marked ``failed`` with an error message.
    """
    submission = await db.get(Submission, submission_id)
    if submission is None:
        return

    try:
        rows = await db.execute(
            select(TestCase)
            .where(
                TestCase.problem_id == submission.problem_id,
                TestCase.kind == "grading",
            )
            .order_by(TestCase.ordinal)
        )
        grading_cases = list(rows.scalars())
        problem = await db.get(Problem, submission.problem_id)
        comparison = problem.comparison if problem else "exact"

        cases = _decode_cases(grading_cases)
        outcomes = await asyncio.to_thread(
            run_test_cases, runner, submission.code, problem.function_name, cases, comparison
        )
        submission.test_passed = sum(1 for o in outcomes if o.passed)
        submission.test_total = len(outcomes)

        # LLM judge: code-quality report grounded on the deterministic score.
        case_breakdown = [
            {"index": i, "passed": o.passed, "error": o.error}
            for i, o in enumerate(outcomes)
        ]
        judgement = await judge_submission(
            title=problem.title,
            description_md=problem.description_md,
            rubric=problem.rubric,
            reference_solution=problem.reference_solution,
            function_name=problem.function_name,
            code=submission.code,
            test_passed=submission.test_passed,
            test_total=submission.test_total,
            case_breakdown=case_breakdown,
        )
        submission.strengths = judgement.strengths
        submission.weaknesses = judgement.weaknesses
        submission.analysis_report = judgement.analysis_report
        submission.code_quality_score = judgement.code_quality_score
        submission.status = "graded"
    except Exception as exc:  # noqa: BLE001 — surface failure to the candidate
        submission.status = "failed"
        submission.error = f"{type(exc).__name__}: {exc}"[:300]

    await db.commit()
