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
