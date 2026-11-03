"""Public browsing and cross-visitor isolation through the assembled application."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.features.mock_exam.models import ExamAttempt
from app.features.office_prompting.models import OfficeSession
from app.features.rejection_eval.models import RejectionSession
from feature_demo.models import DemoResource, DemoSession
from feature_demo.session import COOKIE_NAME, token_hash


@pytest.fixture(autouse=True)
def demo_mode(monkeypatch):
    monkeypatch.setattr(get_settings(), "demo_enabled", True)
    monkeypatch.setattr(get_settings(), "demo_cookie_secure", False)


async def open_session(client):
    response = await client.post("/api/demo/session")
    assert response.status_code == 200
    return response.json()


async def test_issue_hash_cookie_reuse_and_renew_without_reset(client, engine):
    first = await open_session(client)
    token = client.cookies.get(COOKIE_NAME)
    response = await client.post("/api/demo/session")
    assert response.json()["session_id"] == first["session_id"]
    assert response.json()["expires_at"] >= first["expires_at"]
    assert client.cookies.get(COOKIE_NAME) == token
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "samesite=lax" in response.headers["set-cookie"].lower()
    assert "no-store" in response.headers["cache-control"]
    async with async_sessionmaker(engine)() as db:
        stored = await db.get(DemoSession, first["session_id"])
        assert stored.token_hash == token_hash(token)
        assert stored.token_hash != token
        assert await db.scalar(select(func.count()).select_from(DemoSession)) == 1
        assert await db.scalar(select(func.count()).select_from(DemoResource)) == 0
    assert (await client.get("/api/demo/session")).json()["session_id"] == first["session_id"]


async def test_production_cookie_is_secure(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "demo_cookie_secure", True)
    response = await client.post("/api/demo/session")
    assert "; secure" in response.headers["set-cookie"].lower()


@pytest.mark.parametrize(
    "path",
    [
        "/api/coding-test/problems",
        "/api/cs-eval/questions",
        "/dev-prompting/problems",
        "/spec-design/tasks",
        "/api/context-engineering/projects",
    ],
)
async def test_browsing_does_not_need_session_or_create_resources(client, engine, path):
    assert (await client.get(path)).status_code == 200
    async with async_sessionmaker(engine)() as db:
        assert await db.scalar(select(func.count()).select_from(DemoSession)) == 0
        assert await db.scalar(select(func.count()).select_from(DemoResource)) == 0


@pytest.mark.parametrize(
    "path",
    [
        "/test-design/sessions",
        "/api/rejection-eval/sessions",
        "/api/office-prompting/sessions",
        "/dev-prompting/runs",
        "/dev-prompting/evaluate",
        "/spec-design/evaluate",
        "/api/context-engineering/submissions",
        "/api/coding-test/submissions",
        "/api/coding-test/problems/x/run",
        "/api/cs-eval/sessions",
        "/api/mock-exam/start",
    ],
)
async def test_all_mutation_entrypoints_reject_missing_cookie_before_work(client, path):
    # The shared fixture sends a valid admin token, which must not bypass visitor ownership.
    assert (await client.post(path, json={})).status_code == 401


@pytest.mark.parametrize("cookie", ["forged-token", "x" * 43, "x" * 10000])
async def test_invalid_cookie_does_not_authenticate(client, cookie):
    client.cookies.set(COOKIE_NAME, cookie)
    assert (await client.get("/api/demo/session")).status_code == 401
    assert (
        await client.post("/test-design/sessions", json={"candidate_name": "x"})
    ).status_code == 401


async def test_expired_cookie_cannot_access_old_resources(client, engine):
    info = await open_session(client)
    created = await client.post("/test-design/sessions", json={"candidate_name": "same"})
    path = f"/test-design/sessions/{created.json()['session_id']}/result"
    async with async_sessionmaker(engine)() as db:
        visitor = await db.get(DemoSession, info["session_id"])
        visitor.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        await db.commit()
    assert (await client.get(path)).status_code == 401
    replacement = await open_session(client)
    assert replacement["session_id"] != info["session_id"]
    assert (await client.get(path)).status_code == 404


@pytest.mark.parametrize(
    "prefix,payload,suffix",
    [
        ("/test-design", {"candidate_name": "same"}, "/result"),
        ("/api/rejection-eval", {}, "/result"),
        ("/api/office-prompting", {"candidate_name": "same"}, "/result"),
    ],
)
async def test_native_results_are_private_even_with_same_candidate_name(
    client,
    engine,
    prefix,
    payload,
    suffix,
):
    first = await open_session(client)
    created = await client.post(f"{prefix}/sessions", json=payload)
    assert created.is_success
    native_id = created.json()["session_id"]
    path = f"{prefix}/sessions/{native_id}{suffix}"
    model = {"/api/rejection-eval": RejectionSession, "/api/office-prompting": OfficeSession}.get(
        prefix
    )
    if model:
        async with async_sessionmaker(engine)() as db:
            resource = await db.get(model, native_id)
            resource.status = "scored"
            resource.precision = resource.recall = resource.f1 = 1.0
            await db.commit()
    assert (await client.get(path)).status_code == 200
    assert (await client.get(path)).headers["cache-control"] == "no-store"
    assert (await client.post("/api/demo/session")).json()["session_id"] == first["session_id"]
    assert (await client.get(path)).status_code == 200
    client.cookies.clear()
    await open_session(client)
    assert (await client.get(path)).status_code == 404
    assert (await client.post(f"{prefix}/sessions/{native_id}/score", json={})).status_code == 404


async def test_other_visitor_cannot_submit_or_run_owners_input(client, mock_judge):
    await open_session(client)
    created = await client.post("/test-design/sessions", json={"candidate_name": "same"})
    native_id = created.json()["session_id"]
    path = f"/test-design/sessions/{native_id}/problems/0/submit"
    assert (await client.post(path, json={"flaws": ["x"]})).status_code == 200
    client.cookies.clear()
    await open_session(client)
    assert (await client.post(path, json={"flaws": ["changed"]})).status_code == 404


async def test_dev_run_is_owned_and_unauthorized_turn_never_calls_solver(client):
    await open_session(client)
    created = await client.post("/dev-prompting/runs", json={"problem_id": "stepping-stones"})
    assert created.status_code == 200
    path = f"/dev-prompting/runs/{created.json()['run_id']}/turns"
    client.cookies.clear()
    await open_session(client)
    assert (await client.post(path, json={"prompt": "x", "turn": 1})).status_code == 404


async def test_mock_exam_uses_server_identity_and_checks_every_child_path(client, engine):
    visitor = await open_session(client)
    created = await client.post("/api/mock-exam/start", json={"candidate_code": "forged"})
    assert created.status_code == 200
    attempt_id = created.json()["attempt_id"]
    root = f"/api/mock-exam/attempts/{attempt_id}"
    async with async_sessionmaker(engine)() as db:
        attempt = await db.get(ExamAttempt, attempt_id)
        assert attempt.candidate_code == f"DEMO-{visitor['session_id']}"
    assert (await client.get(root)).status_code == 200
    client.cookies.clear()
    await open_session(client)
    for suffix in ["", "/steps/context_engineering", "/dev-run"]:
        assert (await client.get(root + suffix)).status_code == 404
    for suffix in [
        "/steps/rejection_eval/generate",
        "/dev-run",
        "/finish",
        "/steps/context_engineering/submit",
        "/steps/context_engineering/retry",
    ]:
        assert (await client.post(root + suffix, json={})).status_code == 404


async def test_untrusted_origin_cannot_issue_or_mutate_session(client):
    assert (
        await client.post("/api/demo/session", headers={"Origin": "https://evil.test"})
    ).status_code == 403
    await open_session(client)
    response = await client.post(
        "/test-design/sessions",
        json={"candidate_name": "x"},
        headers={"Origin": "https://evil.test"},
    )
    assert response.status_code == 403
    allowed = await client.post("/api/demo/session", headers={"Origin": "http://localhost:3000"})
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-credentials"] == "true"


async def test_demo_disabled_preserves_legacy_mode(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "demo_enabled", False)
    assert (await client.post("/api/demo/session")).status_code == 404
    assert (await client.get("/api/demo/session")).status_code == 404
    assert (
        await client.post("/test-design/sessions", json={"candidate_name": "x"})
    ).status_code == 201


async def test_demo_cookie_never_authenticates_admin(client):
    await open_session(client)
    client.headers.pop("X-Admin-Token")
    assert (await client.get("/api/admin/exam-results")).status_code == 401


@pytest.mark.parametrize("kind", ["coding_test", "cs_eval"])
async def test_grading_resources_are_owned_before_dispatch_and_polling(
    client, engine, monkeypatch, kind
):
    from app.features.coding_test import tasks as coding_tasks
    from app.features.coding_test.problems import PROBLEMS
    from app.features.cs_eval import tasks as cs_tasks
    from app.features.cs_eval.questions import QUESTIONS
    from app.scripts.seed_cs_questions import _upsert as seed_question
    from app.scripts.seed_problems import _upsert as seed_problem

    visitor = await open_session(client)
    async with async_sessionmaker(engine)() as db:
        await seed_problem(db, PROBLEMS[0])
        await seed_question(db, QUESTIONS[0])
        await db.commit()

    dispatched = []

    async def enqueue(db, resource_id, *args):
        owner = await db.get(DemoResource, (kind, resource_id))
        assert owner.session_id == visitor["session_id"]
        dispatched.append(resource_id)

    if kind == "coding_test":
        monkeypatch.setattr(coding_tasks, "enqueue_grading", enqueue)
        create_path, read_path, key = (
            "/api/coding-test/submissions",
            "/api/coding-test/submissions",
            "submission_id",
        )
        payload = {"candidate_id": "same", "problem_id": PROBLEMS[0].id, "code": "pass"}
    else:
        monkeypatch.setattr(cs_tasks, "enqueue_grading", enqueue)
        create_path, read_path, key = "/api/cs-eval/sessions", "/api/cs-eval/sessions", "session_id"
        payload = {
            "candidate_id": "same",
            "answers": [{"question_id": QUESTIONS[0].id, "answer_text": "x"}],
        }
    response = await client.post(create_path, json=payload)
    assert response.status_code == 202
    resource_id = response.json()[key]
    assert dispatched == [resource_id]
    assert (await client.get(f"{read_path}/{resource_id}")).status_code == 200
    client.cookies.clear()
    await open_session(client)
    assert (await client.get(f"{read_path}/{resource_id}")).status_code == 404
