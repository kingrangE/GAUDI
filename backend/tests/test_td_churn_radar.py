"""Tests specific to the cx-churn-radar problem in the test-design evaluation.

Covers:
1. Problem loads by ID.
2. Exactly 15 flaws with valid id / severity / category fields.
3. All 8 flaw categories are represented.
4. A mocked-judge submission yields recall/precision/mean_quality/weighted_score
   with weighted_score in [0, 1].
"""

import pytest

from app.features.test_design.problems import find_problem
from app.features.test_design.scoring import SEVERITY_WEIGHT

_VALID_SEVERITIES = {"low", "medium", "high"}
_VALID_CATEGORIES = {
    "boundary",
    "error_handling",
    "concurrency",
    "security",
    "data_integrity",
    "validation",
    "performance",
    "correctness",
}

# Index of cx-churn-radar inside the PROBLEMS tuple (7th problem, 0-based → 6).
_CCR_INDEX = 6


# ---------------------------------------------------------------------------
# Unit-level: problem fixtures
# ---------------------------------------------------------------------------


def test_cx_churn_radar_problem_loads():
    p = find_problem("cx-churn-radar")
    assert p is not None
    assert p.id == "cx-churn-radar"
    assert p.difficulty == "hard"
    assert p.title
    assert p.spec.strip()
    assert len(p.provided_tests) >= 2


def test_cx_churn_radar_has_exactly_15_flaws_with_valid_fields():
    p = find_problem("cx-churn-radar")
    assert p is not None
    assert len(p.flaws) == 15, f"Expected 15 flaws, got {len(p.flaws)}"

    ids_seen: set[str] = set()
    for flaw in p.flaws:
        assert flaw.id, "Flaw id must be non-empty"
        assert flaw.id not in ids_seen, f"Duplicate flaw id: {flaw.id}"
        ids_seen.add(flaw.id)

        assert flaw.text.strip(), f"Flaw {flaw.id} has empty text"
        assert flaw.severity in _VALID_SEVERITIES, (
            f"Flaw {flaw.id} severity={flaw.severity!r} not in {_VALID_SEVERITIES}"
        )
        assert flaw.category in _VALID_CATEGORIES, (
            f"Flaw {flaw.id} category={flaw.category!r} not in {_VALID_CATEGORIES}"
        )


def test_cx_churn_radar_covers_all_8_categories():
    p = find_problem("cx-churn-radar")
    assert p is not None
    categories_present = {f.category for f in p.flaws}
    missing = _VALID_CATEGORIES - categories_present
    assert not missing, f"cx-churn-radar flaws missing categories: {missing}"


# ---------------------------------------------------------------------------
# Integration-level: mocked-judge submission through the API
# ---------------------------------------------------------------------------


async def test_cx_churn_radar_mocked_judge_submission_yields_valid_scores(
    client, mock_judge
):
    """Submit two candidate flaws for cx-churn-radar via the API with a
    deterministic stub judge (matches only flaw 0 at quality 2) and verify
    that recall / precision / mean_quality / weighted_score are computed
    correctly and that weighted_score is in [0, 1].

    Expected values (stub matches ccr_f01, severity=high, weight=3; total
    weight = 8×3 + 6×2 + 1×1 = 37):
      recall          = 1 / 15
      precision       = 1 / 2   (1 tp out of 2 submitted flaws)
      mean_quality    = 2.0
      weighted_score  = 3 * (2/2) / 37 = 3/37 ≈ 0.081
    """
    p = find_problem("cx-churn-radar")
    assert p is not None

    # Compute expected weighted total from the real flaw definitions.
    expected_total_weight = sum(SEVERITY_WEIGHT[f.severity] for f in p.flaws)
    first_flaw_weight = SEVERITY_WEIGHT[p.flaws[0].severity]
    expected_weighted_score = first_flaw_weight / expected_total_weight

    # Create a session and submit two flaws for the cx-churn-radar problem.
    resp = await client.post(
        "/test-design/sessions", json={"candidate_name": "테스트응시자"}
    )
    assert resp.status_code == 201
    sid = resp.json()["session_id"]

    submit = await client.post(
        f"/test-design/sessions/{sid}/problems/{_CCR_INDEX}/submit",
        json={"flaws": ["윈도우 경계 off-by-one 문제", "엉뚱한 지적"]},
    )
    assert submit.status_code == 200
    assert submit.json() == {"problem_index": _CCR_INDEX, "submitted": True}

    result = (await client.get(f"/test-design/sessions/{sid}/result")).json()
    problems = result["problems"]
    assert len(problems) == 1

    prob = problems[0]
    assert prob["problem_id"] == "cx-churn-radar"
    assert prob["difficulty"] == "hard"

    assert prob["recall"] == pytest.approx(1 / 15)
    assert prob["precision"] == pytest.approx(1 / 2)
    assert prob["mean_quality"] == pytest.approx(2.0)
    assert prob["weighted_score"] == pytest.approx(expected_weighted_score)

    # weighted_score must be in [0, 1]
    assert 0.0 <= prob["weighted_score"] <= 1.0

    # Stub judge detail: first flaw matched, remaining 14 missed.
    assert prob["flaws"][0]["found"] is True
    assert prob["flaws"][0]["quality"] == 2
    for flaw_result in prob["flaws"][1:]:
        assert flaw_result["found"] is False

    assert prob["false_positives"] == ["엉뚱한 지적"]
    assert prob["report"] == "stub report"
