"""cx-churn-radar-topn task: counts, evaluation with mocked LLM, scoring signal tests.

Verifies:
- Task loads with exactly 8 requirements and 7 dimensions.
- GET /spec-design/tasks includes the new task with correct counts (rubric hidden).
- A mocked-sample evaluation returns EvaluationResult with score.total in [0, 100].
- Weak/bad decisions lower the score compared to a fully sound spec.
- Over-engineering items are penalised.
"""

from __future__ import annotations

import asyncio
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from feature_spec_design.analyzer import analyze
from feature_spec_design.api import get_gen_dependency, get_judge_dependency, router
from feature_spec_design.models import Sample
from feature_spec_design.scorer import score_spec
from feature_spec_design.tasks import get_task

TASK = get_task("cx-churn-radar-topn")

# Canonical good decisions for all 7 dimensions
GOOD_DECISIONS = {
    "window_aggregation": "streaming",
    "late_event_policy": "watermark",
    "pii_handling": "tokenized",
    "storage": "postgres",
    "pagination": "cursor",
    "access_control": "internal_only",
    "scoring_source": "precomputed",
}

ALL_REQ_IDS = [r.id for r in TASK.requirements]


# ---------------------------------------------------------------------------
# Fake LLM helpers
# ---------------------------------------------------------------------------


class FakeJudge:
    """Returns the same canned judgement JSON for every call."""

    def __init__(self, payload: dict):
        self._payload = payload

    def complete(self, system, user, *, temperature=None, max_tokens=None):
        return json.dumps(self._payload)


class FakeGen:
    """Returns a fixed design sketch for every generation call."""

    CONTENT = (
        "결정: batch_precomputed, watermark, tokenized, postgres, "
        "cursor, internal_only, precomputed\n"
        "구현: 매일 배치 잡으로 이탈 스코어를 사전 계산해 PostgreSQL에 저장하고, "
        "cursor 페이지네이션으로 Top-N 목록을 내부 전용 엔드포인트로 제공한다."
    )

    def complete(self, system, user, *, temperature=None, max_tokens=None):
        return self.CONTENT


def _make_client(judge_payload: dict) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_gen_dependency] = FakeGen
    app.dependency_overrides[get_judge_dependency] = lambda: FakeJudge(judge_payload)
    return TestClient(app)


# ---------------------------------------------------------------------------
# Task structure tests
# ---------------------------------------------------------------------------


def test_task_loads():
    assert TASK is not None, "cx-churn-radar-topn task not found in registry"


def test_task_has_8_requirements():
    assert len(TASK.requirements) == 8


def test_task_has_7_dimensions():
    assert len(TASK.dimensions) == 7


def test_requirement_ids_are_unique():
    ids = [r.id for r in TASK.requirements]
    assert len(ids) == len(set(ids))


def test_dimension_keys_are_unique():
    keys = [d.key for d in TASK.dimensions]
    assert len(keys) == len(set(keys))


def test_all_dimension_options_have_valid_quality():
    valid = {"good", "ok", "weak", "bad"}
    for dim in TASK.dimensions:
        for opt in dim.options:
            assert opt.quality in valid, (
                f"dim={dim.key} opt={opt.value} has invalid quality={opt.quality!r}"
            )


def test_each_dimension_has_at_least_one_good_option():
    for dim in TASK.dimensions:
        good_opts = [o for o in dim.options if o.quality == "good"]
        assert good_opts, f"dimension {dim.key!r} has no 'good' option"


def test_each_dimension_has_at_least_one_bad_or_weak_option():
    for dim in TASK.dimensions:
        poor_opts = [o for o in dim.options if o.quality in ("bad", "weak")]
        assert poor_opts, f"dimension {dim.key!r} has no 'bad' or 'weak' option"


# ---------------------------------------------------------------------------
# API: task list / detail exposure
# ---------------------------------------------------------------------------


def _api_client() -> TestClient:
    return _make_client(
        {
            "requirements_met": ALL_REQ_IDS,
            "decisions": GOOD_DECISIONS,
            "extra_scope": [],
        }
    )


def test_list_tasks_includes_cx_churn():
    resp = _api_client().get("/spec-design/tasks")
    assert resp.status_code == 200
    ids = {t["id"] for t in resp.json()}
    assert "cx-churn-radar-topn" in ids


def test_get_task_returns_correct_counts():
    resp = _api_client().get("/spec-design/tasks/cx-churn-radar-topn")
    assert resp.status_code == 200
    body = resp.json()
    assert body["requirement_count"] == 8
    assert body["dimension_count"] == 7


def test_get_task_hides_rubric():
    resp = _api_client().get("/spec-design/tasks/cx-churn-radar-topn")
    body = resp.json()
    # The hidden decision rubric must never reach the client
    assert "dimensions" not in body
    assert "requirements" not in body


# ---------------------------------------------------------------------------
# Evaluation: mocked generator + judge
# ---------------------------------------------------------------------------


def test_evaluate_perfect_spec_scores_100():
    payload = {
        "requirements_met": ALL_REQ_IDS,
        "decisions": GOOD_DECISIONS,
        "extra_scope": [],
    }
    resp = _make_client(payload).post(
        "/spec-design/evaluate",
        json={
            "task_id": "cx-churn-radar-topn",
            "instruction": "스트리밍 집계, watermark, 토큰화 PII, postgres, "
            "cursor, 내부 전용, 사전계산",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["task_id"] == "cx-churn-radar-topn"
    total = body["score"]["total"]
    assert 0.0 <= total <= 100.0
    assert total == 100.0
    assert body["score"]["failed_requirements"] == []
    assert body["score"]["overengineered"] == []


def test_evaluate_result_total_in_0_100_range():
    """Any mocked evaluation must stay within [0, 100]."""
    payload = {
        "requirements_met": ALL_REQ_IDS[:4],  # partial coverage
        "decisions": {**GOOD_DECISIONS, "late_event_policy": "drop"},  # weak decision
        "extra_scope": [],
    }
    resp = _make_client(payload).post(
        "/spec-design/evaluate",
        json={"task_id": "cx-churn-radar-topn", "instruction": "적당히 설계해"},
    )
    assert resp.status_code == 200
    total = resp.json()["score"]["total"]
    assert 0.0 <= total <= 100.0


def test_evaluate_sample_and_dim_counts():
    payload = {
        "requirements_met": ALL_REQ_IDS,
        "decisions": GOOD_DECISIONS,
        "extra_scope": [],
    }
    resp = _make_client(payload).post(
        "/spec-design/evaluate",
        json={"task_id": "cx-churn-radar-topn", "instruction": "완벽한 설계"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["requirements"]) == 8
    assert len(body["dimensions"]) == 7
    assert len(body["samples"]) == 10  # default N=10


# ---------------------------------------------------------------------------
# Scoring signal: weak/bad decisions reduce score vs good decisions
# ---------------------------------------------------------------------------


def _samples(n: int = 10) -> list[Sample]:
    return [Sample(index=i, content="x") for i in range(n)]


def _run_analyze(payload: dict, n: int = 10):
    judge = FakeJudge(payload)
    samples = _samples(n)
    return asyncio.run(analyze(samples, TASK, judge))


def test_bad_pii_decision_lowers_score():
    good_payload = {"requirements_met": ALL_REQ_IDS, "decisions": GOOD_DECISIONS, "extra_scope": []}
    bad_payload = {
        "requirements_met": ALL_REQ_IDS,
        "decisions": {**GOOD_DECISIONS, "pii_handling": "plaintext"},
        "extra_scope": [],
    }
    reqs_g, dims_g, over_g = _run_analyze(good_payload)
    reqs_b, dims_b, over_b = _run_analyze(bad_payload)

    score_good = score_spec(reqs_g, dims_g, over_g).total
    score_bad = score_spec(reqs_b, dims_b, over_b).total
    assert score_bad < score_good, "bad PII handling should lower the score"


def test_weak_late_event_policy_listed_in_weak_decisions():
    payload = {
        "requirements_met": ALL_REQ_IDS,
        "decisions": {**GOOD_DECISIONS, "late_event_policy": "drop"},
        "extra_scope": [],
    }
    reqs, dims, over = _run_analyze(payload)
    score = score_spec(reqs, dims, over)
    # "drop" is quality=weak (score < 0.7) and agreement==1.0 (not diverged) -> weak_decisions
    weak_keys = [w.lower() for w in score.weak_decisions]
    assert any("late" in w or "late_event_policy" in w for w in weak_keys), (
        f"expected weak late_event_policy in weak_decisions, got: {score.weak_decisions}"
    )


def test_over_engineering_penalises_total():
    base_payload = {
        "requirements_met": ALL_REQ_IDS,
        "decisions": GOOD_DECISIONS,
        "extra_scope": [],
    }
    oe_payload = {
        "requirements_met": ALL_REQ_IDS,
        "decisions": GOOD_DECISIONS,
        "extra_scope": ["realtime_ml_pipeline", "admin_dashboard"],
    }
    reqs_b, dims_b, over_b = _run_analyze(base_payload)
    reqs_o, dims_o, over_o = _run_analyze(oe_payload)

    score_base = score_spec(reqs_b, dims_b, over_b).total
    score_oe = score_spec(reqs_o, dims_o, over_o).total
    assert score_oe < score_base, "over-engineering should reduce the total score"


def test_missing_requirements_fail_and_appear_in_feedback():
    payload = {
        "requirements_met": [],  # none met
        "decisions": GOOD_DECISIONS,
        "extra_scope": [],
    }
    reqs, dims, over = _run_analyze(payload)
    score = score_spec(reqs, dims, over)
    assert score.requirement_score == 0.0
    assert len(score.failed_requirements) == 8
    assert score.total < 100.0


def test_no_access_control_listed_as_bad_decision():
    payload = {
        "requirements_met": ALL_REQ_IDS,
        "decisions": {**GOOD_DECISIONS, "access_control": "public"},
        "extra_scope": [],
    }
    reqs, dims, over = _run_analyze(payload)
    score = score_spec(reqs, dims, over)
    assert any("access" in w.lower() or "접근" in w.lower() for w in score.weak_decisions), (
        f"expected bad access_control in weak_decisions, got: {score.weak_decisions}"
    )


def test_score_total_is_0_to_100_with_all_bad_decisions():
    """All-bad decisions + no requirements + over-engineering must stay in [0, 100].

    With all bad decisions the decision_score and requirement_score are 0, but
    consistently-wrong choices still contribute to the consistency axis (weight 0.4).
    The over-engineering penalty is capped at 30, so the floor is not necessarily 0.
    The important invariant is that the result is within [0, 100] and is well below the
    score obtained with a sound spec.
    """
    bad_decisions = {
        "window_aggregation": "no_window",
        "late_event_policy": "ignore",
        "pii_handling": "plaintext",
        "storage": "none",
        "pagination": "none",
        "access_control": "public",
        "scoring_source": "unscored",
    }
    payload = {
        "requirements_met": [],
        "decisions": bad_decisions,
        "extra_scope": ["realtime_ml", "admin_ui", "global_cdn", "ml_retraining"],
    }
    reqs, dims, over = _run_analyze(payload)
    score = score_spec(reqs, dims, over)
    # Invariant: score is always within valid range
    assert 0.0 <= score.total <= 100.0
    # Bad decisions + missing requirements + over-engineering must score below 50
    assert score.total < 50.0
