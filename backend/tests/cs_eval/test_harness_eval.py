"""cs_eval judge-reliability analyses, tested with deterministic stub judges.

No real LLM: a stub adapter returns canned ``AnswerJudgement``s so the wiring of
``run_agreement`` / ``run_consistency`` (and their reuse of ``app.harness.metrics``)
is verified offline. One opt-in integration test exercises the real adapter.
"""

import os

import pytest

from app.features.cs_eval.harness_eval import run_agreement, run_consistency
from app.features.cs_eval.judge import AnswerJudgement

pytestmark = pytest.mark.harness


def _gold(question_index: int, response_type: str, score: int) -> dict:
    return {
        "question_index": question_index,
        "answer_text": "a",
        "human": {"response_type": response_type, "score": score},
    }


def _judgement(response_type: str, score: int) -> AnswerJudgement:
    return AnswerJudgement(
        response_type=response_type,
        score=score,
        matched_keywords=[],
        missing_keywords=[],
        rationale="stub",
    )


class MapAdapter:
    """Maps each question_index to a fixed canned judgement (ignores answer)."""

    def __init__(self, by_index: dict):
        self.by_index = by_index

    async def judge(self, question_index: int, answer_text: str) -> AnswerJudgement:
        rt, sc = self.by_index[question_index]
        return _judgement(rt, sc)


class SeqAdapter:
    """Cycles through a sequence of (type, score) per call — for consistency runs."""

    def __init__(self, seq):
        self.seq = list(seq)
        self.i = 0

    async def judge(self, question_index: int, answer_text: str) -> AnswerJudgement:
        rt, sc = self.seq[self.i % len(self.seq)]
        self.i += 1
        return _judgement(rt, sc)


# --- agreement -------------------------------------------------------------


async def test_agreement_perfect_when_judge_matches_humans():
    gold = [_gold(0, "correct", 5), _gold(1, "honest_unknown", -2)]
    adapter = MapAdapter({0: ("correct", 5), 1: ("honest_unknown", -2)})

    result = await run_agreement(adapter, gold)

    assert result["type_accuracy"] == 1.0
    assert result["honesty_kappa"] == 1.0
    assert result["score_mae"] == 0.0
    assert result["honest_bluff_confusions"] == 0


async def test_agreement_surfaces_honest_bluff_confusion():
    # Human says honest "I don't know"; the judge wrongly calls it a bluff.
    gold = [_gold(0, "honest_unknown", -2), _gold(1, "correct", 5)]
    adapter = MapAdapter({0: ("bluff_wrong", -5), 1: ("correct", 5)})

    result = await run_agreement(adapter, gold)

    assert result["type_accuracy"] == 0.5  # only item 1 matches
    assert result["honest_bluff_confusions"] == 1
    assert result["score_mae"] > 0
    # judge labeled nothing honest while a human did → kappa below perfect
    assert result["honesty_kappa"] < 1.0
    assert result["confusion"]["honest_unknown"]["bluff_wrong"] == 1


# --- consistency -----------------------------------------------------------


async def test_consistency_flags_unstable_response_type():
    # Same item judged 4×, type flips between runs → unstable.
    adapter = SeqAdapter([("correct", 5), ("partial", 3), ("correct", 5), ("partial", 3)])
    items = [{"question_index": 0, "answer_text": "x"}]

    result = await run_consistency(adapter, items, runs=4)

    item = result["items"][0]
    assert item["type_flip_rate"] > 0
    assert item["unstable"] is True
    assert result["unstable_count"] == 1


async def test_consistency_stable_when_verdict_unanimous():
    adapter = SeqAdapter([("correct", 5)])  # always the same
    items = [{"question_index": 0, "answer_text": "x"}]

    result = await run_consistency(adapter, items, runs=5)

    item = result["items"][0]
    assert item["type_flip_rate"] == 0.0
    assert item["type_mode"] == "correct"
    assert item["score_cv"] == 0.0
    assert item["unstable"] is False
    assert result["unstable_count"] == 0


# --- integration (opt-in, real LLM) ---------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="no OPENAI_API_KEY")
async def test_real_adapter_runs_agreement_end_to_end():
    from app.features.cs_eval.harness_adapter import CsEvalAdapter

    gold = [
        {
            "question_index": 1,
            "answer_text": "솔직히 잘 모르겠습니다.",
            "human": {"response_type": "honest_unknown", "score": -2},
        }
    ]
    result = await run_agreement(CsEvalAdapter(), gold)
    assert result["n_items"] == 1
    assert 0.0 <= result["type_accuracy"] <= 1.0
