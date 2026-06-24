"""Normalize each mock-exam feature's native score onto a 0–100 scale.

Each of the five features scores on its own scale; the admin console needs one
comparable number per feature plus an overall. Normalization lives here, in one
place, so the (separately built) mock-exam orchestration just hands us the
feature's raw result blob and a feature_key.

Native shapes (see each feature's scoring/models):
- test_design        : weighted_score in [0, 1]      -> ×100
- rejection_eval     : f1            in [0, 1]        -> ×100
- dev_prompting      : total         in [0, 1]        -> ×100  (ScoreBreakdown)
- spec_design        : total         in [0, 100]      -> as-is  (SpecScore)
- context_engineering: total         in [0, 100]      -> as-is  (EvaluationReport)
"""

from __future__ import annotations

from app.features.mock_exam.candidates import is_mock_exam_feature

# feature_key -> (field name in raw_result, multiplier to reach 0–100)
_FIELD_AND_SCALE: dict[str, tuple[str, float]] = {
    "test_design": ("weighted_score", 100.0),
    "rejection_eval": ("f1", 100.0),
    "dev_prompting": ("total", 100.0),
    "spec_design": ("total", 1.0),
    "context_engineering": ("total", 1.0),
}


def normalize_score(feature_key: str, raw_result: dict) -> float:
    """Return a 0–100 score for the feature, clamped to range.

    Raises ValueError for an unknown feature_key or a missing/non-numeric field
    so a malformed recording fails loudly rather than silently scoring 0.
    """
    if not is_mock_exam_feature(feature_key):
        raise ValueError(f"unknown mock-exam feature: {feature_key!r}")

    field, scale = _FIELD_AND_SCALE[feature_key]
    if not isinstance(raw_result, dict) or field not in raw_result:
        raise ValueError(
            f"{feature_key!r} result missing required field {field!r}"
        )

    value = raw_result[field]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{feature_key!r} field {field!r} is not numeric: {value!r}")

    return max(0.0, min(100.0, float(value) * scale))
