"""Consistency: run the judge N times per item and measure dispersion.

High coefficient-of-variation items are flagged — those are where the judge's
verdict is unstable and the rubric/prompt likely needs tightening.
"""

from collections.abc import Sequence

from app.harness.interface import JudgeAdapter
from app.harness.metrics import cv, mean_std

DEFAULT_RUNS = 5
DEFAULT_CV_THRESHOLD = 0.15


async def run_consistency(
    adapter: JudgeAdapter,
    items: Sequence[dict],
    runs: int = DEFAULT_RUNS,
    cv_threshold: float = DEFAULT_CV_THRESHOLD,
) -> dict:
    """``items``: ``[{"problem_index": int, "flaws": [str]}, ...]``."""
    per_item = []
    for item in items:
        recalls: list[float] = []
        weighted: list[float] = []
        for _ in range(runs):
            outcome = await adapter.score(item["problem_index"], item["flaws"])
            recalls.append(outcome.recall)
            weighted.append(outcome.weighted_score)
        r_mean, r_std = mean_std(recalls)
        r_cv = cv(recalls)
        per_item.append(
            {
                "problem_index": item["problem_index"],
                "runs": runs,
                "recall_mean": r_mean,
                "recall_std": r_std,
                "recall_cv": r_cv,
                "weighted_mean": mean_std(weighted)[0],
                "weighted_std": mean_std(weighted)[1],
                "high_variance": r_cv > cv_threshold,
            }
        )
    return {
        "runs": runs,
        "cv_threshold": cv_threshold,
        "items": per_item,
        "high_variance_count": sum(1 for i in per_item if i["high_variance"]),
    }
