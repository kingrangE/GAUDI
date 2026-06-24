"""Smoke test for the assembled app entrypoint (router mounted, health up)."""

from fastapi.testclient import TestClient

from main import app


def test_health():
    resp = TestClient(app).get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_dev_prompting_router_mounted():
    resp = TestClient(app).get("/dev-prompting/problems")
    assert resp.status_code == 200
    assert any(p["id"] == "stepping-stones" for p in resp.json())
