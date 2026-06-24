"""Scoring: blend requirement coverage + decision (agreement × quality); surface gaps."""

from feature_spec_design.models import (
    DimensionResult,
    OverEngineeringItem,
    RequirementResult,
)
from feature_spec_design.scorer import score_spec


def _req(rid, satisfaction):
    return RequirementResult(
        id=rid,
        text=rid,
        met_count=round(satisfaction * 10),
        total=10,
        satisfaction=satisfaction,
        satisfied=satisfaction >= 0.7,
    )


def _dim(key, agreement, quality, quality_score, diverged=False, top="x"):
    return DimensionResult(
        key=key,
        label=key,
        distribution={top: 10},
        top_value=top,
        agreement=agreement,
        quality=quality,
        quality_score=quality_score,
        score=round(agreement * quality_score, 4),
        diverged=diverged,
    )


def test_perfect_spec_is_100():
    reqs = [_req("a", 1.0), _req("b", 1.0)]
    dims = [_dim("p", 1.0, "good", 1.0), _dim("q", 1.0, "good", 1.0)]
    s = score_spec(reqs, dims)
    assert s.requirement_score == 100.0
    assert s.decision_score == 100.0
    assert s.total == 100.0
    assert s.grade == "excellent"
    assert s.failed_requirements == []
    assert s.weak_decisions == []
    assert s.diverged_decisions == []
    assert s.overengineered == []
    assert s.overengineering_penalty == 0.0
    assert s.base_score == 100.0


def test_omitted_requirement_is_penalized_and_listed():
    reqs = [_req("signup", 1.0), _req("email_verification", 0.0)]
    dims = [_dim("p", 1.0, "good", 1.0)]
    s = score_spec(reqs, dims)
    # requirement mean = (1.0 + 0.0)/2 = 0.5 -> 50
    assert s.requirement_score == 50.0
    assert "email_verification" in s.failed_requirements
    assert s.total < 100.0


def test_confidently_wrong_decision_is_penalized_and_flagged():
    reqs = [_req("a", 1.0)]
    dims = [_dim("password_storage", 1.0, "bad", 0.0, top="md5")]  # consistent but bad
    s = score_spec(reqs, dims)
    assert s.decision_score == 0.0  # agreement × quality(bad)
    assert any("password_storage" in w and "위험" in w for w in s.weak_decisions)


def test_diverged_decision_listed_not_in_weak():
    reqs = [_req("a", 1.0)]
    dims = [_dim("token_transport", 0.4, "good", 1.0, diverged=True)]
    s = score_spec(reqs, dims)
    assert "token_transport" in s.diverged_decisions
    assert s.weak_decisions == []  # diverged is reported separately


def _over(label, count, total=10):
    return OverEngineeringItem(label=label, count=count, prevalence=count / total)


def test_overengineering_penalizes_and_lists():
    reqs = [_req("a", 1.0)]
    dims = [_dim("p", 1.0, "good", 1.0)]  # base would be 100
    over = [_over("two_factor_auth", 8), _over("admin_dashboard", 7)]
    s = score_spec(reqs, dims, over)
    assert s.base_score == 100.0
    assert s.overengineering_penalty == 20.0  # 2 items × 10
    assert s.total == 80.0
    assert any("two_factor_auth" in o for o in s.overengineered)
    assert "과설계" in s.feedback


def test_overengineering_penalty_is_capped():
    reqs = [_req("a", 1.0)]
    dims = [_dim("p", 1.0, "good", 1.0)]
    over = [_over(f"feat_{i}", 9) for i in range(5)]  # 5×10 = 50, capped at 30
    s = score_spec(reqs, dims, over)
    assert s.overengineering_penalty == 30.0
    assert s.total == 70.0


def test_total_clamped_at_zero():
    reqs = [_req("a", 0.0)]
    dims = [_dim("p", 0.0, "bad", 0.0, diverged=True)]  # base 0
    over = [_over("x", 10)]
    s = score_spec(reqs, dims, over)
    assert s.total == 0.0  # max(0, 0 - 10)


def test_grade_thresholds():
    # All three axes equal t/100 (req sat, agreement, quality 1.0) -> total == t.
    def graded(t):
        reqs = [_req("a", t / 100)]
        dims = [_dim("p", t / 100, "good", 1.0)]
        s = score_spec(reqs, dims)
        return s.total, s.grade

    assert graded(100) == (100.0, "excellent")
    assert graded(80) == (80.0, "good")
    assert graded(60) == (60.0, "fair")
    assert graded(20) == (20.0, "poor")


def test_consistency_is_weighted_highest():
    # Same requirement + quality, but higher agreement -> higher total (consistency 0.4).
    low = score_spec([_req("a", 1.0)], [_dim("p", 0.4, "good", 1.0, diverged=True)]).total
    high = score_spec([_req("a", 1.0)], [_dim("p", 1.0, "good", 1.0)]).total
    assert high > low
