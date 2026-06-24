"""HTTP surface for the context-engineering feature (FastAPI TestClient, no real network)."""

import json

from fastapi.testclient import TestClient

from app import app
from feature_context_engineering import router as router_mod
from feature_context_engineering.rubric import get_rubric

client = TestClient(app)


def test_list_projects_endpoint():
    res = client.get("/api/context-engineering/projects")
    assert res.status_code == 200
    ids = [p["id"] for p in res.json()]
    assert "todo-api" in ids


def test_get_project_serves_full_file_content():
    res = client.get("/api/context-engineering/projects/todo-api")
    assert res.status_code == 200
    files = [f for f in res.json()["files"] if f["kind"] == "file"]
    assert files and all(f["content"] for f in files)


def test_get_unknown_project_404():
    res = client.get("/api/context-engineering/projects/nope")
    assert res.status_code == 404


def test_submit_empty_400():
    res = client.post(
        "/api/context-engineering/submissions",
        json={"project_id": "todo-api", "claude_md": "   "},
    )
    assert res.status_code == 400


def test_submit_without_judge_runs_deterministic_axes(monkeypatch):
    # No API key -> coverage/boundary unavailable, but grounding/conciseness still score.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    res = client.post(
        "/api/context-engineering/submissions",
        json={"project_id": "todo-api", "claude_md": "`app/main.py` 실행은 `make test`"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["scored"] is True
    dims = {d["key"]: d for d in body["dimensions"]}
    assert dims["coverage"]["available"] is False
    assert dims["grounding"]["available"] is True


def test_submit_with_judge_returns_composite(monkeypatch):
    ids = [c.id for c in get_rubric("todo-api")]
    coverage_raw = json.dumps([{"id": i, "covered": True, "evidence": "MK"} for i in ids])
    boundary_raw = json.dumps({"action": "refuse", "code": ""})

    class RoutingClient:
        def complete(self, system: str, user: str) -> str:
            return boundary_raw if "작업 요청" in user else coverage_raw

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(router_mod, "get_llm_client", lambda settings: RoutingClient())

    res = client.post(
        "/api/context-engineering/submissions",
        json={"project_id": "todo-api", "claude_md": "`app/main.py` `make test` MK"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["scored"] is True
    dims = {d["key"]: d for d in body["dimensions"]}
    assert dims["coverage"]["available"] is True
    assert dims["coverage"]["score"] == 100.0
    assert dims["boundary"]["score"] == 100.0
    assert body["total"] > 0
    assert all(r["text"] for r in body["results"])
