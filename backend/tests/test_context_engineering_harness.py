"""context_engineering plugs into the judge-reliability harness (adapter + pairwise, LLM mocked)."""

import pytest

from app.harness.agreement import run_agreement
from app.harness.consistency import run_consistency
from feature_context_engineering import harness_adapter as adapter_mod
from feature_context_engineering.harness_adapter import ContextEngAdapter
from feature_context_engineering.models import CriterionVerdict
from feature_context_engineering.rubric import get_rubric

pytestmark = pytest.mark.harness


def _fake_judge(covered_ids):
    """Return a judge_submission stub that marks ``covered_ids`` covered, the rest not."""

    def _fn(client, project, submission, criteria):
        return [
            CriterionVerdict(
                id=c.id,
                covered=c.id in covered_ids,
                evidence="quote" if c.id in covered_ids else "",
            )
            for c in criteria
        ]

    return _fn


async def test_adapter_maps_coverage_to_score_outcome(monkeypatch):
    adapter = ContextEngAdapter()
    project = adapter._projects[0]
    crit_ids = [c.id for c in get_rubric(project.id)]
    covered = crit_ids[:1]
    monkeypatch.setattr(adapter_mod, "judge_submission", _fake_judge(covered))

    out = await adapter.score(0, ["some CLAUDE.md text"])

    assert out.gt_ids == crit_ids
    assert out.matched_ids == covered
    assert out.recall == round(len(covered) / len(crit_ids), 4)


async def test_adapter_pairwise_returns_winner(monkeypatch):
    adapter = ContextEngAdapter()
    monkeypatch.setattr(adapter_mod, "judge_pairwise", lambda c, p, a, b: "A")

    assert await adapter.pairwise(0, ["doc a"], ["doc b"]) == "A"


async def test_harness_consistency_runs_on_context_eng(monkeypatch):
    adapter = ContextEngAdapter()
    project = adapter._projects[0]
    crit_ids = [c.id for c in get_rubric(project.id)]
    monkeypatch.setattr(adapter_mod, "judge_submission", _fake_judge(crit_ids))  # full coverage

    res = await run_consistency(adapter, [{"problem_index": 0, "flaws": ["doc"]}], runs=3)

    assert res["items"][0]["recall_mean"] == pytest.approx(1.0)
    assert res["items"][0]["recall_cv"] == 0.0  # deterministic judge -> stable


async def test_harness_agreement_runs_on_context_eng(monkeypatch):
    adapter = ContextEngAdapter()
    project = adapter._projects[0]
    crit_ids = [c.id for c in get_rubric(project.id)]
    monkeypatch.setattr(adapter_mod, "judge_submission", _fake_judge(crit_ids))

    gold = [
        {"problem_index": 0, "flaws": ["doc"], "human": {"matched_ids": crit_ids, "recall": 1.0}}
    ]

    res = await run_agreement(adapter, gold)

    assert res["kappa"] == pytest.approx(1.0)  # judge matches human exactly
    assert res["mae_recall"] == pytest.approx(0.0)
