"""No paid calls: policy accounting, isolation, exhaustion and process fencing."""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.requests import Request

from app.core.config import get_settings
from feature_demo import dispatch, limits, meter, slots, worker
from feature_demo.execution import Execution, execution
from feature_demo.models import DemoAttempt, DemoBudget, DemoCall, DemoJob, DemoSlot

BODY = {
    "feature": "context_engineering",
    "action": "evaluate",
    "input": {"project_id": "todo-api", "claude_md": "`app/main.py` and `make test`"},
}


@pytest.fixture(autouse=True)
def policy(monkeypatch):
    cfg = get_settings()
    for key, value in {
        "demo_enabled": True,
        "demo_limits_enabled": True,
        "demo_cookie_secure": False,
        "demo_daily_budget_usd": Decimal("1000"),
        "demo_model_prices": {
            model: {"input": Decimal("1"), "output": Decimal("2")}
            for model in {cfg.llm_model, cfg.solver_model, cfg.spec_gen_model, cfg.spec_judge_model}
        },
    }.items():
        monkeypatch.setattr(cfg, key, value)
    monkeypatch.setattr(dispatch, "enqueue", lambda *args: None)
    monkeypatch.setattr(dispatch, "get_demo_queue", lambda: None)
    return cfg


async def submit(client, key="one", body=None):
    if not client.cookies:
        assert (await client.post("/api/demo/session")).status_code == 200
    return await client.post("/api/demo/jobs", json=body or BODY, headers={"Idempotency-Key": key})


async def test_optional_browsing_and_completed_replay_do_not_spend(client, engine, monkeypatch):
    assert (await client.get("/dev-prompting/problems")).status_code == 200
    info = await client.post("/api/demo/session")
    usage = (await client.get("/api/demo/usage")).json()
    assert len(usage["features"]) == 9
    assert all(item["remaining"] == 1 for item in usage["features"])
    async with async_sessionmaker(engine)() as db:
        assert await db.scalar(select(func.count()).select_from(DemoAttempt)) == 0
    accepted = await submit(client)
    assert accepted.status_code == 202
    job_id = accepted.json()["job_id"]
    monkeypatch.setattr(
        worker, "evaluate_context", lambda *args: {"project_id": "todo-api", "scored": True}
    )
    await worker.run_job(job_id, async_sessionmaker(engine, expire_on_commit=False))
    assert (await submit(client, "duplicate")).json()["job_id"] == job_id
    changed = {**BODY, "input": {**BODY["input"], "claude_md": "different"}}
    assert (await submit(client, "changed", changed)).status_code == 409
    async with async_sessionmaker(engine)() as db:
        attempt = await db.scalar(select(DemoAttempt))
        budget = await db.get(DemoBudget, "global")
        assert attempt.closed and budget.reserved == budget.spent == budget.inflight == 0
        assert attempt.session_id == info.json()["session_id"]
    usage = (await client.get("/api/demo/usage")).json()["features"]
    assert next(i for i in usage if i["feature"] == "context_engineering")["remaining"] == 0
    assert next(i for i in usage if i["feature"] == "spec_design")["remaining"] == 1
    client.cookies.clear()
    await client.post("/api/demo/session")
    assert all(
        item["remaining"] == 1 for item in (await client.get("/api/demo/usage")).json()["features"]
    )


@pytest.mark.parametrize("change,status", [("budget", 429), ("unset", 503), ("price", 503)])
async def test_admission_fails_closed_without_reserving(
    client, engine, policy, monkeypatch, change, status
):
    if change == "price":
        monkeypatch.setattr(policy, "demo_model_prices", {})
    else:
        monkeypatch.setattr(
            policy,
            "demo_daily_budget_usd",
            Decimal("0.00001") if change == "budget" else Decimal(0),
        )
    assert (await submit(client)).status_code == status
    async with async_sessionmaker(engine)() as db:
        assert await db.scalar(select(func.count()).select_from(DemoAttempt)) == 0
        assert await db.scalar(select(func.count()).select_from(DemoJob)) == 0


async def test_queue_cap_does_not_consume_second_feature(client, engine, policy, monkeypatch):
    monkeypatch.setattr(policy, "demo_max_session_jobs", 1)
    assert (await submit(client)).status_code == 202
    # Queue check applies even to cheap create-run operations.
    body = {
        "feature": "dev_prompting",
        "action": "create_run",
        "input": {"body": {"problem_id": "idempotent-sum"}},
    }
    assert (await submit(client, "two", body)).status_code == 429
    async with async_sessionmaker(engine)() as db:
        assert await db.scalar(select(func.count()).select_from(DemoAttempt)) == 1


async def test_failed_step_retries_are_bounded_and_input_is_fixed(client, engine):
    maker = async_sessionmaker(engine, expire_on_commit=False)
    first = (await submit(client)).json()["job_id"]
    async with maker() as db:
        (await db.get(DemoJob, first)).status = "failed"
        await db.commit()
    second = await submit(client, "retry")
    assert second.status_code == 202 and second.json()["job_id"] != first
    async with maker() as db:
        (await db.get(DemoJob, second.json()["job_id"])).status = "failed"
        await db.commit()
    assert (await submit(client, "third")).status_code == 429
    async with maker() as db:
        assert await db.scalar(select(func.count()).select_from(DemoAttempt)) == 1


async def test_issuance_limit_ignores_untrusted_forwarded_ip_and_allows_renewal(
    client, policy, monkeypatch
):
    monkeypatch.setattr(policy, "demo_session_issues_per_hour", 1)
    assert (await client.post("/api/demo/session")).status_code == 200
    assert (await client.post("/api/demo/session")).status_code == 200
    client.cookies.clear()
    assert (
        await client.post("/api/demo/session", headers={"X-Forwarded-For": "9.8.7.6"})
    ).status_code == 429


def test_only_explicit_proxy_networks_can_supply_client_ip(policy, monkeypatch):
    from feature_demo.issuance import client_address

    request = Request(
        {
            "type": "http",
            "client": ("127.0.0.1", 50),
            "headers": [(b"x-forwarded-for", b"1.2.3.4, 10.0.0.4")],
        }
    )
    assert client_address(request) == "127.0.0.1"
    monkeypatch.setattr(policy, "demo_trusted_proxies", "127.0.0.1/32,10.0.0.0/8")
    assert client_address(request) == "1.2.3.4"


async def activate(client, engine):
    job_id = (await submit(client)).json()["job_id"]
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        job = await db.get(DemoJob, job_id)
        job.status, job.lease = "running", "lease"
        owner = job.session_id
        await db.commit()

    async def progress(*args):
        pass

    token = execution.set(
        Execution(
            owner,
            maker,
            datetime.now(timezone.utc),
            asyncio.get_running_loop(),
            progress,
            job_id,
            "lease",
        )
    )
    return maker, token, job_id


@pytest.mark.parametrize("known", [True, False])
async def test_usage_settles_once_and_unknown_usage_keeps_upper_charge(
    client, engine, policy, known
):
    maker, token, _ = await activate(client, engine)
    try:
        call_id = await meter.reserve(policy.llm_model, [{"content": "hello"}], None, 100)
        async with maker() as db:
            initial = await db.get(DemoCall, call_id)
            upper = initial.reserved
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=20) if known else None
        await meter.settle(call_id, usage, 100)
        await meter.settle(call_id, usage, 100)
        async with maker() as db:
            call = await db.get(DemoCall, call_id)
            budget = await db.get(DemoBudget, "global")
            assert budget.inflight == 0
            assert call.charged == budget.spent == (50_000 if known else upper)
            assert call.state == ("settled" if known else "unknown")
    finally:
        execution.reset(token)


async def test_meter_rejects_no_lease_oversize_and_exhausted_calls(client, engine, policy):
    with pytest.raises(HTTPException) as error:
        await meter.reserve(policy.llm_model, [], None, 10)
    assert error.value.status_code == 403
    maker, token, _ = await activate(client, engine)
    try:
        with pytest.raises(HTTPException) as error:
            await meter.reserve(policy.llm_model, [{"content": "x" * 70000}], None, 10)
        assert error.value.status_code == 413
        async with maker() as db:
            attempt = await db.scalar(select(DemoAttempt))
            attempt.calls = attempt.max_calls
            await db.commit()
        with pytest.raises(HTTPException) as error:
            await meter.reserve(policy.llm_model, [], None, 10)
        assert error.value.status_code == 429
    finally:
        execution.reset(token)


async def test_day_rollover_retains_reservations_and_inflight(engine):
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        db.add(DemoBudget(id="global", day="2000-01-01", reserved=100, inflight=40, spent=60))
        await db.commit()
        budget = await limits.gate(db)
        assert (budget.reserved, budget.inflight, budget.spent) == (100, 40, 0)


async def test_global_slot_waits_for_release_and_old_lease_cannot_release(client, engine):
    maker, token, job_id = await activate(client, engine)
    execution.reset(token)
    first = await slots.acquire(maker, "evaluation", job_id, "first")
    waiting = asyncio.create_task(slots.acquire(maker, "evaluation", job_id, "second"))
    await asyncio.sleep(0.2)
    assert not waiting.done()
    await slots.release(maker, "evaluation", first, "stale")
    await asyncio.sleep(0.15)
    assert not waiting.done()
    await slots.release(maker, "evaluation", first, "first")
    second = await asyncio.wait_for(waiting, 2)
    await slots.release(maker, "evaluation", second, "second")


async def test_recovery_refuses_live_pid_and_charges_dead_unknown_calls(
    client, engine, monkeypatch, policy
):
    maker, token, job_id = await activate(client, engine)
    try:
        call_id = await meter.reserve(policy.llm_model, [], None, 100)
        await slots.acquire(maker, "evaluation", job_id, "lease")
        async with maker() as db:
            assert (await slots.recover_slots(db))["slots_unresolved"] == 1
        monkeypatch.setattr(slots, "dead_local_process", lambda slot: True)
        async with maker() as db:
            assert (await slots.recover_slots(db))["slots_released"] == 1
        async with maker() as db:
            call = await db.get(DemoCall, call_id)
            assert call.state == "unknown" and call.charged == call.reserved
            assert (await db.get(DemoJob, job_id)).status == "failed"
            assert (await db.get(DemoBudget, "global")).inflight == 0
    finally:
        execution.reset(token)


async def test_dead_sandbox_slot_requires_confirmed_cleanup(client, engine, monkeypatch):
    maker, token, job_id = await activate(client, engine)
    execution.reset(token)
    await slots.acquire(maker, "sandbox", job_id, "sandbox-lease", "gaudi-sandbox-test")
    monkeypatch.setattr(slots, "dead_local_process", lambda slot: True)
    monkeypatch.setattr(slots.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=1))
    async with maker() as db:
        assert (await slots.recover_slots(db))["slots_unresolved"] == 1
    monkeypatch.setattr(
        slots.subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(returncode=0, stdout="gaudi-sandbox-test\n"),
    )
    async with maker() as db:
        assert (await slots.recover_slots(db))["slots_released"] == 1


async def test_cheap_creation_does_not_reserve_and_turns_share_one_attempt(
    client, engine, monkeypatch
):
    from feature_dev_prompting.problems import list_problems

    problem = list_problems()[0].id
    maker = async_sessionmaker(engine, expire_on_commit=False)
    create_body = {
        "feature": "dev_prompting",
        "action": "create_run",
        "input": {"body": {"problem_id": problem}},
    }
    created = (await submit(client, "create", create_body)).json()["job_id"]
    await worker.run_job(created, maker)
    async with maker() as db:
        job = await db.get(DemoJob, created)
        run_id = job.result["body"]["run_id"]
        assert await db.scalar(select(func.count()).select_from(DemoAttempt)) == 0
    for turn in [1, 2]:
        body = {
            "feature": "dev_prompting",
            "action": "next_turn",
            "input": {
                "params": {"run_id": run_id},
                "body": {"prompt": f"turn {turn}", "turn": turn},
            },
        }
        response = await submit(client, f"turn-{turn}", body)
        assert response.status_code == 202
        async with maker() as db:
            (await db.get(DemoJob, response.json()["job_id"])).status = "completed"
            await db.commit()
    async with maker() as db:
        assert await db.scalar(select(func.count()).select_from(DemoAttempt)) == 1


async def test_expired_idle_attempt_releases_unused_reservation(client, engine):
    maker = async_sessionmaker(engine, expire_on_commit=False)
    job_id = (await submit(client)).json()["job_id"]
    async with maker() as db:
        attempt = await db.scalar(select(DemoAttempt))
        attempt.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        (await db.get(DemoJob, job_id)).status = "failed"
        await db.commit()
        budget = await limits.gate(db)
        await limits.expire_attempts(db, budget)
        await db.commit()
        assert attempt.closed and budget.reserved == 0


async def test_sync_and_async_provider_paths_cap_output_and_disable_hidden_retries(
    client, engine, monkeypatch, policy
):
    from unittest.mock import AsyncMock, Mock

    from pydantic import BaseModel

    from app.llm import structured
    from llm.client import OpenAIClient
    from llm.config import LLMSettings

    class Output(BaseModel):
        answer: str

    maker, token, _ = await activate(client, engine)
    try:
        fake = Mock()
        fake.with_options.return_value = fake
        fake.chat.completions.create.return_value = SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=5, completion_tokens=6),
            choices=[SimpleNamespace(message=SimpleNamespace(content="done"))],
        )
        sync_client = OpenAIClient(LLMSettings("openai", policy.llm_model, 0, "unused"))
        sync_client._client = fake
        assert await asyncio.to_thread(sync_client.complete, "sys", "user") == "done"
        fake.with_options.assert_called_once_with(max_retries=0)
        assert (
            fake.chat.completions.create.call_args.kwargs["max_tokens"]
            == policy.demo_max_output_tokens
        )

        async_client = Mock()
        async_client.with_options.return_value = async_client
        async_client.beta.chat.completions.parse = AsyncMock(
            return_value=SimpleNamespace(
                usage=SimpleNamespace(prompt_tokens=7, completion_tokens=8),
                choices=[SimpleNamespace(message=SimpleNamespace(parsed=Output(answer="yes")))],
            )
        )
        monkeypatch.setattr(structured, "get_client", lambda: async_client)
        assert (await structured.complete_structured("sys", "user", Output)).answer == "yes"
        async_client.with_options.assert_called_once_with(max_retries=0)
        assert (
            async_client.beta.chat.completions.parse.call_args.kwargs["max_tokens"]
            == policy.demo_max_output_tokens
        )
        async with maker() as db:
            assert (await db.scalar(select(DemoAttempt))).calls == 2
            assert (await db.get(DemoBudget, "global")).inflight == 0
        async_client.beta.chat.completions.parse.side_effect = TimeoutError(
            "unknown provider result"
        )
        with pytest.raises(TimeoutError):
            await structured.complete_structured("sys", "user", Output)
        async with maker() as db:
            assert (
                await db.scalar(
                    select(func.count()).select_from(DemoCall).where(DemoCall.state == "unknown")
                )
                == 1
            )
    finally:
        execution.reset(token)


async def test_worker_cancellation_holds_slot_until_real_thread_finishes(
    client, engine, monkeypatch
):
    from threading import Event

    entered, done = Event(), Event()

    def evaluate(*args):
        entered.set()
        assert done.wait(5)
        return {"project_id": "todo-api", "scored": True}

    monkeypatch.setattr(worker, "evaluate_context", evaluate)
    job_id = (await submit(client)).json()["job_id"]
    maker = async_sessionmaker(engine, expire_on_commit=False)
    task = asyncio.create_task(worker.run_job(job_id, maker))
    try:
        assert await asyncio.to_thread(entered.wait, 3)
        task.cancel()
        await asyncio.sleep(0.1)
        assert not task.done()
        async with maker() as db:
            assert await db.scalar(select(DemoSlot).where(DemoSlot.job_id == job_id)) is not None
    finally:
        done.set()
        with pytest.raises(asyncio.CancelledError):
            await task
    async with maker() as db:
        assert (await db.get(DemoJob, job_id)).status == "completed"
        assert await db.scalar(select(DemoSlot).where(DemoSlot.job_id == job_id)) is None


async def test_office_identical_prompt_can_run_three_times_but_not_a_fourth(
    client, engine, monkeypatch
):
    from app.features.office_prompting import service
    from app.features.office_prompting.schemas import ExtractionOutput

    async def extract(*args):
        return ExtractionOutput(ids=[])

    # Use the actual service mutations, with only the paid extraction replaced.
    monkeypatch.setattr(service, "extract_ids", extract)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    body = {
        "feature": "office_prompting",
        "action": "create_session",
        "input": {"body": {"candidate_name": "demo"}},
    }
    job_id = (await submit(client, "create-office", body)).json()["job_id"]
    await worker.run_job(job_id, maker)
    async with maker() as db:
        session_id = (await db.get(DemoJob, job_id)).result["body"]["session_id"]
    body = {
        "feature": "office_prompting",
        "action": "run",
        "input": {
            "params": {"session_id": session_id, "problem_index": 0},
            "body": {"prompt": "same instruction"},
        },
    }
    for n in range(3):
        accepted = await submit(client, f"office-{n}", body)
        assert accepted.status_code == 202
        await worker.run_job(accepted.json()["job_id"], maker)
    assert (await submit(client, "office-four", body)).status_code == 429


async def test_mock_exam_reserves_one_parent_and_rejects_second_start(client, engine):
    maker = async_sessionmaker(engine, expire_on_commit=False)
    body = {
        "feature": "mock_exam",
        "action": "start",
        "input": {"body": {"candidate_code": "portfolio"}},
    }
    first = await submit(client, "exam", body)
    assert first.status_code == 202
    await worker.run_job(first.json()["job_id"], maker)
    # Another idempotency key still replays the same complete start.
    assert (await submit(client, "exam-again", body)).json()["job_id"] == first.json()["job_id"]
    async with maker() as db:
        attempts = list(await db.scalars(select(DemoAttempt)))
        assert len(attempts) == 1 and attempts[0].feature == "mock_exam"
        assert attempts[0].root != "pending"


def test_nested_context_judge_threads_keep_server_execution(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    from feature_context_engineering.evaluate import build_report
    from feature_context_engineering.service import create_submission, get_project

    seen = []

    class FakeClient:
        def complete(self, *args, **kwargs):
            seen.append(execution.get())
            return "{}"

    marker = SimpleNamespace()
    token = execution.set(marker)
    # Isolate progress (not the nested LLM threads) from the test marker.
    try:
        with ThreadPoolExecutor() as pool:
            # The test caller explicitly propagates the parent context, as asyncio.to_thread does.
            from contextvars import copy_context

            pool.submit(
                copy_context().run,
                build_report,
                get_project("todo-api"),
                create_submission("todo-api", "make test"),
                FakeClient(),
                on_progress=lambda *a: None,
            ).result()
        assert len(seen) == 4 and all(item is marker for item in seen)
    finally:
        execution.reset(token)


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_POSTGRES_TESTS") != "1", reason="Set RUN_POSTGRES_TESTS=1")
async def test_postgres_atomic_budget_attempts_calls_and_slots(policy, monkeypatch):
    from uuid import uuid4

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.db.base import Base
    from feature_demo.jobs import CreateJob, accept_job
    from feature_demo.models import DemoSession

    schema = f"test_demo_limits_{uuid4().hex}"
    admin = create_async_engine(policy.database_url)
    engine = create_async_engine(
        policy.database_url, connect_args={"server_settings": {"search_path": schema}}
    )
    maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with admin.begin() as conn:
            await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with maker() as db:
            owners = [
                DemoSession(
                    token_hash=uuid4().hex,
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
                )
                for _ in range(2)
            ]
            db.add_all(owners)
            await db.commit()
            ids = [row.id for row in owners]
        monkeypatch.setattr(
            policy,
            "demo_daily_budget_usd",
            Decimal(limits.attempt_cost("context_engineering")) / Decimal(1_000_000_000),
        )

        async def accept(owner, key="one"):
            async with maker() as db:
                return (await accept_job(db, owner, key, CreateJob(**BODY))).id

        outcomes = await asyncio.gather(*(accept(owner) for owner in ids), return_exceptions=True)
        successful = [outcome for outcome in outcomes if isinstance(outcome, str)]
        assert len(successful) == 1
        assert (
            next(outcome for outcome in outcomes if isinstance(outcome, HTTPException)).status_code
            == 429
        )
        job_id = successful[0]
        async with maker() as db:
            job = await db.get(DemoJob, job_id)
            owner = job.session_id
            job.status, job.lease = "running", "lease"
            await db.commit()
        assert (
            await asyncio.gather(accept(owner, "duplicate-one"), accept(owner, "duplicate-two"))
        ) == [job_id, job_id]

        async def progress(*a):
            pass

        token = execution.set(
            Execution(
                owner,
                maker,
                datetime.now(timezone.utc),
                asyncio.get_running_loop(),
                progress,
                job_id,
                "lease",
            )
        )
        try:
            calls = await asyncio.gather(
                *(meter.reserve(policy.llm_model, [], None, 100) for _ in range(3))
            )
            await asyncio.gather(
                *(
                    meter.settle(call, SimpleNamespace(prompt_tokens=10, completion_tokens=20), 100)
                    for call in calls
                )
            )
        finally:
            execution.reset(token)
        async with maker() as db:
            attempt = await db.scalar(select(DemoAttempt))
            budget = await db.get(DemoBudget, "global")
            assert attempt.calls == 3 and budget.spent == 150_000 and budget.inflight == 0
            assert budget.reserved + budget.spent == limits.attempt_cost("context_engineering")
        first = await slots.acquire(maker, "evaluation", job_id, "first")
        waiting = asyncio.create_task(slots.acquire(maker, "evaluation", job_id, "second"))
        try:
            await asyncio.sleep(0.2)
            assert not waiting.done()
        finally:
            await slots.release(maker, "evaluation", first, "first")
            second = await asyncio.wait_for(waiting, 5)
            await slots.release(maker, "evaluation", second, "second")
    finally:
        await engine.dispose()
        async with admin.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await admin.dispose()


async def test_logical_replay_binds_new_idempotency_key_to_original_input(client, engine):
    original = (await submit(client, "first")).json()["job_id"]
    assert (await submit(client, "alias")).json()["job_id"] == original
    other = {
        "feature": "dev_prompting",
        "action": "create_run",
        "input": {"body": {"problem_id": "stepping-stones"}},
    }
    assert (await submit(client, "alias", other)).status_code == 409
