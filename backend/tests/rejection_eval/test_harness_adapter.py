"""RejectionEvalAdapter + fixtures, tested with the judge mocked (no LLM).

Mirrors the test_design harness adapter: the live LLM judge is monkeypatched so
the score()/pairwise() mapping and the fixture-derived analysis inputs are
verified deterministically.
"""

import pytest

from app.features.rejection_eval import harness_adapter
from app.features.rejection_eval.harness_adapter import (
    RejectionEvalAdapter,
    build_inputs,
)
from app.features.rejection_eval.schemas import (
    ItemJudgement,
    JudgeOutput,
    PairwiseVerdict,
)

pytestmark = pytest.mark.harness


def _judge_marking_oos(out_of_scope_ids: set[str]):
    """Fake judge_attempt: rule the given item ids out of requirements."""

    async def fake(requirements, items, flagged_ids, reasons, model=None):
        return JudgeOutput(
            report="report",
            judgements=[
                ItemJudgement(item_id=i.id, in_requirements=i.id not in out_of_scope_ids)
                for i in items
            ],
        )

    return fake


async def test_score_is_perfect_when_judge_matches_gold(monkeypatch):
    # problem 0's authoritative gold out-of-scope set is {i6, i7}.
    monkeypatch.setattr(harness_adapter, "judge_attempt", _judge_marking_oos({"i6", "i7"}))
    out = await RejectionEvalAdapter().score(0, [])
    assert set(out.gt_ids) == {"i6", "i7"}
    assert set(out.matched_ids) == {"i6", "i7"}
    assert out.recall == 1.0
    assert out.precision == 1.0
    assert out.weighted_score == 1.0


async def test_score_recall_drops_when_judge_misses_an_oos_item(monkeypatch):
    monkeypatch.setattr(harness_adapter, "judge_attempt", _judge_marking_oos({"i6"}))
    out = await RejectionEvalAdapter().score(0, [])
    assert set(out.matched_ids) == {"i6"}
    assert out.recall == 0.5  # found 1 of 2 gold out-of-scope items
    assert out.precision == 1.0  # the one it flagged is truly out of scope


async def test_score_precision_drops_on_false_out_of_scope(monkeypatch):
    # i1 is an in-requirements item; flagging it is a false positive.
    monkeypatch.setattr(harness_adapter, "judge_attempt", _judge_marking_oos({"i6", "i1"}))
    out = await RejectionEvalAdapter().score(0, [])
    assert set(out.matched_ids) == {"i6"}
    assert out.recall == 0.5
    assert out.precision == 0.5  # 1 of 2 flagged were truly out of scope


async def test_pairwise_returns_judge_winner(monkeypatch):
    async def fake_pairwise(requirements, items, flaws_a, flaws_b, model=None):
        return PairwiseVerdict(winner="B", reason="B가 더 정확히 거부함")

    monkeypatch.setattr(harness_adapter, "judge_pairwise", fake_pairwise)
    winner = await RejectionEvalAdapter().pairwise(0, ["i3"], ["i3", "i6"])
    assert winner == "B"


def test_build_inputs_keys_per_problem_and_has_pairs():
    inputs = build_inputs()
    assert {i["problem_index"] for i in inputs["consistency_items"]} == {0, 1, 2}
    assert {g["problem_index"] for g in inputs["agreement_gold"]} == {0, 1, 2}
    assert all("human" in g for g in inputs["agreement_gold"])
    assert inputs["pairwise_pairs"]  # adjacent submissions form pairs
    assert inputs["human_recall_by_key"]


def test_fixtures_are_internally_consistent():
    inputs = build_inputs()
    problems = harness_adapter._PROBLEMS
    items_by_problem = {pi: {it["id"] for it in p["items"]} for pi, p in problems.items()}

    # gold out-of-scope ids reference real items
    for pi, p in problems.items():
        assert set(p["gold_out_of_scope_ids"]) <= items_by_problem[pi]

    # human-annotated matches are a subset of the authoritative gold
    for g in inputs["agreement_gold"]:
        gold = set(problems[g["problem_index"]]["gold_out_of_scope_ids"])
        assert set(g["human"]["matched_ids"]) <= gold

    # synthetic submissions reference real items and known author models
    panel_authors = set(inputs["panel"]["author_models"])
    for s in inputs["synthetic"]:
        assert set(s["flaws"]) <= items_by_problem[s["problem_index"]]
        assert s["author_model"] in panel_authors
