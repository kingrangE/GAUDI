"""Job acceptance, worker fencing, ownership, and explicit recovery (offline)."""

import asyncio
from datetime import datetime, timedelta, timezone
from threading import Event
from types import SimpleNamespace

import pytest
from redis.exceptions import ConnectionError
from rq.exceptions import DuplicateJobError
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from feature_demo import dispatch, worker
from feature_demo.models import DemoJob, DemoSession

BODY = {
    "feature": "context_engineering",
    "action": "evaluate",
    "input": {
        "project_id": "todo-api",
        "claude_md": "`app/main.py` and `make test`",
    },
}
REPORT = {"project_id": "todo-api", "scored": True, "total": 80, "dimensions": [], "results": []}


class FakeQueue:
    def __init__(self):
        self.jobs = {}
        self.calls = []
        self.available = True

    def enqueue(self, target, native_id, **kwargs):
        if not self.available:
            raise ConnectionError("private broker error")
        self.calls.append((target, native_id, kwargs))
        if kwargs["job_id"] in self.jobs:
            raise DuplicateJobError()
        self.jobs[kwargs["job_id"]] = SimpleNamespace(get_status=lambda: "queued")

    def fetch_job(self, job_id):
        if not self.available:
            raise ConnectionError("private broker error")
        return self.jobs.get(job_id)


@pytest.fixture
def queue(monkeypatch):
    monkeypatch.setattr(get_settings(), "demo_enabled", True)
    monkeypatch.setattr(get_settings(), "demo_cookie_secure", False)
    queue = FakeQueue()
    monkeypatch.setattr(dispatch, "get_demo_queue", lambda: queue)
    return queue


async def create(client, key="request-1", body=None):
    if not client.cookies:
        assert (await client.post("/api/demo/session")).status_code == 200
    return await client.post("/api/demo/jobs", json=body or BODY, headers={"Idempotency-Key": key})


async def test_accept_preserves_input_and_exposes_only_state(client, engine, queue):
    response = await create(client)
    assert response.status_code == 202
    state = response.json()
    assert state["status"] == "queued"
    assert state["dispatch_status"] == "enqueued"
    assert state["progress_percent"] == 0
    assert response.headers["cache-control"] == "no-store"
    assert not {"payload", "input", "lease", "result", "input_hash"} & state.keys()
    async with async_sessionmaker(engine)() as db:
        saved = await db.get(DemoJob, state["job_id"])
        assert saved.payload == BODY["input"]
        assert saved.result is None
    target, native_id, options = queue.calls[0]
    assert target == "feature_demo.worker.execute"
    assert native_id == state["job_id"]
    assert options["unique"] is True
    assert options["job_timeout"] == 900
    assert (await client.get(f"/api/demo/jobs/{native_id}/result")).status_code == 409


async def test_same_key_returns_original_and_changed_input_conflicts(client, engine, queue):
    first = await create(client)
    again = await create(client)
    assert first.json()["job_id"] == again.json()["job_id"]
    changed = {**BODY, "input": {**BODY["input"], "claude_md": "new input"}}
    assert (await create(client, body=changed)).status_code == 409
    async with async_sessionmaker(engine)() as db:
        assert await db.scalar(select(func.count()).select_from(DemoJob)) == 1


async def test_other_session_cannot_poll_or_read_result_even_with_admin_token(client, queue):
    created = await create(client)
    job_id = created.json()["job_id"]
    assert (await client.get(f"/api/demo/jobs/{job_id}")).status_code == 200
    client.cookies.clear()
    await client.post("/api/demo/session")
    for suffix in ["", "/result"]:
        assert (await client.get(f"/api/demo/jobs/{job_id}{suffix}")).status_code == 404
    own = await create(client)
    assert own.json()["job_id"] != job_id


@pytest.mark.parametrize("key", ["", "bad key", "x" * 129])
async def test_invalid_key_is_rejected(client, queue, key):
    assert (await create(client, key=key)).status_code == 422
    assert not queue.calls


@pytest.mark.parametrize(
    "change",
    [
        {"feature": "arbitrary.worker"},
        {"action": "delete"},
        {"input": {"project_id": "missing", "claude_md": "x"}},
        {"input": {"project_id": "todo-api", "claude_md": "   "}},
    ],
)
async def test_invalid_work_is_not_persisted_or_dispatched(client, engine, queue, change):
    assert (await create(client, body={**BODY, **change})).status_code in {400, 422}
    assert not queue.calls
    async with async_sessionmaker(engine)() as db:
        assert await db.scalar(select(func.count()).select_from(DemoJob)) == 0


async def test_cookie_and_enabled_mode_are_required(client, queue, monkeypatch):
    response = await client.post("/api/demo/jobs", json=BODY, headers={"Idempotency-Key": "k"})
    assert response.status_code == 401
    monkeypatch.setattr(get_settings(), "demo_enabled", False)
    response = await client.post("/api/demo/jobs", json=BODY, headers={"Idempotency-Key": "k"})
    assert response.status_code == 404


async def test_redis_failure_preserves_job_and_admin_recovers_without_replacing_input(
    client, engine, queue
):
    queue.available = False
    created = await create(client)
    assert created.status_code == 202
    state = created.json()
    assert state["dispatch_status"] == "error"
    assert (await client.get(f"/api/demo/jobs/{state['job_id']}")).status_code == 200
    queue.available = True
    recovered = await client.post("/api/demo/jobs/recover")
    assert recovered.json()["dispatched"] == 1
    async with async_sessionmaker(engine)() as db:
        assert (await db.get(DemoJob, state["job_id"])).payload == BODY["input"]
    # A second recovery leaves an already delivered message in place.
    count = len(queue.calls)
    assert (await client.post("/api/demo/jobs/recover")).json()["dispatched"] == 0
    assert len(queue.calls) == count


async def test_recovery_requires_admin_and_broker_failures_are_sanitized(client, queue):
    await create(client)
    queue.available = False
    response = await client.post("/api/demo/jobs/recover")
    assert response.status_code == 503
    assert "private broker error" not in response.text
    client.headers.pop("X-Admin-Token")
    assert (await client.post("/api/demo/jobs/recover")).status_code == 401


async def test_worker_progress_and_completion_are_persisted_and_duplicates_do_not_rerun(
    client,
    engine,
    queue,
    monkeypatch,
):
    job_id = (await create(client)).json()["job_id"]
    states = []

    def evaluate(payload, progress):
        assert payload == BODY["input"]
        for event in [
            ("static_checks", 2, 4),
            ("static_checks", 2, 4),
            ("coverage", 3, 4),
            ("static_checks", 2, 4),
            ("boundary", 4, 4),
        ]:
            progress(*event)
            states.append(event)
        return REPORT

    monkeypatch.setattr(worker, "evaluate_context", evaluate)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    await worker.run_job(job_id, maker)
    await worker.run_job(job_id, maker)
    assert len(states) == 5
    result = await client.get(f"/api/demo/jobs/{job_id}/result")
    assert result.json() == REPORT
    state = (await client.get(f"/api/demo/jobs/{job_id}")).json()
    assert state["status"] == "completed"
    assert state["progress_percent"] == 100
    assert state["completed_units"] == state["total_units"] == 4
    assert state["started_at"] and state["finished_at"]
    assert not {"lease", "payload", "input_hash"} & state.keys()


@pytest.mark.parametrize(
    "bad_result",
    [
        None,
        {"invalid": "report"},
        {"project_id": "wrong-project", "scored": True},
        {"project_id": "todo-api", "scored": False},
    ],
)
async def test_invalid_report_never_reaches_completed(
    client, engine, queue, monkeypatch, bad_result
):
    job_id = (await create(client)).json()["job_id"]
    monkeypatch.setattr(worker, "evaluate_context", lambda *_: bad_result)
    await worker.run_job(job_id, async_sessionmaker(engine, expire_on_commit=False))
    state = (await client.get(f"/api/demo/jobs/{job_id}")).json()
    assert state["status"] == "failed"
    assert state["error_code"] == "evaluation_failed"
    assert state["progress_percent"] < 100
    assert (await client.get(f"/api/demo/jobs/{job_id}/result")).status_code == 409


async def test_running_progress_never_reports_100_and_failures_do_not_leak_details(
    client,
    engine,
    queue,
    monkeypatch,
):
    from feature_demo.jobs import job_state

    job_id = (await create(client)).json()["job_id"]

    def evaluate(_, progress):
        progress("boundary", 4, 4)
        raise RuntimeError("secret prompt and provider credentials")

    monkeypatch.setattr(worker, "evaluate_context", evaluate)
    await worker.run_job(job_id, async_sessionmaker(engine, expire_on_commit=False))
    async with async_sessionmaker(engine)() as db:
        job = await db.get(DemoJob, job_id)
        assert job_state(job)["progress_percent"] == 99
        assert job.result is None
    state = (await client.get(f"/api/demo/jobs/{job_id}")).json()
    assert state["status"] == "failed"
    assert "secret" not in str(state)


async def test_expired_owner_is_rejected_by_worker_before_evaluation(
    client, engine, queue, monkeypatch
):
    job_id = (await create(client)).json()["job_id"]
    async with async_sessionmaker(engine)() as db:
        await db.execute(
            update(DemoSession).values(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
        )
        await db.commit()
    monkeypatch.setattr(worker, "evaluate_context", lambda *_: pytest.fail("must not evaluate"))
    await worker.run_job(job_id, async_sessionmaker(engine, expire_on_commit=False))
    async with async_sessionmaker(engine)() as db:
        job = await db.get(DemoJob, job_id)
        assert job.status == "failed" and job.error_code == "session_expired"


@pytest.mark.parametrize("broker_status", ["failed", "stopped", "canceled", "finished"])
async def test_recovery_terminal_broker_state_marks_failed_without_reexecution(
    client,
    engine,
    queue,
    broker_status,
):
    job_id = (await create(client)).json()["job_id"]
    async with async_sessionmaker(engine)() as db:
        await db.execute(
            update(DemoJob)
            .where(DemoJob.id == job_id)
            .values(status="running", lease="old-execution")
        )
        await db.commit()
    queue.jobs[f"demo-{job_id}"] = SimpleNamespace(get_status=lambda: broker_status)
    calls = len(queue.calls)
    assert (await client.post("/api/demo/jobs/recover")).json()["failed"] == 1
    assert len(queue.calls) == calls
    assert (await client.get(f"/api/demo/jobs/{job_id}")).json()["status"] == "failed"


async def test_missing_broker_metadata_never_restarts_running_job(client, engine, queue):
    job_id = (await create(client)).json()["job_id"]
    async with async_sessionmaker(engine)() as db:
        await db.execute(update(DemoJob).where(DemoJob.id == job_id).values(status="running"))
        await db.commit()
    queue.jobs.clear()
    assert (await client.post("/api/demo/jobs/recover")).json()["unresolved"] == 1
    assert (await client.get(f"/api/demo/jobs/{job_id}")).json()["status"] == "running"


async def test_recovery_cursor_reaches_later_jobs_without_looping_on_first_batch(
    client, engine, queue
):
    native_id = (await create(client)).json()["job_id"]
    async with async_sessionmaker(engine)() as db:
        original = await db.get(DemoJob, native_id)
        for i in range(100):
            job_id = f"{i:032x}"
            db.add(
                DemoJob(
                    id=job_id,
                    session_id=original.session_id,
                    idempotency_key=f"batch-{i}",
                    feature=BODY["feature"],
                    action=BODY["action"],
                    payload=BODY["input"],
                    input_hash="0" * 64,
                )
            )
            queue.jobs[f"demo-{job_id}"] = SimpleNamespace(get_status=lambda: "queued")
        await db.commit()
    first = (await client.post("/api/demo/jobs/recover")).json()
    assert first["unresolved"] == 100
    assert first["next_cursor"] == f"{99:032x}"
    second = (await client.post(f"/api/demo/jobs/recover?after={first['next_cursor']}")).json()
    assert second["unresolved"] == 1
    assert second["next_cursor"] is None


async def test_real_context_core_runs_without_llm(client, engine, queue, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    job_id = (await create(client)).json()["job_id"]
    await worker.run_job(job_id, async_sessionmaker(engine, expire_on_commit=False))
    report = (await client.get(f"/api/demo/jobs/{job_id}/result")).json()
    assert report["scored"] is True
    assert report["project_id"] == "todo-api"
    dims = {dim["key"]: dim for dim in report["dimensions"]}
    assert dims["grounding"]["available"] is True
    assert dims["coverage"]["available"] is False


@pytest.mark.parametrize("interrupt", [False, True])
async def test_polling_is_available_while_running_and_recovery_fences_late_results(
    client,
    engine,
    queue,
    monkeypatch,
    interrupt,
):
    job_id = (await create(client)).json()["job_id"]
    entered, release = Event(), Event()

    def evaluate(_, progress):
        progress("coverage", 3, 4)
        progress("boundary", 4, 4)
        progress("static_checks", 2, 4)
        entered.set()
        assert release.wait(10)
        return REPORT

    monkeypatch.setattr(worker, "evaluate_context", evaluate)
    task = asyncio.create_task(
        worker.run_job(job_id, async_sessionmaker(engine, expire_on_commit=False))
    )
    try:
        assert await asyncio.to_thread(entered.wait, 10)
        state = (await client.get(f"/api/demo/jobs/{job_id}")).json()
        assert state["status"] == "running"
        assert state["phase"] == "boundary"
        assert state["completed_units"] == 4
        assert state["progress_percent"] == 99
        assert (await client.get(f"/api/demo/jobs/{job_id}/result")).status_code == 409
        if interrupt:
            queue.jobs[f"demo-{job_id}"] = SimpleNamespace(get_status=lambda: "failed")
            assert (await client.post("/api/demo/jobs/recover")).json()["failed"] == 1
    finally:
        release.set()
        await task
    state = (await client.get(f"/api/demo/jobs/{job_id}")).json()
    assert state["status"] == ("failed" if interrupt else "completed")
    assert state["progress_percent"] == (99 if interrupt else 100)
