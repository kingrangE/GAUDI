"""Orchestration for the office-prompting evaluation flow.

One session = three fixed problems. Per problem the candidate submits a prompt
which is run against the datasets (up to MAX_RUNS times); only the AI's returned
rows are shown back — never correctness. The LAST run is what gets scored. After
every problem has at least one run, scoring compares each last run's id set to
the precomputed ground truth (deterministic P/R/F1).
"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.office_prompting import datasets
from app.features.office_prompting.extraction import extract_ids
from app.features.office_prompting.models import OfficeAttempt, OfficeSession
from app.features.office_prompting.problems import PROBLEM_COUNT, PROBLEMS
from app.features.office_prompting.schemas import (
    CreateSessionResponse,
    DatasetTable,
    ProblemMeta,
    ResultProblem,
    ResultResponse,
    RunRequest,
    RunResponse,
)
from app.features.office_prompting.scoring import aggregate, score_id_set

MAX_RUNS = 3


async def _get_session(db: AsyncSession, session_id: str) -> OfficeSession:
    session = await db.get(OfficeSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session


async def _get_attempt(db: AsyncSession, session_id: str, problem_index: int) -> OfficeAttempt:
    if not 0 <= problem_index < PROBLEM_COUNT:
        raise HTTPException(status_code=404, detail="problem not found")
    result = await db.execute(
        select(OfficeAttempt).where(
            OfficeAttempt.session_id == session_id,
            OfficeAttempt.problem_index == problem_index,
        )
    )
    attempt = result.scalar_one_or_none()
    if attempt is None:
        raise HTTPException(status_code=404, detail="attempt not found")
    return attempt


def _dataset_payload() -> list[DatasetTable]:
    return [
        DatasetTable(name=name, columns=datasets.COLUMNS[name], rows=datasets.DATASETS[name])
        for name in datasets.COLUMNS
    ]


async def create_session(db: AsyncSession, candidate_name: str) -> CreateSessionResponse:
    session = OfficeSession(candidate_name=candidate_name)
    db.add(session)
    await db.flush()  # assign session.id before linking attempts
    for problem in PROBLEMS:
        db.add(
            OfficeAttempt(
                session_id=session.id,
                problem_index=problem.index,
                problem_title=problem.title,
            )
        )
    await db.commit()
    return CreateSessionResponse(
        session_id=session.id,
        candidate_name=candidate_name,
        problems=[
            ProblemMeta(
                index=p.index,
                title=p.title,
                description=p.description,
                target_entity=p.target_entity,
                max_runs=MAX_RUNS,
            )
            for p in PROBLEMS
        ],
        datasets=_dataset_payload(),
    )


async def run_for_problem(
    db: AsyncSession, session_id: str, problem_index: int, req: RunRequest
) -> RunResponse:
    await _get_session(db, session_id)
    attempt = await _get_attempt(db, session_id, problem_index)
    runs = list(attempt.runs or [])
    if len(runs) >= MAX_RUNS:
        raise HTTPException(status_code=409, detail="no runs remaining")

    problem = PROBLEMS[problem_index]
    output = await extract_ids(problem, req.prompt)
    # Drop hallucinated / out-of-universe ids so they can't unfairly tank precision.
    valid = datasets.existing_ids(problem.target_table)
    predicted_ids = [i for i in dict.fromkeys(output.ids) if i in valid]

    run_number = len(runs) + 1
    runs.append({"run_number": run_number, "prompt": req.prompt, "predicted_ids": predicted_ids})
    attempt.runs = runs
    attempt.last_prompt = req.prompt
    attempt.last_predicted_ids = predicted_ids  # last run is what gets scored
    await db.commit()

    return RunResponse(
        problem_index=problem_index,
        run_number=run_number,
        runs_used=run_number,
        runs_remaining=MAX_RUNS - run_number,
        predicted_ids=predicted_ids,
        predicted_rows=datasets.rows_by_ids(problem.target_table, predicted_ids),
    )


async def score_session(db: AsyncSession, session_id: str) -> ResultResponse:
    session = await _get_session(db, session_id)
    result = await db.execute(
        select(OfficeAttempt)
        .where(OfficeAttempt.session_id == session_id)
        .order_by(OfficeAttempt.problem_index)
    )
    attempts = list(result.scalars())

    per_problem_scores: list[dict] = []
    for attempt in attempts:
        if attempt.last_predicted_ids is None:
            raise HTTPException(
                status_code=409, detail="every problem must be run at least once"
            )
        truth = PROBLEMS[attempt.problem_index].ground_truth_ids
        scored = score_id_set(attempt.last_predicted_ids, truth)
        attempt.score = scored
        attempt.precision = scored["precision"]
        attempt.recall = scored["recall"]
        attempt.f1 = scored["f1"]
        per_problem_scores.append(scored)

    precision, recall, f1 = aggregate(per_problem_scores)
    session.precision, session.recall, session.f1 = precision, recall, f1
    session.status = "scored"
    await db.commit()
    return await get_result(db, session_id)


async def get_result(db: AsyncSession, session_id: str) -> ResultResponse:
    session = await _get_session(db, session_id)
    if session.status != "scored":
        raise HTTPException(status_code=409, detail="session not scored yet")
    result = await db.execute(
        select(OfficeAttempt)
        .where(OfficeAttempt.session_id == session_id)
        .order_by(OfficeAttempt.problem_index)
    )
    attempts = list(result.scalars())

    problems: list[ResultProblem] = []
    for attempt in attempts:
        problem = PROBLEMS[attempt.problem_index]
        score = attempt.score or {}
        predicted = list(attempt.last_predicted_ids or [])
        problems.append(
            ResultProblem(
                problem_index=attempt.problem_index,
                title=problem.title,
                target_entity=problem.target_entity,
                final_prompt=attempt.last_prompt or "",
                predicted_ids=predicted,
                truth_ids=sorted(problem.ground_truth_ids),
                tp=score.get("tp", 0),
                fp=score.get("fp", 0),
                fn=score.get("fn", 0),
                precision=attempt.precision or 0.0,
                recall=attempt.recall or 0.0,
                f1=attempt.f1 or 0.0,
                correct_count=score.get("correct_count", 0),
                truth_count=score.get("truth_count", len(problem.ground_truth_ids)),
            )
        )

    total_correct = sum(p.tp for p in problems)
    return ResultResponse(
        session_id=session.id,
        candidate_name=session.candidate_name,
        status=session.status,
        precision=session.precision or 0.0,
        recall=session.recall or 0.0,
        f1=session.f1 or 0.0,
        total_correct=total_correct,
        problems=problems,
    )
