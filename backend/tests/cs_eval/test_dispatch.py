"""Async grading dispatch: rq enqueue, worker bridge, and the failure path."""

from types import SimpleNamespace

from app.features.cs_eval import grading, tasks, worker
from app.features.cs_eval.models import CsAnswer, CsSession


async def test_rq_mode_enqueues_the_job(monkeypatch):
    calls = []

    class FakeQueue:
        def enqueue(self, func_path, *args):
            calls.append((func_path, args))

    import app.queue as queue_mod

    monkeypatch.setattr(queue_mod, "get_queue", lambda: FakeQueue())
    monkeypatch.setattr(tasks, "get_settings", lambda: SimpleNamespace(grading_mode="rq"))

    # rq path never touches the DB, so db=None is fine.
    await tasks.enqueue_grading(db=None, session_id="sess-1")

    assert calls == [("app.features.cs_eval.worker.grade_session", ("sess-1",))]


def test_worker_bridges_to_grading(monkeypatch):
    captured = {}

    async def fake_grade(db, session_id):
        captured["session_id"] = session_id

    monkeypatch.setattr(grading, "grade_session", fake_grade)
    worker.grade_session("abc")
    assert captured["session_id"] == "abc"


async def test_grade_session_failure_marks_failed(cs_db, monkeypatch):
    async with cs_db() as db:
        session = CsSession(candidate_id="c")
        db.add(session)
        await db.flush()
        db.add(
            CsAnswer(
                session_id=session.id,
                question_id="ds-hashmap",
                answer_text="x",
                ordinal=0,
            )
        )
        await db.commit()
        session_id = session.id

    async def boom(**_kwargs):
        raise RuntimeError("llm down")

    monkeypatch.setattr(grading, "judge_answer", boom)

    async with cs_db() as db:
        await grading.grade_session(db, session_id)

    async with cs_db() as db:
        graded = await db.get(CsSession, session_id)
        assert graded.status == "failed"
        assert "llm down" in graded.error
