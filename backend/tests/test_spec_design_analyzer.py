"""Judge + aggregation: requirement coverage and decision (agreement × quality).

The judge LLM is mocked with a fake returning canned judgement JSON.
"""

import asyncio
import json
import threading

from feature_spec_design.analyzer import (
    aggregate_dimensions,
    aggregate_overengineering,
    aggregate_requirements,
    analyze,
    parse_judgement,
    quality_of,
)
from feature_spec_design.tasks import get_task

TASK = get_task("login-signup")
GOOD_DECISIONS = {
    "password_storage": "bcrypt",
    "auth_mechanism": "jwt",
    "token_transport": "httponly_cookie",
    "user_id_strategy": "uuid",
    "input_validation": "pydantic",
}


class FakeJudge:
    """Returns the same canned judgement for every sample."""

    def __init__(self, payload):
        self._payload = payload
        self.calls = 0
        self._lock = threading.Lock()

    def complete(self, system, user, *, temperature=None, max_tokens=None):
        with self._lock:
            self.calls += 1
        return json.dumps(self._payload)


def _dim(key):
    return next(d for d in TASK.dimensions if d.key == key)


def test_quality_of_grades_known_unknown_unspecified():
    pw = _dim("password_storage")
    assert quality_of(pw, "bcrypt") == ("good", 1.0)
    assert quality_of(pw, "md5") == ("bad", 0.0)
    assert quality_of(pw, "unspecified") == ("unspecified", 0.0)
    assert quality_of(pw, "weirdvalue") == ("unknown", 0.0)


def test_parse_judgement_filters_and_normalizes():
    raw = '{"requirements_met": ["signup", "bogus"], "decisions": {"password_storage": "BCrypt"}}'
    j = parse_judgement(raw, TASK, 0)
    assert j.requirements_met == ["signup"]  # invalid id dropped
    assert j.decisions["password_storage"] == "bcrypt"  # lowercased
    assert j.decisions["auth_mechanism"] == "unspecified"  # missing -> unspecified


def test_parse_judgement_handles_junk():
    j = parse_judgement("not json", TASK, 3)
    assert j.requirements_met == []
    assert all(v == "unspecified" for v in j.decisions.values())
    assert j.extra_scope == []


def test_parse_judgement_extracts_extra_scope():
    raw = '{"requirements_met": [], "decisions": {}, "extra_scope": ["Two_Factor_Auth", " "]}'
    j = parse_judgement(raw, TASK, 0)
    assert j.extra_scope == ["two_factor_auth"]  # lowercased, blanks dropped


def test_analyze_confidently_wrong_decision_scores_zero():
    # All 10 samples consistently choose MD5 — high agreement, but bad quality.
    payload = {
        "requirements_met": [r.id for r in TASK.requirements],
        "decisions": {**GOOD_DECISIONS, "password_storage": "md5"},
    }
    judge = FakeJudge(payload)
    samples = [type("S", (), {"index": i, "content": "x"})() for i in range(10)]
    reqs, dims, _over = asyncio.run(analyze(samples, TASK, judge))

    by_dim = {d.key: d for d in dims}
    pw = by_dim["password_storage"]
    assert pw.agreement == 1.0  # consistent
    assert pw.quality == "bad"
    assert pw.score == 0.0  # agreement × quality(bad) == 0  -> not rewarded


def test_analyze_consistently_omitted_requirement_fails():
    # Every sample meets all requirements EXCEPT email verification.
    met = [r.id for r in TASK.requirements if r.id != "email_verification"]
    judge = FakeJudge({"requirements_met": met, "decisions": GOOD_DECISIONS})
    samples = [type("S", (), {"index": i, "content": "x"})() for i in range(10)]
    reqs, dims, _over = asyncio.run(analyze(samples, TASK, judge))

    assert judge.calls == 10
    by_req = {r.id: r for r in reqs}
    assert by_req["email_verification"].satisfaction == 0.0
    assert by_req["email_verification"].satisfied is False
    assert by_req["signup"].satisfaction == 1.0
    # good decisions still score full
    assert {d.key: d.score for d in dims}["password_storage"] == 1.0


def test_aggregate_dimensions_split_lowers_agreement():
    from feature_spec_design.models import SampleJudgement

    juds = [
        SampleJudgement(index=i, requirements_met=[], decisions={"password_storage": "bcrypt"})
        for i in range(6)
    ] + [
        SampleJudgement(index=i, requirements_met=[], decisions={"password_storage": "argon2"})
        for i in range(6, 10)
    ]
    dims = aggregate_dimensions(juds, TASK, threshold=0.7)
    pw = {d.key: d for d in dims}["password_storage"]
    assert pw.agreement == 0.6  # 6/10
    assert pw.diverged is True  # below 0.7 — instruction did not pin it
    assert pw.top_value == "bcrypt"


def test_aggregate_requirements_rate():
    from feature_spec_design.models import SampleJudgement

    juds = [SampleJudgement(index=i, requirements_met=["signup"], decisions={}) for i in range(7)]
    juds += [SampleJudgement(index=i, requirements_met=[], decisions={}) for i in range(7, 10)]
    reqs = aggregate_requirements(juds, TASK, threshold=0.7)
    by_req = {r.id: r for r in reqs}
    assert by_req["signup"].satisfaction == 0.7
    assert by_req["signup"].satisfied is True


def test_aggregate_overengineering_keeps_consistent_drops_rare():
    from feature_spec_design.models import SampleJudgement

    # 2fa appears in 8/10 (consistent -> candidate-driven), caching in 1/10 (noise).
    juds = []
    for i in range(10):
        extra = []
        if i < 8:
            extra.append("two_factor_auth")
        if i == 0:
            extra.append("caching")
        juds.append(SampleJudgement(index=i, requirements_met=[], decisions={}, extra_scope=extra))

    items = aggregate_overengineering(juds, threshold=0.5)
    labels = {it.label: it for it in items}
    assert "two_factor_auth" in labels  # 0.8 >= 0.5
    assert labels["two_factor_auth"].count == 8
    assert labels["two_factor_auth"].prevalence == 0.8
    assert "caching" not in labels  # 0.1 < 0.5 -> dropped as noise


def test_aggregate_overengineering_counts_once_per_sample():
    from feature_spec_design.models import SampleJudgement

    # duplicate label within one sample must not double-count
    juds = [
        SampleJudgement(
            index=i, requirements_met=[], decisions={}, extra_scope=["social_login", "social_login"]
        )
        for i in range(6)
    ]
    items = aggregate_overengineering(juds, threshold=0.5)
    assert {it.label: it.count for it in items} == {"social_login": 6}


def test_analyze_returns_overengineering():
    payload = {
        "requirements_met": [r.id for r in TASK.requirements],
        "decisions": GOOD_DECISIONS,
        "extra_scope": ["admin_dashboard"],
    }
    judge = FakeJudge(payload)
    samples = [type("S", (), {"index": i, "content": "x"})() for i in range(10)]
    _reqs, _dims, over = asyncio.run(analyze(samples, TASK, judge))
    assert [it.label for it in over] == ["admin_dashboard"]
    assert over[0].count == 10
