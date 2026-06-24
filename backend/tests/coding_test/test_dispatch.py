"""Grading dispatch seam: rq-mode enqueues (no broker) and the worker bridge."""

import app.queue as queue_mod
from app.core.config import get_settings
from app.features.coding_test import grading, tasks, worker


async def test_rq_mode_enqueues_and_skips_inline(monkeypatch):
    monkeypatch.setattr(get_settings(), "grading_mode", "rq")

    enqueued = []

    class FakeQueue:
        def enqueue(self, func_path, *args):
            enqueued.append((func_path, args))

    monkeypatch.setattr(queue_mod, "get_queue", lambda: FakeQueue())

    async def fail_inline(*_a, **_k):
        raise AssertionError("inline grading must not run in rq mode")

    monkeypatch.setattr(grading, "grade_submission", fail_inline)

    await tasks.enqueue_grading(db=None, submission_id="sub-1", runner=None)

    assert enqueued == [
        ("app.features.coding_test.worker.grade_submission", ("sub-1",))
    ]


async def test_inline_mode_runs_grading(monkeypatch):
    monkeypatch.setattr(get_settings(), "grading_mode", "inline")
    seen = {}

    async def fake_grade(db, submission_id, runner):
        seen["id"] = submission_id

    monkeypatch.setattr(grading, "grade_submission", fake_grade)
    await tasks.enqueue_grading(db="DB", submission_id="sub-2", runner="R")
    assert seen["id"] == "sub-2"


def test_worker_bridge_opens_session_and_grades(monkeypatch):
    seen = {}

    async def fake_grade(db, submission_id, runner):
        seen["id"] = submission_id
        seen["db"] = db

    class FakeSession:
        async def __aenter__(self):
            return "DB"

        async def __aexit__(self, *_a):
            return False

    monkeypatch.setattr(grading, "grade_submission", fake_grade)
    monkeypatch.setattr(worker, "AsyncSessionLocal", lambda: FakeSession())

    worker.grade_submission("sub-3")  # sync RQ entry point drives asyncio.run

    assert seen == {"id": "sub-3", "db": "DB"}
