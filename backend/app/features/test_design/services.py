"""Orchestration for the test-design evaluation.

Ties the pieces together: serve public problems, score a submission (LLM judge
-> deterministic scoring -> persist), and build a candidate's result. The LLM
call is isolated in ``judging.judge_submission`` so unit tests can mock it.
"""

from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.test_design import scoring
from app.features.test_design.judging import judge_submission
from app.features.test_design.models import TestDesignSession, TestDesignSubmission
from app.features.test_design.problems import PROBLEM_COUNT, PROBLEMS, get_problem
from app.features.test_design.schemas import (
    CreateSessionResponse,
    ProblemPublic,
    ResultFlaw,
    ResultProblem,
    ResultResponse,
)


class SessionNotFound(Exception):
    """Raised when a session id does not exist."""


def public_problems() -> list[ProblemPublic]:
    """The problems as shown to candidates — answer sets are never included."""
    return [
        ProblemPublic(
            index=i,
            id=p.id,
            title=p.title,
            difficulty=p.difficulty,
            spec=p.spec,
            provided_tests=list(p.provided_tests),
        )
        for i, p in enumerate(PROBLEMS)
    ]


async def create_session(db: AsyncSession, candidate_name: str) -> CreateSessionResponse:
    session = TestDesignSession(candidate_name=candidate_name)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return CreateSessionResponse(
        session_id=session.id,
        candidate_name=session.candidate_name,
        problems=public_problems(),
    )


async def _get_session(db: AsyncSession, session_id: str) -> TestDesignSession:
    session = await db.get(TestDesignSession, session_id)
    if session is None:
        raise SessionNotFound(session_id)
    return session


async def submit_problem(
    db: AsyncSession, session_id: str, problem_index: int, flaws: list[str]
) -> TestDesignSubmission:
    """Judge + score one problem submission and persist it (idempotent per problem)."""
    await _get_session(db, session_id)
    if not 0 <= problem_index < PROBLEM_COUNT:
        raise IndexError(problem_index)
    problem = get_problem(problem_index)

    judged = await judge_submission(problem, flaws)
    gt_flaws = [asdict(f) for f in problem.flaws]
    matches = [m.model_dump() for m in judged.matches]
    score = scoring.score_submission(
        gt_flaws,
        flaws,
        matches,
        report=judged.report,
        already_covered_indices=judged.already_covered_indices,
    )

    existing = (
        await db.execute(
            select(TestDesignSubmission).where(
                TestDesignSubmission.session_id == session_id,
                TestDesignSubmission.problem_index == problem_index,
            )
        )
    ).scalar_one_or_none()

    submission = existing or TestDesignSubmission(
        session_id=session_id, problem_index=problem_index
    )
    submission.problem_id = problem.id
    submission.candidate_flaws = list(flaws)
    submission.judge_result = score
    submission.recall = score["recall"]
    submission.precision = score["precision"]
    submission.mean_quality = score["mean_quality"]
    submission.weighted_score = score["weighted_score"]
    if existing is None:
        db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


async def build_result(db: AsyncSession, session_id: str) -> ResultResponse:
    session = await _get_session(db, session_id)
    submissions = list(
        (
            await db.execute(
                select(TestDesignSubmission)
                .where(TestDesignSubmission.session_id == session_id)
                .order_by(TestDesignSubmission.problem_index)
            )
        )
        .scalars()
        .all()
    )

    result_problems: list[ResultProblem] = []
    for sub in submissions:
        score = sub.judge_result or {}
        result_problems.append(
            ResultProblem(
                problem_index=sub.problem_index,
                problem_id=sub.problem_id,
                title=PROBLEMS[sub.problem_index].title,
                difficulty=PROBLEMS[sub.problem_index].difficulty,
                provided_tests=list(PROBLEMS[sub.problem_index].provided_tests),
                candidate_flaws=sub.candidate_flaws or [],
                flaws=[ResultFlaw(**f) for f in score.get("flaws", [])],
                false_positives=score.get("false_positives", []),
                recall=score.get("recall", 0.0),
                precision=score.get("precision", 0.0),
                mean_quality=score.get("mean_quality", 0.0),
                weighted_score=score.get("weighted_score", 0.0),
                report=score.get("report", ""),
            )
        )

    recall, precision, weighted = scoring.aggregate(
        [s.judge_result for s in submissions if s.judge_result]
    )
    status = "completed" if len(submissions) >= PROBLEM_COUNT else "in_progress"

    # persist the rolled-up session metrics
    session.recall = recall
    session.precision = precision
    session.weighted_score = weighted
    session.status = status
    await db.commit()

    return ResultResponse(
        session_id=session.id,
        candidate_name=session.candidate_name,
        status=status,
        recall=recall,
        precision=precision,
        weighted_score=weighted,
        problems=result_problems,
    )
