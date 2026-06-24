"""Deterministic P/R/F1 scoring tests (no DB, no LLM)."""

from app.features.rejection_eval.scoring import aggregate, score_items


def _item(item_id: str, is_flawed: bool):
    return {
        "id": item_id,
        "text": f"decision {item_id}",
        "is_flawed": is_flawed,
        "flaw_type": "wrong_tech" if is_flawed else "none",
        "explanation": "...",
    }


def test_all_flaws_caught_is_perfect():
    items = [_item("a", True), _item("b", True), _item("c", False)]
    score = score_items(items, flagged_ids=["a", "b"])
    assert (score["tp"], score["fp"], score["fn"]) == (2, 0, 0)
    assert score["precision"] == 1.0
    assert score["recall"] == 1.0
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
    assert score["f1"] == 0.5
    outcomes = {i["id"]: i["outcome"] for i in score["items"]}
    assert outcomes == {"a": "caught", "b": "missed", "c": "false_alarm"}


def test_zero_flaw_topic_no_flags_is_perfect():
    items = [_item("a", False), _item("b", False)]
    score = score_items(items, flagged_ids=[])
    assert (score["tp"], score["fp"], score["fn"]) == (0, 0, 0)
    assert score["precision"] == 1.0
    assert score["recall"] == 1.0
    assert score["f1"] == 1.0


def test_zero_flaw_topic_with_false_alarm():
    items = [_item("a", False), _item("b", False)]
    score = score_items(items, flagged_ids=["a"])
    assert (score["tp"], score["fp"], score["fn"]) == (0, 1, 0)
    assert score["precision"] == 0.0
    assert score["recall"] == 1.0
    assert score["f1"] == 0.0


def test_bonus_found_reclassifies_false_alarm():
    items = [_item("a", True), _item("b", False)]
    # candidate flags both; b is not an injected flaw but judge rules it a real flaw
    score = score_items(items, flagged_ids=["a", "b"], bonus_ids=["b"])
    assert (score["tp"], score["fp"], score["fn"]) == (2, 0, 0)
    assert score["precision"] == 1.0
    outcomes = {i["id"]: i["outcome"] for i in score["items"]}
    assert outcomes == {"a": "caught", "b": "bonus_found"}


def test_aggregate_micro_averages_counts():
    s1 = score_items([_item("a", True), _item("b", False)], flagged_ids=["a"])
    s2 = score_items([_item("c", True), _item("d", True)], flagged_ids=["c"])
    # s1: tp1 fp0 fn0 ; s2: tp1 fp0 fn1  -> micro tp2 fp0 fn1
    precision, recall, f1 = aggregate([s1, s2])
    assert precision == 1.0
    assert recall == 2 / 3
    assert round(f1, 4) == round(2 * 1.0 * (2 / 3) / (1.0 + 2 / 3), 4)
