"""Deterministic set-scoring unit tests (no DB, no LLM)."""

from app.features.office_prompting.scoring import aggregate, score_id_set


def test_perfect_match():
    s = score_id_set(["C001", "C002", "C003"], ["C003", "C002", "C001"])
    assert s["tp"] == 3 and s["fp"] == 0 and s["fn"] == 0
    assert s["precision"] == 1.0 and s["recall"] == 1.0 and s["f1"] == 1.0
    assert s["correct_count"] == 3 and s["truth_count"] == 3


def test_partial_with_false_alarm_and_miss():
    # predicted {a,b,x}; truth {a,b,c} -> tp=2, fp=1 (x), fn=1 (c)
    s = score_id_set(["a", "b", "x"], ["a", "b", "c"])
    assert (s["tp"], s["fp"], s["fn"]) == (2, 1, 1)
    assert s["precision"] == 2 / 3
    assert s["recall"] == 2 / 3
    assert s["correct_count"] == 2


def test_empty_prediction_is_zero_recall():
    s = score_id_set([], ["a", "b"])
    assert (s["tp"], s["fp"], s["fn"]) == (0, 0, 2)
    assert s["recall"] == 0.0
    assert s["predicted_count"] == 0


def test_duplicates_collapse():
    s = score_id_set(["a", "a", "a"], ["a"])
    assert s["tp"] == 1 and s["fp"] == 0
    assert s["predicted_count"] == 1


def test_aggregate_micro_average():
    a = score_id_set(["a", "b"], ["a", "b"])  # tp2 fp0 fn0
    b = score_id_set(["x"], ["y", "z"])  # tp0 fp1 fn2
    precision, recall, f1 = aggregate([a, b])
    # micro: tp=2, fp=1, fn=2 -> P=2/3, R=2/4=0.5
    assert precision == 2 / 3
    assert recall == 0.5
