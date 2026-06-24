"""The offline harness runner/registry are feature-agnostic (stub adapter, no LLM)."""

from pathlib import Path

import pytest

from app.harness.interface import ScoreOutcome
from app.harness.registry import HarnessTarget, get_target, list_targets, register_target
from app.harness.runner import Fixtures, run_analyses

pytestmark = pytest.mark.harness


class StubAdapter:
    """Deterministic adapter standing in for any feature's live judge."""

    name = "stub"

    def __init__(self, model=None):
        self.model = model

    async def score(self, problem_index, flaws):
        return ScoreOutcome(gt_ids=["f1", "f2"], matched_ids=["f1"], recall=0.5, weighted_score=0.5)

    async def pairwise(self, problem_index, flaws_a, flaws_b):
        return "tie"


def _fixtures():
    synthetic = [
        {"key": "s1", "problem_index": 0, "flaws": ["a"], "author_model": "m1"},
        {"key": "s2", "problem_index": 0, "flaws": ["b"], "author_model": "m2"},
    ]
    gold_labels = {
        "s1": {"key": "s1", "matched_ids": ["f1"], "recall": 0.5},
        "s2": {"key": "s2", "matched_ids": ["f1"], "recall": 0.5},
    }
    return Fixtures(
        synthetic=synthetic,
        gold_labels=gold_labels,
        panel={"judge_models": ["m1", "m2"]},
    )


async def test_run_analyses_is_feature_agnostic():
    # A stub feature (not test_design) drives all four analyses through the generic runner.
    target = HarnessTarget(
        name="stub", make_adapter=lambda m: StubAdapter(m), fixtures_dir=Path(".")
    )
    res = await run_analyses(target, _fixtures(), mode="all", runs=3)
    assert set(res) == {"consistency", "agreement", "position_bias", "self_preference"}
    assert res["consistency"]["runs"] == 3


def test_register_and_lookup():
    target = HarnessTarget(
        name="stub2", make_adapter=lambda m: StubAdapter(m), fixtures_dir=Path(".")
    )
    register_target(target)
    assert "stub2" in list_targets()
    assert get_target("stub2") is target


def test_get_unknown_target_raises():
    with pytest.raises(KeyError):
        get_target("nope-not-registered")


def test_builtin_test_design_is_registered():
    import app.harness.runner  # noqa: F401  importing registers the built-in targets

    assert "test_design" in list_targets()
