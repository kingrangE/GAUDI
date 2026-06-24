"""Consensus wrapper: repeat a judge, vote/median, surface dispersion (no LLM)."""

import pytest

from app.judge.consensus import consensus_score, reduce_scores, sample, tally, vote


def _counter_fn(values):
    """An async judge stub that returns ``values`` in order across calls."""

    state = {"i": 0}

    async def judge():
        v = values[state["i"] % len(values)]
        state["i"] += 1
        return v

    return judge


async def test_sample_runs_n_times():
    calls = {"n": 0}

    async def judge():
        calls["n"] += 1
        return "x"

    out = await sample(judge, 4)
    assert calls["n"] == 4
    assert out == ["x", "x", "x", "x"]


async def test_sample_drops_failed_calls():
    state = {"i": 0}

    async def judge():
        state["i"] += 1
        if state["i"] == 2:
            raise RuntimeError("malformed judge output")
        return "ok"

    out = await sample(judge, 3)
    assert out == ["ok", "ok"]  # the raising call is dropped, the rest survive


async def test_sample_rejects_nonpositive_n():
    async def judge():
        return "x"

    with pytest.raises(ValueError):
        await sample(judge, 0)


def test_tally_majority_and_agreement():
    v = tally(["A", "A", "B"])
    assert v.winner == "A"
    assert v.agreement == pytest.approx(2 / 3)
    assert v.counts == {"A": 2, "B": 1}
    assert v.n == 3


def test_tally_unanimous_is_full_agreement():
    v = tally(["tie", "tie", "tie"])
    assert v.winner == "tie"
    assert v.agreement == 1.0


def test_tally_empty_raises():
    with pytest.raises(ValueError):
        tally([])


def test_reduce_scores_median_and_cv_flag_instability():
    c = reduce_scores([80.0, 80.0, 20.0])
    assert c.median == 80.0  # robust to the single outlier run
    assert c.mean == pytest.approx(60.0)
    assert c.cv > 0.3  # an outlier run makes the judge look unstable here
    assert c.n == 3


def test_reduce_scores_stable_has_zero_cv():
    c = reduce_scores([50.0, 50.0, 50.0])
    assert c.median == 50.0
    assert c.cv == 0.0


def test_reduce_scores_empty_raises():
    with pytest.raises(ValueError):
        reduce_scores([])


async def test_vote_reduces_repeated_categorical_judge():
    v = await vote(_counter_fn(["A", "A", "B"]), n=3)
    assert v.winner == "A"
    assert v.n == 3


async def test_consensus_score_reduces_repeated_numeric_judge():
    c = await consensus_score(_counter_fn([90.0, 10.0]), n=2)
    assert c.median == pytest.approx(50.0)
    assert c.cv > 0.0
