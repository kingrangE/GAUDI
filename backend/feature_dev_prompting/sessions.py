"""Persist each generated turn once, then grade exactly the code the user saw."""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import JSON, DateTime, ForeignKey, String, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from feature_demo.execution import advance_sync
from feature_dev_prompting.evaluator import build_feedback
from feature_dev_prompting.grader import evaluation_score, summarize_run
from feature_dev_prompting.models import TurnResult
from feature_dev_prompting.problems import get_problem
from feature_dev_prompting.sandbox import run_against_tests
from feature_dev_prompting.solver import generate_code


class DevRun(Base):
    __tablename__ = "dev_prompting_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    exam_attempt_id: Mapped[str | None] = mapped_column(
        String(32),
        ForeignKey("exam_attempts.id"),
        unique=True,
        nullable=True,
    )
    problem_id: Mapped[str] = mapped_column(String(80))
    turns: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="idle")
    pending_prompt: Mapped[str | None] = mapped_column(String(20000), nullable=True)
    lease: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


def result(run: DevRun) -> dict:
    turns = [TurnResult.model_validate(t) for t in run.turns]
    score = evaluation_score(turns)
    return {
        "run_id": run.id,
        "problem_id": run.problem_id,
        "solved": score.solved,
        "score": score.model_dump(),
        "turns": run.turns,
        "pending_prompt": run.pending_prompt,
        "status": run.status,
    }


def public_result(run: DevRun, through: int | None = None) -> dict:
    # Only public examples reach the exam client; hidden feedback remains server-side.
    turns = []
    for turn in run.turns[:through]:
        public_cases = [c for c in turn["case_results"] if not c["hidden"]]
        turns.append(
            {
                "turn": turn["turn"],
                "prompt": turn["prompt"],
                "code": turn["code"],
                "case_results": public_cases,
            }
        )
    return {
        "run_id": run.id,
        "problem_id": run.problem_id,
        "turns": turns,
        "pending_prompt": run.pending_prompt,
        "status": run.status,
    }


def execute_turn(problem, turns: list[dict], prompt: str, client) -> TurnResult:
    previous = turns[-1] if turns else None
    code = generate_code(
        client,
        problem,
        prompt,
        previous["code"] if previous else problem.starter_code,
        previous["feedback"] if previous else None,
    )
    advance_sync("generating_code", 1, 2)
    cases = run_against_tests(
        code, problem.tests, problem.entry_point, time_limit=problem.time_limit_sec
    )
    advance_sync("testing_turn", 2, 2)
    passed, total = summarize_run(cases)
    return TurnResult(
        turn=len(turns) + 1,
        prompt=prompt,
        code=code,
        passed_count=passed,
        total=total,
        solved=total > 0 and passed == total,
        feedback=build_feedback(cases),
        case_results=cases,
    )


async def run_turn(db: AsyncSession, run: DevRun, prompt: str, turn: int, client) -> None:
    if turn <= len(run.turns):
        if run.turns[turn - 1]["prompt"] != prompt:
            raise HTTPException(status_code=409, detail="turn input is immutable")
        return
    if turn != len(run.turns) + 1:
        raise HTTPException(status_code=409, detail="reload the saved run before the next turn")
    if run.pending_prompt is not None and run.pending_prompt != prompt:
        raise HTTPException(status_code=409, detail="retry the pending prompt first")
    now, lease = datetime.now(timezone.utc), uuid4().hex
    claimed = await db.execute(
        update(DevRun)
        .execution_options(synchronize_session="fetch")
        .where(
            DevRun.id == run.id,
            func.json_array_length(DevRun.turns) == turn - 1,
            or_(DevRun.pending_prompt.is_(None), DevRun.pending_prompt == prompt),
            or_(DevRun.status != "running", DevRun.updated_at < now - timedelta(minutes=15)),
        )
        .values(status="running", pending_prompt=prompt, lease=lease, updated_at=now)
    )
    await db.commit()
    if claimed.rowcount != 1:
        raise HTTPException(status_code=409, detail="turn generation is already in progress")
    run_id = run.id
    try:
        generated = await asyncio.to_thread(
            execute_turn, get_problem(run.problem_id), run.turns, prompt, client
        )
    except Exception as exc:
        await db.rollback()
        await db.execute(
            update(DevRun)
            .execution_options(synchronize_session="fetch")
            .where(DevRun.id == run_id, DevRun.lease == lease)
            .values(
                status="failed",
                updated_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()
        raise HTTPException(status_code=503, detail="prompt saved; retry the same turn") from exc
    written = await db.execute(
        update(DevRun)
        .execution_options(synchronize_session="fetch")
        .where(DevRun.id == run_id, DevRun.lease == lease)
        .values(
            turns=[*run.turns, generated.model_dump()],
            status="idle",
            pending_prompt=None,
            updated_at=datetime.now(timezone.utc),
        )
    )
    await db.commit()
    if written.rowcount != 1:
        raise HTTPException(status_code=409, detail="turn was reclaimed; reload the saved run")
    await db.refresh(run)
