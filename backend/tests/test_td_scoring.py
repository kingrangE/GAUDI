"""Pure unit tests for deterministic scoring (no LLM, no DB)."""

from app.features.test_design.scoring import aggregate, score_submission

GT3 = [
    {"id": "f1", "text": "a", "severity": "high", "category": "edge_case"},
    {"id": "f2", "text": "b", "severity": "medium", "category": "validation"},
    {"id": "f3", "text": "c", "severity": "low", "category": "validation"},
]


def _match(gt_id, matched, idx=None, quality=0):
    return {
        "ground_truth_id": gt_id,
        "matched": matched,
        "candidate_index": idx,
        "quality": quality,
    }


def test_full_recall_all_matched_quality_two():
    matches = [
        _match("f1", True, 0, 2),
        _match("f2", True, 1, 2),
        _match("f3", True, 2, 2),
    ]
    s = score_submission(GT3, ["x", "y", "z"], matches)
    assert s["recall"] == 1.0
    assert s["precision"] == 1.0
    assert s["mean_quality"] == 2.0
    assert s["weighted_score"] == 1.0
    assert s["false_positives"] == []


def test_zero_matches():
    matches = [_match("f1", False), _match("f2", False), _match("f3", False)]
    s = score_submission(GT3, ["wrong"], matches)
    assert s["recall"] == 0.0
    assert s["precision"] == 0.0  # one claim, no true positive
    assert s["mean_quality"] == 0.0
    assert s["weighted_score"] == 0.0
    assert s["false_positives"] == ["wrong"]


def test_partial_recall_and_precision_with_false_positives():
    # candidate submitted 3 flaws; only #0 matches the high-severity f1.
    matches = [_match("f1", True, 0, 1), _match("f2", False), _match("f3", False)]
    s = score_submission(GT3, ["right", "noise1", "noise2"], matches)
    assert s["recall"] == 1 / 3
    assert s["precision"] == 1 / 3  # 1 true positive out of 3 claims
    assert s["mean_quality"] == 1.0
    assert s["false_positives"] == ["noise1", "noise2"]


def test_severity_weighting():
    # only the high-severity flaw (weight 3) caught at full quality; weights 3+2+1=6
    matches = [_match("f1", True, 0, 2), _match("f2", False), _match("f3", False)]
    s = score_submission(GT3, ["right"], matches)
    assert s["weighted_score"] == 3 / 6


def test_quality_is_clamped():
    matches = [_match("f1", True, 0, 99), _match("f2", False), _match("f3", False)]
    s = score_submission(GT3, ["right"], matches)
    assert s["flaws"][0]["quality"] == 2


def test_empty_candidate_flaws_precision_is_one():
    matches = [_match("f1", False), _match("f2", False), _match("f3", False)]
    s = score_submission(GT3, [], matches)
    assert s["precision"] == 1.0  # no claims => no false alarms
    assert s["recall"] == 0.0


def test_matched_text_resolved_from_candidate_index():
    matches = [_match("f1", True, 1, 2), _match("f2", False), _match("f3", False)]
    s = score_submission(GT3, ["first", "second"], matches)
    assert s["flaws"][0]["matched_candidate_text"] == "second"
    assert s["false_positives"] == ["first"]


def test_aggregate_micro_average():
    a = score_submission(
        GT3, ["x"], [_match("f1", True, 0, 2), _match("f2", False), _match("f3", False)]
    )
    b = score_submission(
        GT3,
        ["x", "y"],
        [_match("f1", True, 0, 2), _match("f2", True, 1, 2), _match("f3", False)],
    )
    recall, precision, weighted = aggregate([a, b])
    # matched 1+2=3 of total 3+3=6
    assert recall == 3 / 6
    # tp candidates 1+2=3 of claims 1+2=3
    assert precision == 1.0
