"""Deadline, immutable inputs/results, recoverable grading and concurrent requests."""

import asyncio
import time
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.features.mock_exam import exam_router, service
from app.features.mock_exam.models import ExamAttempt, ExamSubmission
from app.main import app


@pytest.fixture(autouse=True)
def offline_solver():
    app.dependency_overrides[exam_router.get_solver_client] = lambda: object()
    app.dependency_overrides[exam_router.get_context_client] = lambda: None
    yield
    app.dependency_overrides.pop(exam_router.get_solver_client, None)
    app.dependency_overrides.pop(exam_router.get_context_client, None)


async def start(client):
    result = await client.post("/api/mock-exam/start", json={"candidate_code": "AY-7F3K9Q"})
    return result.json()["attempt_id"]


async def expire(engine, aid):
    async with async_sessionmaker(engine, expire_on_commit=False)() as db:
        a = await db.get(ExamAttempt, aid)
        a.started_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await db.commit()


async def test_expired_exam_rejects_new_submission_and_generation(client, engine):
    aid = await start(client)
    await expire(engine, aid)
    root = f"/api/mock-exam/attempts/{aid}"
    assert (
        await client.post(root + "/steps/context_engineering/submit", json={"claude_md": "answer"})
    ).status_code == 409
    assert (
        await client.post(root + "/steps/rejection_eval/generate", json={"prompt": "design"})
    ).status_code == 409
    async with async_sessionmaker(engine)() as db:
        assert await db.scalar(select(ExamSubmission.id)) is None


async def test_failure_preserves_answer_and_retry_after_deadline(client, engine, monkeypatch):
    aid = await start(client)
    root = f"/api/mock-exam/attempts/{aid}"
    inputs = []

    async def failing(feature, db, attempt, body, *args):
        inputs.append(body.claude_md)
        raise RuntimeError("provider failed")

    monkeypatch.setattr(exam_router, "_score_step", failing)
    response = await client.post(
        root + "/steps/context_engineering/submit", json={"claude_md": "saved"}
    )
    assert response.status_code == 503
    async with async_sessionmaker(engine)() as db:
        saved = await db.scalar(select(ExamSubmission))
        assert saved.payload["claude_md"] == "saved"
        assert saved.status == "failed"
    state = (await client.get(root)).json()
    assert state["submissions"]["context_engineering"] == "failed"
    assert (await client.post(root + "/finish")).status_code == 409
    changed = await client.post(
        root + "/steps/context_engineering/submit", json={"claude_md": "changed"}
    )
    assert changed.status_code == 409
    await expire(engine, aid)

    async def success(feature, db, attempt, body, *args):
        inputs.append(body.claude_md)
        return {"total": 100}

    monkeypatch.setattr(exam_router, "_score_step", success)
    assert (await client.post(root + "/steps/context_engineering/retry")).status_code == 200
    assert inputs == ["saved", "saved"]
    assert (await client.post(root + "/finish")).status_code == 200
    async with async_sessionmaker(engine)() as db:
        a = await db.get(ExamAttempt, aid)
        assert a.overall_normalized == 20


async def test_completed_exam_is_immutable_and_finish_is_idempotent(client, engine, monkeypatch):
    aid = await start(client)
    root = f"/api/mock-exam/attempts/{aid}"

    async def score(*args):
        return {"total": 100}

    monkeypatch.setattr(exam_router, "_score_step", score)
    body = {"claude_md": "answer"}
    for _ in range(2):
        assert (
            await client.post(root + "/steps/context_engineering/submit", json=body)
        ).status_code == 200
    assert (await client.post(root + "/finish")).status_code == 200
    async with async_sessionmaker(engine)() as db:
        original = await db.get(ExamAttempt, aid)
        stamp = original.completed_at
    for path, payload in [
        ("/steps/context_engineering/submit", body),
        ("/steps/rejection_eval/generate", {"prompt": "new"}),
    ]:
        assert (await client.post(root + path, json=payload)).status_code == 409
    assert (await client.post(root + "/steps/context_engineering/retry")).status_code == 409
    assert (await client.post(root + "/finish")).status_code == 200
    async with async_sessionmaker(engine)() as db:
        a = await db.get(ExamAttempt, aid)
        assert a.completed_at == stamp
        with pytest.raises(ValueError, match="completed"):
            await service.record_feature_result(db, aid, "context_engineering", {"total": 20})


async def test_empty_exam_scores_zero(client, engine):
    aid = await start(client)
    assert (await client.post(f"/api/mock-exam/attempts/{aid}/finish")).status_code == 200
    async with async_sessionmaker(engine)() as db:
        assert (await db.get(ExamAttempt, aid)).overall_normalized == 0


async def test_slow_context_grading_does_not_block_health_or_allow_finish(client, monkeypatch):
    aid = await start(client)
    other = await start(client)
    entered = asyncio.Event()
    loop = asyncio.get_running_loop()

    def slow(*args):
        loop.call_soon_threadsafe(entered.set)
        time.sleep(0.3)
        return {"total": 80}

    monkeypatch.setattr(exam_router, "_score_context", slow)
    task = asyncio.create_task(
        client.post(
            f"/api/mock-exam/attempts/{aid}/steps/context_engineering/submit",
            json={"claude_md": "saved"},
        )
    )
    await asyncio.wait_for(entered.wait(), 1)
    try:
        await asyncio.wait_for(client.get("/health"), 0.15)
        state = await asyncio.wait_for(client.get(f"/api/mock-exam/attempts/{other}"), 0.15)
        assert state.status_code == 200
        assert not task.done()
        finish = await client.post(f"/api/mock-exam/attempts/{aid}/finish")
        assert finish.status_code == 409
    finally:
        assert (await task).status_code == 200


async def test_saved_dev_turns_are_reused_and_final_submission_does_not_generate(
    client, monkeypatch
):
    from feature_dev_prompting import sessions
    from feature_dev_prompting.models import CaseResult, TurnResult

    seen = []

    def execute(problem, turns, prompt, solver):
        seen.append((list(turns), prompt))
        number = len(turns) + 1
        return TurnResult(
            turn=number,
            prompt=prompt,
            code=f"def solution(): return {number}",
            passed_count=number,
            total=2,
            solved=number == 2,
            feedback="hidden feedback",
            case_results=[
                CaseResult(
                    index=0, hidden=False, passed=True, status="pass", expected="1", got="1"
                ),
                CaseResult(
                    index=1,
                    hidden=True,
                    passed=number == 2,
                    status="pass" if number == 2 else "wrong_answer",
                ),
            ],
        )

    monkeypatch.setattr(sessions, "execute_turn", execute)
    aid = await start(client)
    root = f"/api/mock-exam/attempts/{aid}"
    first = await client.post(root + "/dev-run", json={"prompt": "first", "turn": 1})
    assert first.status_code == 200
    public = first.json()
    assert "score" not in public
    assert set(public["turns"][0]) == {"turn", "prompt", "code", "case_results"}
    assert all(not c["hidden"] for c in public["turns"][0]["case_results"])
    assert len(seen) == 1
    duplicate = await client.post(root + "/dev-run", json={"prompt": "first", "turn": 1})
    assert duplicate.json() == public
    assert len(seen) == 1
    other = await start(client)
    denied = await client.post(
        f"/api/mock-exam/attempts/{other}/steps/dev_prompting/submit", json={"prompts": ["first"]}
    )
    assert denied.status_code in (409, 503)
    practice = await client.post(
        f"/dev-prompting/runs/{public['run_id']}/turns", json={"prompt": "steal", "turn": 2}
    )
    assert practice.status_code == 404
    second = await client.post(root + "/dev-run", json={"prompt": "second", "turn": 2})
    assert second.status_code == 200
    assert seen[1][0][0]["code"] == first.json()["turns"][0]["code"]
    restored = (await client.get(root + "/dev-run")).json()
    assert restored["turns"] == second.json()["turns"]
    final = await client.post(
        root + "/steps/dev_prompting/submit", json={"prompts": ["first", "second"]}
    )
    assert final.status_code == 200
    assert len(seen) == 2
    detail = (await client.get(f"/api/admin/exam-results/{aid}")).json()
    raw = detail["features"][0]["raw_result"]
    assert raw["turns"][-1]["code"] == second.json()["turns"][-1]["code"]
    assert raw["score"]["total"] == 94.0
    assert (
        await client.post(root + "/dev-run", json={"prompt": "third", "turn": 3})
    ).status_code == 409





@pytest.mark.parametrize("seconds_left,expected", [(0.1, 1), (0.0, 0), (-0.1, 0)])
def test_deadline_boundary(seconds_left, expected, monkeypatch):
    fixed = datetime(2026, 11, 3, tzinfo=timezone.utc)

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(exam_router, "datetime", Clock)
    attempt = ExamAttempt(started_at=fixed - timedelta(seconds=3600 - seconds_left))
    assert exam_router._remaining_seconds(attempt) == expected


async def test_dev_prompt_recovery_and_confirmation_after_deadline(client, engine, monkeypatch):
    from feature_dev_prompting import sessions
    from feature_dev_prompting.models import TurnResult

    aid = await start(client)
    root = f"/api/mock-exam/attempts/{aid}"

    def fail(*args):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(sessions, "execute_turn", fail)
    assert (
        await client.post(root + "/dev-run", json={"prompt": "saved", "turn": 1})
    ).status_code == 503
    await expire(engine, aid)
    assert (
        await client.post(root + "/dev-run", json={"prompt": "new", "turn": 1})
    ).status_code == 409

    def succeed(problem, turns, prompt, solver):
        return TurnResult(
            turn=1,
            prompt=prompt,
            code="def solution(): return 1",
            passed_count=1,
            total=1,
            solved=True,
            feedback="",
            case_results=[],
        )

    monkeypatch.setattr(sessions, "execute_turn", succeed)
    retry = await client.post(root + "/dev-run", json={"prompt": "saved", "turn": 1})
    assert retry.status_code == 200
    assert (
        await client.post(root + "/steps/dev_prompting/submit", json={"prompts": ["saved"]})
    ).status_code == 200
    assert (await client.post(root + "/finish")).status_code == 200


async def test_reclaimed_grading_cannot_overwrite_new_result(client, engine, monkeypatch):
    from sqlalchemy import update

    aid = await start(client)
    root = f"/api/mock-exam/attempts/{aid}"
    entered, release = asyncio.Event(), asyncio.Event()
    calls = 0

    async def score(*args):
        nonlocal calls
        calls += 1
        if calls == 1:
            entered.set()
            await release.wait()
            return {"total": 100}
        return {"total": 20}

    monkeypatch.setattr(exam_router, "_score_step", score)
    original = asyncio.create_task(
        client.post(root + "/steps/context_engineering/submit", json={"claude_md": "saved"})
    )
    await asyncio.wait_for(entered.wait(), 1)
    try:
        async with async_sessionmaker(engine)() as db:
            await db.execute(
                update(ExamSubmission)
                .where(ExamSubmission.exam_attempt_id == aid)
                .values(updated_at=datetime.now(timezone.utc) - timedelta(minutes=16))
            )
            await db.commit()
        assert (await client.post(root + "/steps/context_engineering/retry")).status_code == 200
    finally:
        release.set()
        assert (await original).status_code == 503
    detail = (await client.get(f"/api/admin/exam-results/{aid}")).json()
    assert detail["features"][0]["normalized_score"] == 20
    assert detail["submissions"][0]["status"] == "graded"


async def test_finish_refreshes_cached_status_before_locking(engine):
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as first, maker() as second:
        attempt = await service.create_exam_attempt(first, "AY-7F3K9Q")
        cached = await second.get(ExamAttempt, attempt.id)
        assert cached.status == "in_progress"
        completed = await service.finalize_exam_attempt(first, attempt.id)
        await second.commit()
        again = await service.finalize_exam_attempt(second, attempt.id)
        assert again is cached
        assert again.completed_at.replace(tzinfo=None) == completed.completed_at.replace(
            tzinfo=None
        )
