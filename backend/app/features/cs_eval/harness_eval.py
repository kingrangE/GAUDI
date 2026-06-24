"""cs_eval-native judge-reliability analyses.

The shared ``app.harness`` analyses are flaw/recall-shaped; cs_eval's signature
is the four-way response *type* — and crucially the honest_unknown(−2) vs
bluff_wrong(−5) distinction, which keyword recall can't see (both score ~0).
So these two analyses center the response type, while every statistic is the
shared, unit-tested primitive from ``app.harness.metrics`` (no new math here).

Both take any adapter exposing ``async judge(question_index, answer_text) ->
AnswerJudgement`` (see ``CsEvalAdapter``); tests pass a deterministic stub.
"""

from collections import Counter
from collections.abc import Sequence

from app.harness.metrics import cohen_kappa, cv, mae, mean_std, pearson_r

RESPONSE_TYPES = ("correct", "partial", "honest_unknown", "bluff_wrong")

DEFAULT_RUNS = 5
DEFAULT_CV_THRESHOLD = 0.15


async def run_agreement(adapter, gold: Sequence[dict]) -> dict:
    """Judge vs human labels on a gold set.

    ``gold``: ``[{"question_index", "answer_text",
                  "human": {"response_type", "score"}}, ...]``.
    """
    judge_types: list[str] = []
    human_types: list[str] = []
    judge_scores: list[float] = []
    human_scores: list[float] = []

    for case in gold:
        judgement = await adapter.judge(case["question_index"], case["answer_text"])
        human = case["human"]
        judge_types.append(judgement.response_type)
        human_types.append(human["response_type"])
        judge_scores.append(float(judgement.score))
        human_scores.append(float(human["score"]))

    n = len(gold)
    correct = sum(1 for j, h in zip(judge_types, human_types) if j == h)

    # 4×4 human → judge confusion matrix.
    confusion = {h: {j: 0 for j in RESPONSE_TYPES} for h in RESPONSE_TYPES}
    for j, h in zip(judge_types, human_types):
        confusion[h][j] += 1

    # The dangerous error: confusing an honest "I don't know" with a bluff.
    honest_bluff_confusions = sum(
        1
        for j, h in zip(judge_types, human_types)
        if {j, h} == {"honest_unknown", "bluff_wrong"}
    )

    # Agreement on recognizing honesty, as a binary decision.
    judge_honest = [1 if t == "honest_unknown" else 0 for t in judge_types]
    human_honest = [1 if t == "honest_unknown" else 0 for t in human_types]

    return {
        "n_items": n,
        "type_accuracy": correct / n if n else 0.0,
        "confusion": confusion,
        "honest_bluff_confusions": honest_bluff_confusions,
        "honesty_kappa": cohen_kappa(judge_honest, human_honest),
        "score_mae": mae(judge_scores, human_scores),
        "score_pearson": pearson_r(judge_scores, human_scores),
    }


async def run_consistency(
    adapter,
    items: Sequence[dict],
    runs: int = DEFAULT_RUNS,
    cv_threshold: float = DEFAULT_CV_THRESHOLD,
) -> dict:
    """Run the judge ``runs`` times per item; flag unstable verdicts.

    ``items``: ``[{"question_index", "answer_text"}, ...]``. An item is unstable
    if its response type isn't unanimous across runs, or the score's coefficient
    of variation exceeds ``cv_threshold``.
    """
    per_item = []
    for item in items:
        types: list[str] = []
        scores: list[float] = []
        for _ in range(runs):
            judgement = await adapter.judge(item["question_index"], item["answer_text"])
            types.append(judgement.response_type)
            scores.append(float(judgement.score))

        mode, mode_count = Counter(types).most_common(1)[0]
        type_flip_rate = (runs - mode_count) / runs if runs else 0.0
        s_mean, s_std = mean_std(scores)
        s_cv = cv(scores)
        per_item.append(
            {
                "question_index": item["question_index"],
                "runs": runs,
                "type_mode": mode,
                "type_flip_rate": type_flip_rate,
                "score_mean": s_mean,
                "score_std": s_std,
                "score_cv": s_cv,
                "unstable": type_flip_rate > 0 or s_cv > cv_threshold,
            }
        )

    return {
        "runs": runs,
        "cv_threshold": cv_threshold,
        "items": per_item,
        "unstable_count": sum(1 for i in per_item if i["unstable"]),
    }
