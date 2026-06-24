"""Deterministic P/R/F1 scoring tests (no DB, no LLM).

An item must be rejected if it is an injected flaw OR out of scope (not in the
requirements). Scoring takes the union.
"""

from app.features.rejection_eval.scoring import aggregate, score_items


def _item(item_id: str, is_flawed: bool):
    return {
        "id": item_id,
        "text": f"decision {item_id}",
        "is_flawed": is_flawed,
        "flaw_type": "wrong_tech" if is_flawed else "none",
        "explanation": "...",
    }


def test_injected_flaws_caught_is_perfect():
    items = [_item("a", True), _item("b", True), _item("c", False)]
    score = score_items(items, flagged_ids=["a", "b"])
    assert (score["tp"], score["fp"], score["fn"]) == (2, 0, 0)
    assert score["f1"] == 1.0
    outcomes = {i["id"]: i["outcome"] for i in score["items"]}
    assert outcomes == {"a": "caught", "b": "caught", "c": "correct_accept"}


def test_missed_and_false_alarm():
    items = [_item("a", True), _item("b", True), _item("c", False)]
    # caught a, missed b, false alarm on c
    score = score_items(items, flagged_ids=["a", "c"])
    assert (score["tp"], score["fp"], score["fn"]) == (1, 1, 1)
    assert score["precision"] == 0.5
    assert score["recall"] == 0.5
    outcomes = {i["id"]: i["outcome"] for i in score["items"]}
    assert outcomes == {"a": "caught", "b": "missed", "c": "false_alarm"}


def test_out_of_scope_item_is_a_flaw_to_reject():
    # b is technically fine (not injected) but not in the requirements -> must reject
    items = [_item("a", True), _item("b", False)]
    score = score_items(items, flagged_ids=["a", "b"], out_of_scope_ids=["b"])
    assert (score["tp"], score["fp"], score["fn"]) == (2, 0, 0)
    by_id = {i["id"]: i for i in score["items"]}
    assert by_id["a"]["flaw_source"] == "injected"
    assert by_id["b"]["flaw_source"] == "out_of_scope"
    assert by_id["b"]["in_requirements"] is False
    assert {i["id"]: i["outcome"] for i in score["items"]} == {"a": "caught", "b": "caught"}


def test_out_of_scope_not_flagged_is_missed():
    items = [_item("a", False), _item("b", False)]
    score = score_items(items, flagged_ids=[], out_of_scope_ids=["a"])
    assert (score["tp"], score["fp"], score["fn"]) == (0, 0, 1)
    assert score["recall"] == 0.0
    assert {i["id"]: i["outcome"] for i in score["items"]} == {
        "a": "missed",
        "b": "correct_accept",
    }


def test_no_flaws_no_flags_is_perfect():
    items = [_item("a", False), _item("b", False)]
    score = score_items(items, flagged_ids=[])
    assert (score["tp"], score["fp"], score["fn"]) == (0, 0, 0)
    assert score["precision"] == 1.0
    assert score["recall"] == 1.0
    assert score["f1"] == 1.0


def test_no_flaws_with_false_alarm():
    items = [_item("a", False), _item("b", False)]
    score = score_items(items, flagged_ids=["a"])
    assert (score["tp"], score["fp"], score["fn"]) == (0, 1, 0)
    assert score["precision"] == 0.0
    assert score["f1"] == 0.0


def test_aggregate_micro_averages_counts():
    s1 = score_items([_item("a", True), _item("b", False)], flagged_ids=["a"])
    s2 = score_items([_item("c", True), _item("d", True)], flagged_ids=["c"])
    # s1: tp1 fp0 fn0 ; s2: tp1 fp0 fn1  -> micro tp2 fp0 fn1
    precision, recall, f1 = aggregate([s1, s2])
    assert precision == 1.0
    assert recall == 2 / 3
    assert round(f1, 4) == round(2 * 1.0 * (2 / 3) / (1.0 + 2 / 3), 4)
