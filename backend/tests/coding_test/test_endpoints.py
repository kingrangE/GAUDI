"""Endpoint tests for the coding-test flow (in-process runner, no LLM)."""

from app.features.coding_test.problems import PROBLEMS

_REF = {p.id: p.reference_solution for p in PROBLEMS}

BASE = "/api/coding-test"


async def test_list_problems(coding_client):
    resp = await coding_client.get(f"{BASE}/problems")
    assert resp.status_code == 200
    ids = {p["id"] for p in resp.json()}
    assert ids == {"two-sum", "group-anagrams", "valid-parentheses"}


async def test_problem_detail_hides_ground_truth(coding_client):
    resp = await coding_client.get(f"{BASE}/problems/two-sum")
    assert resp.status_code == 200
    body = resp.json()
    assert body["function_name"] == "two_sum"
    assert body["starter_code"]
    assert len(body["sample_cases"]) == 2
    # hidden grounding must never leak to the candidate
    assert "reference_solution" not in body
    assert "rubric" not in body
    assert "grading" not in body
    assert "test_cases" not in body


async def test_run_executes_samples(coding_client):
    ok = await coding_client.post(
        f"{BASE}/problems/two-sum/run", json={"code": _REF["two-sum"]}
    )
    assert ok.status_code == 200
    results = ok.json()["results"]
    assert len(results) == 2
    assert all(r["passed"] for r in results)

    buggy = await coding_client.post(
        f"{BASE}/problems/two-sum/run",
        json={"code": "def two_sum(nums, target):\n    return []\n"},
    )
    assert buggy.status_code == 200
    assert all(not r["passed"] for r in buggy.json()["results"])


async def test_submit_reference_scores_full(coding_client):
    created = await coding_client.post(
        f"{BASE}/submissions",
        json={"problem_id": "two-sum", "candidate_id": "민수", "code": _REF["two-sum"]},
    )
    assert created.status_code == 202
    assert created.json()["status"] == "grading"
    submission_id = created.json()["submission_id"]

    result = await coding_client.get(f"{BASE}/submissions/{submission_id}")
    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "graded"
    assert body["test_passed"] == body["test_total"] == 5
    # judge fields are not populated until PR-B
    assert body["code_quality_score"] is None
    assert body["analysis_report"] is None


async def test_submit_buggy_is_partial(coding_client):
    created = await coding_client.post(
        f"{BASE}/submissions",
        json={
            "problem_id": "two-sum",
            "candidate_id": "민수",
            "code": "def two_sum(nums, target):\n    return []\n",
        },
    )
    submission_id = created.json()["submission_id"]
    body = (await coding_client.get(f"{BASE}/submissions/{submission_id}")).json()
    assert body["status"] == "graded"
    assert body["test_passed"] == 0
    assert body["test_total"] == 5


async def test_unordered_problem_reference_passes(coding_client):
    """group-anagrams uses the unordered comparator end-to-end."""
    created = await coding_client.post(
        f"{BASE}/submissions",
        json={
            "problem_id": "group-anagrams",
            "candidate_id": "혁신",
            "code": _REF["group-anagrams"],
        },
    )
    submission_id = created.json()["submission_id"]
    body = (await coding_client.get(f"{BASE}/submissions/{submission_id}")).json()
    assert body["status"] == "graded"
    assert body["test_passed"] == body["test_total"]


async def test_unknown_problem_is_404(coding_client):
    assert (await coding_client.get(f"{BASE}/problems/nope")).status_code == 404
    assert (
        await coding_client.post(f"{BASE}/problems/nope/run", json={"code": "x=1"})
    ).status_code == 404
    created = await coding_client.post(
        f"{BASE}/submissions",
        json={"problem_id": "nope", "candidate_id": "x", "code": "x=1"},
    )
    assert created.status_code == 404


async def test_unknown_submission_is_404(coding_client):
    assert (
        await coding_client.get(f"{BASE}/submissions/does-not-exist")
    ).status_code == 404


async def test_missing_fields_are_422(coding_client):
    assert (
        await coding_client.post(f"{BASE}/problems/two-sum/run", json={})
    ).status_code == 422
    assert (
        await coding_client.post(f"{BASE}/submissions", json={"problem_id": "two-sum"})
    ).status_code == 422
