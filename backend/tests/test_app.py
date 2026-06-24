"""App assembly smoke test: the spec-design router is mounted and health works."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_spec_design_router_mounted():
    # /tasks needs no LLM, so it proves mounting without hitting the network.
    resp = client.get("/spec-design/tasks")
    assert resp.status_code == 200
    ids = {t["id"] for t in resp.json()}
    assert "login-signup" in ids
