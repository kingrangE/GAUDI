"""Endpoint tests for the office-prompting flow with the LLM mocked.

The LLM is mocked at the service layer (``service.extract_ids``); scoring stays
real and deterministic. Key behaviors asserted: correctness is hidden during
runs, runs are capped at MAX_RUNS, and the LAST run is what gets scored.
"""

import pytest

from app.features.office_prompting import service
from app.features.office_prompting.problems import PROBLEM_COUNT, PROBLEMS
from app.features.office_prompting.schemas import ExtractionOutput


@pytest.fixture
def mock_extract(monkeypatch):
    """Stateful fake: returns the problem's ground truth by default, or a scripted
    sequence of id-lists per problem index when one is provided via ``plan``."""
    plan: dict[int, list[list[str]]] = {}

    async def fake_extract(problem, prompt):
        seq = plan.get(problem.index)
        if seq:
            return ExtractionOutput(ids=seq.pop(0))
        return ExtractionOutput(ids=list(problem.ground_truth_ids))

    monkeypatch.setattr(service, "extract_ids", fake_extract)
    return plan


async def _start(client) -> str:
    resp = await client.post("/api/office-prompting/sessions", json={"candidate_name": "민수"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["problems"]) == PROBLEM_COUNT
    # full datasets shipped to the candidate, meeting the row floors
    tables = {t["name"]: t for t in body["datasets"]}
    assert set(tables) == {"customers", "orders", "products"}
    assert len(tables["customers"]["rows"]) >= 200
    return body["session_id"]


async def test_run_hides_correctness(client, mock_extract):
    session_id = await _start(client)
    base = f"/api/office-prompting/sessions/{session_id}"
    resp = await client.post(f"{base}/problems/0/run", json={"prompt": "조건 명세"})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {
        "problem_index",
        "run_number",
        "runs_used",
        "runs_remaining",
        "predicted_ids",
        "predicted_rows",
    }
    # ground-truth / scoring must NOT leak during a run
    for leak in ("precision", "recall", "f1", "tp", "fp", "fn", "truth_ids", "correct_count"):
        assert leak not in body
    assert body["runs_remaining"] == 2


async def test_runs_are_capped(client, mock_extract):
    session_id = await _start(client)
    base = f"/api/office-prompting/sessions/{session_id}/problems/0/run"
    remaining = []
    for _ in range(3):
        resp = await client.post(base, json={"prompt": "x"})
        assert resp.status_code == 200
        remaining.append(resp.json()["runs_remaining"])
    assert remaining == [2, 1, 0]
    # 4th run rejected
    resp = await client.post(base, json={"prompt": "x"})
    assert resp.status_code == 409


async def test_last_run_is_scored(client, mock_extract):
    session_id = await _start(client)
    base = f"/api/office-prompting/sessions/{session_id}"
    # problem 0: two wrong runs (empty), then a perfect last run
    mock_extract[0] = [[], [], list(PROBLEMS[0].ground_truth_ids)]
    for _ in range(3):
        await client.post(f"{base}/problems/0/run", json={"prompt": "x"})
    # problems 1 & 2: a single perfect run (fake default returns ground truth)
    for idx in (1, 2):
        await client.post(f"{base}/problems/{idx}/run", json={"prompt": "x"})

    resp = await client.post(f"{base}/score")
    assert resp.status_code == 200
    result = resp.json()
    p0 = result["problems"][0]
    # if the FIRST (empty) run had been scored, recall would be 0; it's the LAST.
    assert p0["f1"] == 1.0
    assert p0["correct_count"] == p0["truth_count"] > 0


async def test_full_flow_perfect_then_reveals_truth(client, mock_extract):
    session_id = await _start(client)
    base = f"/api/office-prompting/sessions/{session_id}"
    for idx in range(PROBLEM_COUNT):
        await client.post(f"{base}/problems/{idx}/run", json={"prompt": "정확한 조건"})
    resp = await client.post(f"{base}/score")
    assert resp.status_code == 200
    result = resp.json()
    assert result["status"] == "scored"
    assert result["precision"] == 1.0 and result["recall"] == 1.0 and result["f1"] == 1.0
    expected_total = sum(len(p.ground_truth_ids) for p in PROBLEMS)
    assert result["total_correct"] == expected_total
    # result reveals ground truth
    assert result["problems"][0]["truth_ids"]

    fetched = await client.get(f"{base}/result")
    assert fetched.status_code == 200
    assert fetched.json()["f1"] == 1.0


async def test_unknown_session_is_404(client, mock_extract):
    resp = await client.post(
        "/api/office-prompting/sessions/nope/problems/0/run", json={"prompt": "x"}
    )
    assert resp.status_code == 404


async def test_problem_index_out_of_range_is_404(client, mock_extract):
    session_id = await _start(client)
    resp = await client.post(
        f"/api/office-prompting/sessions/{session_id}/problems/9/run", json={"prompt": "x"}
    )
    assert resp.status_code == 404


async def test_score_before_any_run_is_conflict(client, mock_extract):
    session_id = await _start(client)
    resp = await client.post(f"/api/office-prompting/sessions/{session_id}/score")
    assert resp.status_code == 409


async def test_result_before_scoring_is_conflict(client, mock_extract):
    session_id = await _start(client)
    resp = await client.get(f"/api/office-prompting/sessions/{session_id}/result")
    assert resp.status_code == 409
