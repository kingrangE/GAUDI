"""Orchestration for the coding-test flow.

Endpoints stay thin; this module owns DB access and runner invocation. The
module-level `runner` is the injection seam — tests monkeypatch it with a fast
in-process fake so no subprocess (and no LLM) runs in unit tests.
"""

from __future__ import annotations

import asyncio
import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.coding_test import tasks
from app.features.coding_test.grading import run_test_cases
from app.features.coding_test.models import Problem, Submission, TestCase
from app.features.coding_test.runner import CodeRunner, SubprocessCodeRunner
from app.features.coding_test.schemas import (
    CaseRunResult,
    CreateSubmissionRequest,
    ProblemDetail,
    ProblemSummary,
    RunResponse,
    SampleCase,
    SubmissionCreated,
    SubmissionResult,
)

# Default runner; monkeypatched in tests.
runner: CodeRunner = SubprocessCodeRunner()


async def _get_problem(db: AsyncSession, problem_id: str) -> Problem:
    problem = await db.get(Problem, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="problem not found")
    return problem


async def _cases(db: AsyncSession, problem_id: str, kind: str) -> list[TestCase]:
    rows = await db.execute(
        select(TestCase)
        .where(TestCase.problem_id == problem_id, TestCase.kind == kind)
        .order_by(TestCase.ordinal)
    )
    return list(rows.scalars())


async def list_problems(db: AsyncSession) -> list[ProblemSummary]:
    rows = await db.execute(select(Problem).order_by(Problem.id))
    return [
        ProblemSummary(id=p.id, title=p.title, difficulty=p.difficulty)
        for p in rows.scalars()
    ]


async def get_problem(db: AsyncSession, problem_id: str) -> ProblemDetail:
    problem = await _get_problem(db, problem_id)
    samples = await _cases(db, problem_id, "sample")
    return ProblemDetail(
        id=problem.id,
        title=problem.title,
        description_md=problem.description_md,
        function_name=problem.function_name,
        starter_code=problem.starter_code,
        difficulty=problem.difficulty,
        sample_cases=[
            SampleCase(args=json.loads(c.args_json), expected=json.loads(c.expected_json))
            for c in samples
        ],
    )


async def run_code(db: AsyncSession, problem_id: str, code: str) -> RunResponse:
    """Execute the visible sample cases synchronously. Nothing is persisted."""
    problem = await _get_problem(db, problem_id)
    samples = await _cases(db, problem_id, "sample")
    cases = [(json.loads(c.args_json), json.loads(c.expected_json)) for c in samples]
    outcomes = await asyncio.to_thread(
        run_test_cases, runner, code, problem.function_name, cases, problem.comparison
    )
    return RunResponse(
        results=[
            CaseRunResult(index=i, passed=o.passed, error=o.error)
            for i, o in enumerate(outcomes)
        ]
    )


async def create_submission(
    db: AsyncSession, req: CreateSubmissionRequest
) -> SubmissionCreated:
    await _get_problem(db, req.problem_id)  # 404 if unknown
    submission = Submission(
        problem_id=req.problem_id, candidate_id=req.candidate_id, code=req.code
    )
    db.add(submission)
    await db.flush()
    await db.commit()
    submission_id = submission.id
    # PR-A: inline grading (returns once graded). The response still reports the
    # initial "grading" status so the client uses the same poll-for-result path
    # it will use against the async (RQ) backend in PR-B.
    await tasks.enqueue_grading(db, submission_id, runner)
    return SubmissionCreated(submission_id=submission_id, status="grading")


async def get_submission(db: AsyncSession, submission_id: str) -> SubmissionResult:
    submission = await db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="submission not found")
    return SubmissionResult(
        id=submission.id,
        problem_id=submission.problem_id,
        candidate_id=submission.candidate_id,
        status=submission.status,
        test_passed=submission.test_passed,
        test_total=submission.test_total,
        strengths=submission.strengths,
        weaknesses=submission.weaknesses,
        analysis_report=submission.analysis_report,
        code_quality_score=submission.code_quality_score,
        error=submission.error,
    )
