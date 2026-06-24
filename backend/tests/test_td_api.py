"""API behavior tests with an in-memory DB and a mocked judge."""

import pytest


async def _create_session(client, name="길원"):
    resp = await client.post("/test-design/sessions", json={"candidate_name": name})
    assert resp.status_code == 201
    return resp.json()


async def test_create_session_returns_six_problems_without_ground_truth(client):
    data = await _create_session(client)
    assert data["session_id"]
    assert data["candidate_name"] == "길원"
    assert len(data["problems"]) == 6
    for p in data["problems"]:
        assert p["spec"] and p["difficulty"]
        # the hidden answer set must never be serialized to the candidate
        assert "flaws" not in p
        # prose-only: no code field is exposed
        assert set(p.keys()) == {"index", "id", "title", "difficulty", "spec"}


async def test_submit_scores_and_persists(client, mock_judge):
    session = await _create_session(client)
    sid = session["session_id"]

    resp = await client.post(
        f"/test-design/sessions/{sid}/problems/0/submit",
        json={"flaws": ["빈 리스트일 때 ZeroDivisionError", "엉뚱한 지적"]},
    )
    assert resp.status_code == 200
    assert resp.json() == {"problem_index": 0, "submitted": True}

    result = (await client.get(f"/test-design/sessions/{sid}/result")).json()
    assert result["status"] == "in_progress"  # only 1 of 6 submitted
    problem = result["problems"][0]
    assert problem["difficulty"] == "easy"  # problem_001 is an easy-tier scenario
    # stub judge matches the first item (1 of 6 for problem_001) via candidate 0
    assert problem["recall"] == pytest.approx(1 / 6)
    assert problem["precision"] == pytest.approx(1 / 2)  # 1 tp of 2 claims
    assert problem["flaws"][0]["found"] is True
    assert problem["flaws"][0]["quality"] == 2
    assert problem["flaws"][1]["found"] is False
    assert problem["false_positives"] == ["엉뚱한 지적"]
    assert problem["report"] == "stub report"


async def test_resubmit_is_idempotent_per_problem(client, mock_judge):
    session = await _create_session(client)
    sid = session["session_id"]
    for _ in range(2):
        r = await client.post(
            f"/test-design/sessions/{sid}/problems/0/submit",
            json={"flaws": ["x"]},
        )
        assert r.status_code == 200
    result = (await client.get(f"/test-design/sessions/{sid}/result")).json()
    # still a single submission for problem 0
    assert len(result["problems"]) == 1


async def test_empty_flaws_is_422(client, mock_judge):
    session = await _create_session(client)
    sid = session["session_id"]
    resp = await client.post(
        f"/test-design/sessions/{sid}/problems/0/submit", json={"flaws": []}
    )
    assert resp.status_code == 422


async def test_unknown_session_is_404(client, mock_judge):
    submit = await client.post(
        "/test-design/sessions/nope/problems/0/submit", json={"flaws": ["x"]}
    )
    assert submit.status_code == 404
    result = await client.get("/test-design/sessions/nope/result")
    assert result.status_code == 404


async def test_bad_problem_index_is_404(client, mock_judge):
    session = await _create_session(client)
    sid = session["session_id"]
    resp = await client.post(
        f"/test-design/sessions/{sid}/problems/99/submit", json={"flaws": ["x"]}
    )
    assert resp.status_code == 404
