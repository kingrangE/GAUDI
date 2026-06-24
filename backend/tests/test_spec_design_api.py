"""API behavior via TestClient with generator + judge clients overridden (LLM mocked)."""

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from feature_spec_design.api import get_gen_dependency, get_judge_dependency, router
from feature_spec_design.tasks import get_task

DESIGN = "결정: FastAPI, PostgreSQL, bcrypt, JWT, UUID, pydantic\n구현 …"


class FakeGen:
    def complete(self, system, user, *, temperature=None, max_tokens=None):
        return DESIGN


def _fixed_judge():
    task = get_task("login-signup")
    payload = {
        "requirements_met": [r.id for r in task.requirements],
        "decisions": {
            "password_storage": "bcrypt",
            "auth_mechanism": "jwt",
            "token_transport": "httponly_cookie",
            "user_id_strategy": "uuid",
            "input_validation": "pydantic",
        },
        "extra_scope": [],
    }

    class FakeJudge:
        def complete(self, system, user, *, temperature=None, max_tokens=None):
            return json.dumps(payload)

    return FakeJudge()


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_gen_dependency] = FakeGen
    app.dependency_overrides[get_judge_dependency] = _fixed_judge
    return TestClient(app)


def test_evaluate_endpoint_sound_spec_scores_high():
    resp = _client().post(
        "/spec-design/evaluate",
        json={
            "task_id": "login-signup",
            "instruction": "FastAPI, PostgreSQL, bcrypt, JWT 쿠키, UUID, pydantic",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["task_id"] == "login-signup"
    assert body["total_score"] == 100.0
    assert body["score"]["grade"] == "excellent"
    assert body["score"]["failed_requirements"] == []
    assert body["score"]["overengineered"] == []
    assert body["score"]["overengineering_penalty"] == 0.0
    assert body["overengineering"] == []
    assert len(body["samples"]) == 10
    assert len(body["requirements"]) == 7
    assert len(body["dimensions"]) == 5


def test_evaluate_unknown_task_404():
    resp = _client().post(
        "/spec-design/evaluate",
        json={"task_id": "does-not-exist", "instruction": "x"},
    )
    assert resp.status_code == 404


def test_evaluate_blank_instruction_422():
    resp = _client().post(
        "/spec-design/evaluate",
        json={"task_id": "login-signup", "instruction": "   "},
    )
    assert resp.status_code == 422


def test_list_tasks_endpoint():
    resp = _client().get("/spec-design/tasks")
    assert resp.status_code == 200
    ids = {t["id"] for t in resp.json()}
    assert {"login-signup", "file-upload-api"} <= ids


def test_get_task_hides_rubric_dimensions():
    resp = _client().get("/spec-design/tasks/login-signup")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "login-signup"
    assert body["dimension_count"] == 5
    assert body["requirement_count"] == 7
    # the decision rubric must never reach the client
    assert "dimensions" not in body


def test_get_task_unknown_404():
    resp = _client().get("/spec-design/tasks/nope")
    assert resp.status_code == 404
