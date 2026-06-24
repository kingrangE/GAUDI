"""context-engineering gold fixtures: labels are valid + all 4 harness analyses run on them.

The reliability sweep itself hits a real LLM (offline tool); here a deterministic stub adapter
stands in so the fixtures + the full 4-analysis pipeline are exercised without a key.
"""

import json

import pytest

from app.harness.interface import ScoreOutcome
from app.harness.registry import HarnessTarget, get_target
from app.harness.runner import load_fixtures, run_analyses  # importing registers built-in targets
from feature_context_engineering.projects import list_projects
from feature_context_engineering.rubric import get_rubric

pytestmark = pytest.mark.harness

_TARGET = get_target("context_engineering")  # registered on importing app.harness.runner
_FIXTURES = load_fixtures(_TARGET.fixtures_dir)


def test_gold_labels_are_valid_and_recall_consistent():
    synthetic = json.loads((_TARGET.fixtures_dir / "synthetic_submissions.json").read_text("utf-8"))
    gold = {g["key"]: g for g in _FIXTURES.gold_labels.values()}
    projects = list_projects()

    assert len(synthetic) == len(gold) == 9
    for s in synthetic:
        g = gold[s["key"]]
        criteria = {c.id for c in get_rubric(projects[s["problem_index"]].id)}
        assert set(g["matched_ids"]) <= criteria, f"{s['key']}: unknown criterion id"
        assert g["recall"] == round(len(g["matched_ids"]) / len(criteria), 4), s["key"]
        assert s["flaws"] and isinstance(s["flaws"][0], str)  # CLAUDE.md carried in flaws[0]


class _StubAdapter:
    """Deterministic adapter (claims full coverage) — exercises the pipeline without an LLM."""

    name = "ce-stub"

    def __init__(self, model=None):
        self.model = model

    async def score(self, problem_index, flaws):
        criteria = [c.id for c in get_rubric(list_projects()[problem_index].id)]
        return ScoreOutcome(
            gt_ids=criteria, matched_ids=criteria, recall=1.0, weighted_score=1.0
        )

    async def pairwise(self, problem_index, flaws_a, flaws_b):
        return "tie"


async def test_all_four_analyses_run_on_context_eng_fixtures():
    stub_target = HarnessTarget(
        name="ce-stub", make_adapter=lambda m: _StubAdapter(m), fixtures_dir=_TARGET.fixtures_dir
    )
    res = await run_analyses(stub_target, _FIXTURES, mode="all", runs=2)

    assert set(res) == {"consistency", "agreement", "position_bias", "self_preference"}
    assert len(res["consistency"]["items"]) == 9  # one per submission
    assert "flip_rate" in res["position_bias"]
    assert "kappa" in res["agreement"]
