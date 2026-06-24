"""Self-preference bias: does a judge model inflate submissions authored by itself?

Synthetic candidate submissions are authored by a panel of models. Each judge
model scores them all; we measure ``judge_recall - human_recall`` (inflation vs
the human gold) grouped by author model. ``self_preference`` is a judge's mean
inflation on its *own* authored submissions minus its inflation on others'.
"""

from collections.abc import Mapping, Sequence

from app.harness.interface import JudgeAdapter
from app.harness.metrics import mean


async def run_self_preference(
    adapters: Mapping[str, JudgeAdapter],
    synthetic: Sequence[dict],
    human_recall_by_key: Mapping[str, float],
) -> dict:
    """``synthetic``: ``[{"key", "problem_index", "flaws", "author_model"}, ...]``.

    ``adapters``: judge-model-name -> adapter (one per judge model under test).
    ``human_recall_by_key``: gold human recall for each synthetic submission key.
    """
    per_judge: dict[str, dict] = {}

    for judge_model, adapter in adapters.items():
        gaps_by_author: dict[str, list[float]] = {}
        for item in synthetic:
            outcome = await adapter.score(item["problem_index"], item["flaws"])
            gap = outcome.recall - human_recall_by_key[item["key"]]
            gaps_by_author.setdefault(item["author_model"], []).append(gap)

        author_means = {a: mean(g) for a, g in gaps_by_author.items()}
        own = author_means.get(judge_model)
        others = [m for a, m in author_means.items() if a != judge_model]
        self_pref = (own - mean(others)) if (own is not None and others) else None

        per_judge[judge_model] = {
            "mean_gap_by_author": author_means,
            "own_author_gap": own,
            "others_gap": mean(others) if others else None,
            "self_preference": self_pref,
        }

    return {"judges": per_judge}
