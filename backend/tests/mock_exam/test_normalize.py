"""Per-feature score normalization onto 0–100 (pure logic, no DB/LLM)."""

import pytest

from app.features.mock_exam.normalize import normalize_score


@pytest.mark.parametrize(
    "feature_key, raw_result, expected",
    [
        ("test_design", {"weighted_score": 0.5}, 50.0),
        ("rejection_eval", {"f1": 0.8}, 80.0),
        ("dev_prompting", {"total": 1.0}, 100.0),
        ("spec_design", {"total": 73}, 73.0),
        ("context_engineering", {"total": 91.5}, 91.5),
    ],
)
def test_normalizes_each_feature_to_0_100(feature_key, raw_result, expected):
    assert normalize_score(feature_key, raw_result) == pytest.approx(expected)


def test_clamps_out_of_range_values():
    # A 0–1 feature handed >1 must not exceed 100, and negatives floor at 0.
    assert normalize_score("test_design", {"weighted_score": 1.4}) == 100.0
    assert normalize_score("rejection_eval", {"f1": -0.2}) == 0.0


def test_unknown_feature_raises():
    with pytest.raises(ValueError, match="unknown mock-exam feature"):
        normalize_score("cs_eval", {"total": 50})


def test_missing_field_raises():
    with pytest.raises(ValueError, match="missing required field"):
        normalize_score("spec_design", {"score": 50})


def test_non_numeric_field_raises():
    with pytest.raises(ValueError, match="not numeric"):
        normalize_score("spec_design", {"total": "high"})
    # bool must not sneak through as an int.
    with pytest.raises(ValueError, match="not numeric"):
        normalize_score("dev_prompting", {"total": True})
