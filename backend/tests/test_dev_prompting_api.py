"""API endpoint behavior via TestClient, with the solver client overridden (LLM mocked)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from feature_dev_prompting.api import get_solver_client, router

CORRECT_SUM = (
    "from collections import deque\n"
    "def solution(stones, k):\n"
    "    dq = deque()\n"
    "    res = float('inf')\n"
    "    for i, v in enumerate(stones):\n"
    "        while dq and stones[dq[-1]] <= v:\n"
    "            dq.pop()\n"
    "        dq.append(i)\n"
    "        if dq[0] <= i - k:\n"
    "            dq.popleft()\n"
    "        if i >= k - 1:\n"
    "            res = min(res, stones[dq[0]])\n"
    "    return res\n"
)


class FakeClient:
    def complete(self, system, user):
        return CORRECT_SUM


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_solver_client] = lambda: FakeClient()
    return TestClient(app)


def test_evaluate_endpoint_solved():
    resp = _client().post(
        "/dev-prompting/evaluate",
        json={"problem_id": "stepping-stones", "prompts": ["슬라이딩 윈도우로 풀어줘"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["solved"] is True
    assert body["score"]["total"] == 100.0


def test_evaluate_endpoint_unknown_problem():
    resp = _client().post(
        "/dev-prompting/evaluate",
        json={"problem_id": "does-not-exist", "prompts": ["x"]},
    )
    assert resp.status_code == 404


def test_evaluate_endpoint_empty_prompts():
    resp = _client().post(
        "/dev-prompting/evaluate",
        json={"problem_id": "stepping-stones", "prompts": []},
    )
    assert resp.status_code == 422


def test_list_problems_endpoint():
    resp = _client().get("/dev-prompting/problems")
    assert resp.status_code == 200
    ids = {p["id"] for p in resp.json()}
    assert "stepping-stones" in ids


def test_get_problem_hides_test_data():
    resp = _client().get("/dev-prompting/problems/stepping-stones")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "stepping-stones"
    assert body["public_example_count"] == 1
    assert body["entry_point"] == "solution"
    assert "def solution" in body["starter_code"]
    # public examples are exposed (args -> expected), one non-hidden case here
    assert body["examples"] == [{"args": [[2, 4, 5, 3, 2, 1, 4, 2, 5, 1], 3], "expected": 3}]
    # hidden test answers must never reach the client
    assert "tests" not in body


def test_get_problem_unknown():
    resp = _client().get("/dev-prompting/problems/nope")
    assert resp.status_code == 404
