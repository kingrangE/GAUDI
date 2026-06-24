"""Human–judge agreement on a single-annotator gold set.

Per-flaw match decisions are compared via Cohen's kappa; aggregate recall is
compared via MAE and Pearson correlation. The human gold is labeled with the
same rubric, so disagreement isolates the judge's error.
"""

from collections.abc import Sequence

from app.harness.interface import JudgeAdapter
from app.harness.metrics import cohen_kappa, mae, pearson_r


async def run_agreement(adapter: JudgeAdapter, gold: Sequence[dict]) -> dict:
    """``gold``: ``[{"problem_index", "flaws", "human": {"matched_ids", "recall"}}, ...]``."""
    judge_flaw_labels: list[int] = []
    human_flaw_labels: list[int] = []
    judge_recalls: list[float] = []
    human_recalls: list[float] = []

    for case in gold:
        outcome = await adapter.score(case["problem_index"], case["flaws"])
        human = case["human"]
        human_matched = set(human["matched_ids"])
        judge_matched = set(outcome.matched_ids)
        for gt_id in outcome.gt_ids:
            judge_flaw_labels.append(1 if gt_id in judge_matched else 0)
            human_flaw_labels.append(1 if gt_id in human_matched else 0)
        judge_recalls.append(outcome.recall)
        human_recalls.append(human["recall"])

    return {
        "n_items": len(gold),
        "n_flaw_decisions": len(judge_flaw_labels),
        "kappa": cohen_kappa(judge_flaw_labels, human_flaw_labels),
        "mae_recall": mae(judge_recalls, human_recalls),
        "pearson_recall": pearson_r(judge_recalls, human_recalls),
    }
