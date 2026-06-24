"""Harness analyses tested with deterministic stub adapters (no LLM)."""

import pytest

from app.harness.agreement import run_agreement
from app.harness.bias_position import run_position_bias
from app.harness.bias_self_pref import run_self_preference
from app.harness.consistency import run_consistency
from app.harness.interface import ScoreOutcome

pytestmark = pytest.mark.harness

GT = ["f1", "f2", "f3"]


class SeqAdapter:
    """Returns recall values from a cycling sequence (ignores inputs)."""

    name = "seq"

    def __init__(self, values):
        self.values = list(values)
        self.i = 0

    async def score(self, problem_index, flaws):
        v = self.values[self.i % len(self.values)]
        self.i += 1
        return ScoreOutcome(gt_ids=GT, recall=v, weighted_score=v)

    async def pairwise(self, problem_index, flaws_a, flaws_b):
        return "tie"


async def test_consistency_flags_high_variance():
    adapter = SeqAdapter([0.0, 1.0, 0.0, 1.0])
    res = await run_consistency(adapter, [{"problem_index": 0, "flaws": ["x"]}], runs=4)
    item = res["items"][0]
    assert item["recall_mean"] == pytest.approx(0.5)
    assert item["recall_cv"] > 0.15
    assert item["high_variance"] is True
    assert res["high_variance_count"] == 1


async def test_consistency_stable_is_not_flagged():
    adapter = SeqAdapter([0.5])
    res = await run_consistency(adapter, [{"problem_index": 0, "flaws": ["x"]}], runs=3)
    assert res["items"][0]["recall_cv"] == 0.0
    assert res["items"][0]["high_variance"] is False


class MapAdapter:
    """Returns a configured ScoreOutcome per problem_index."""

    name = "map"

    def __init__(self, by_pi):
        self.by_pi = by_pi

    async def score(self, problem_index, flaws):
        return self.by_pi[problem_index]

    async def pairwise(self, problem_index, flaws_a, flaws_b):
        return "tie"


async def test_agreement_perfect_match():
    adapter = MapAdapter(
        {
            0: ScoreOutcome(gt_ids=GT, matched_ids=["f1", "f2"], recall=0.67),
            1: ScoreOutcome(gt_ids=GT, matched_ids=["f1"], recall=0.33),
        }
    )
    gold = [
        {"problem_index": 0, "flaws": [], "human": {"matched_ids": ["f1", "f2"], "recall": 0.67}},
        {"problem_index": 1, "flaws": [], "human": {"matched_ids": ["f1"], "recall": 0.33}},
    ]
    res = await run_agreement(adapter, gold)
    assert res["kappa"] == pytest.approx(1.0)
    assert res["mae_recall"] == pytest.approx(0.0)
    assert res["pearson_recall"] == pytest.approx(1.0)
    assert res["n_flaw_decisions"] == 6


async def test_agreement_detects_disagreement():
    # judge over-claims on item 0 (says f3 too) and under-claims on item 1.
    adapter = MapAdapter(
        {
            0: ScoreOutcome(gt_ids=GT, matched_ids=["f1", "f2", "f3"], recall=1.0),
            1: ScoreOutcome(gt_ids=GT, matched_ids=[], recall=0.0),
        }
    )
    gold = [
        {"problem_index": 0, "flaws": [], "human": {"matched_ids": ["f1", "f2"], "recall": 0.67}},
        {"problem_index": 1, "flaws": [], "human": {"matched_ids": ["f1"], "recall": 0.33}},
    ]
    res = await run_agreement(adapter, gold)
    assert res["kappa"] < 1.0
    assert res["mae_recall"] > 0.0


class FixedPairwise:
    """Always names position 'A' the winner -> maximally position-biased."""

    name = "biased"

    async def score(self, problem_index, flaws):
        return ScoreOutcome(gt_ids=GT)

    async def pairwise(self, problem_index, flaws_a, flaws_b):
        return "A"


class ContentPairwise:
    """Prefers the longer flaw list (content) -> order-invariant."""

    name = "fair"

    async def score(self, problem_index, flaws):
        return ScoreOutcome(gt_ids=GT)

    async def pairwise(self, problem_index, flaws_a, flaws_b):
        return "A" if len(flaws_a) >= len(flaws_b) else "B"


async def test_position_bias_detected():
    pairs = [{"problem_index": 0, "flaws_a": ["x"], "flaws_b": ["y"]}]
    res = await run_position_bias(FixedPairwise(), pairs)
    assert res["flip_rate"] == pytest.approx(1.0)


async def test_position_bias_absent_for_content_judge():
    pairs = [{"problem_index": 0, "flaws_a": ["x", "y"], "flaws_b": ["z"]}]
    res = await run_position_bias(ContentPairwise(), pairs)
    assert res["flip_rate"] == 0.0


class StyleAdapter:
    """Inflates recall to 1.0 for submissions containing ``own_marker``."""

    name = "style"

    def __init__(self, own_marker):
        self.own_marker = own_marker

    async def score(self, problem_index, flaws):
        recall = 1.0 if self.own_marker in flaws else 0.0
        return ScoreOutcome(gt_ids=GT, recall=recall)

    async def pairwise(self, problem_index, flaws_a, flaws_b):
        return "tie"


async def test_self_preference_bias_surfaces():
    synthetic = [
        {"key": "s1", "problem_index": 0, "flaws": ["mini-style"], "author_model": "mini"},
        {"key": "s2", "problem_index": 0, "flaws": ["big-style"], "author_model": "big"},
    ]
    human = {"s1": 0.5, "s2": 0.5}
    adapters = {"mini": StyleAdapter("mini-style"), "big": StyleAdapter("big-style")}
    res = await run_self_preference(adapters, synthetic, human)
    assert res["judges"]["mini"]["self_preference"] == pytest.approx(1.0)
    assert res["judges"]["big"]["self_preference"] == pytest.approx(1.0)


# --- end-to-end wiring: real TestDesignAdapter + fixtures, judge LLM mocked ---
# Proves the whole evaluation pipeline (fixtures -> adapter -> scoring -> analyses)
# runs without an API key, so the harness stays runnable/green in CI.


@pytest.fixture
def stub_td_judge(monkeypatch):
    """Patch test_design's judge so the adapter runs deterministically (no LLM):
    match the first ground-truth flaw via candidate 0, and always prefer 'A'."""
    from app.features.test_design import harness_adapter
    from app.features.test_design.schemas import JudgeMatch, JudgeOutput, PairwiseVerdict

    async def fake_submission(problem, flaws, model=None):
        matches = [
            JudgeMatch(
                ground_truth_id=f.id,
                matched=(i == 0),
                candidate_index=0 if i == 0 else None,
                quality=2 if i == 0 else 0,
            )
            for i, f in enumerate(problem.flaws)
        ]
        return JudgeOutput(matches=matches, report="stub")

    async def fake_pairwise(problem, flaws_a, flaws_b, model=None):
        return PairwiseVerdict(winner="A", reason="stub")

    monkeypatch.setattr(harness_adapter, "judge_submission", fake_submission)
    monkeypatch.setattr(harness_adapter, "judge_pairwise", fake_pairwise)


def _load_fixture(name: str):
    import json
    from pathlib import Path

    fixtures = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "features"
        / "test_design"
        / "fixtures"
    )
    return json.loads((fixtures / name).read_text(encoding="utf-8"))


def _pairs_within_problem(synthetic):
    """Build (A, B) pairs from consecutive submissions sharing a problem_index.

    Kept local so this test does not depend on runner.py internals (which are
    feature-specific and may be refactored).
    """
    from itertools import groupby

    pairs = []
    keyed = sorted(synthetic, key=lambda s: s["problem_index"])
    for pi, group in groupby(keyed, key=lambda s: s["problem_index"]):
        subs = list(group)
        for a, b in zip(subs, subs[1:]):
            pairs.append({"problem_index": pi, "flaws_a": a["flaws"], "flaws_b": b["flaws"]})
    return pairs


async def test_harness_pipeline_runs_over_real_fixtures(stub_td_judge):
    from app.features.test_design.harness_adapter import TestDesignAdapter

    synthetic = _load_fixture("synthetic_submissions.json")
    gold_labels = {g["key"]: g for g in _load_fixture("human_gold.json")}
    adapter = TestDesignAdapter()

    items = [{"problem_index": s["problem_index"], "flaws": s["flaws"]} for s in synthetic]
    gold = [
        {
            "problem_index": s["problem_index"],
            "flaws": s["flaws"],
            "human": {
                "matched_ids": gold_labels[s["key"]]["matched_ids"],
                "recall": gold_labels[s["key"]]["recall"],
            },
        }
        for s in synthetic
    ]

    consistency = await run_consistency(adapter, items[:2], runs=2)
    assert consistency["items"][0]["runs"] == 2
    # the stub judge is deterministic -> no run-to-run variance
    assert consistency["high_variance_count"] == 0

    agreement = await run_agreement(adapter, gold[:3])
    assert agreement["n_items"] == 3
    assert -1.0 <= agreement["kappa"] <= 1.0
    assert 0.0 <= agreement["mae_recall"] <= 1.0

    position = await run_position_bias(adapter, _pairs_within_problem(synthetic)[:2])
    # stub always says 'A' -> ordering flips the winner every time
    assert position["flip_rate"] == pytest.approx(1.0)
