"""rejection_eval's implementation of the harness `JudgeAdapter`.

Wraps the live LLM judge behind the harness interface so the reliability
analyses (consistency / agreement / position-bias / self-preference) can run
against this feature's judge. A specific judge model can be pinned (for the
self-preference sweep); otherwise the centralized ``settings.llm_model`` is used.

Mapping note — unlike test_design (whose judge matches free-text flaws to a fixed
ground truth), this feature's judge is a per-item **classifier**: for each
generated design item it decides ``in_requirements``. We evaluate THAT decision
against an authoritative human gold of out-of-scope items:

    gt_ids       = the problem's gold out-of-scope item ids (fixed)
    judge oos    = items the judge ruled in_requirements=false
    matched_ids  = judge oos ∩ gt_ids
    recall       = |matched| / |gt_ids|       (judge found the out-of-scope items)
    precision    = |matched| / |judge oos|    (judge's flags were truly out-of-scope)

Items are frozen in ``fixtures/problems.json`` so generation nondeterminism does
not pollute the judge-variance signal — the generator is never called here.
"""

import json
from itertools import groupby
from pathlib import Path

from app.features.rejection_eval.judging import judge_attempt, judge_pairwise
from app.features.rejection_eval.schemas import GeneratedItem
from app.harness.interface import ScoreOutcome

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load(name: str):
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


# Frozen problems, indexed by problem_index. Loaded once at import.
_PROBLEMS: dict[int, dict] = {p["problem_index"]: p for p in _load("problems.json")}


def _problem(problem_index: int) -> dict:
    if problem_index not in _PROBLEMS:
        raise KeyError(f"unknown rejection_eval problem_index: {problem_index}")
    return _PROBLEMS[problem_index]


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


class RejectionEvalAdapter:
    name = "rejection_eval"

    def __init__(self, model: str | None = None):
        self.model = model

    async def score(self, problem_index: int, flaws: list[str]) -> ScoreOutcome:
        problem = _problem(problem_index)
        items = [GeneratedItem(**i) for i in problem["items"]]
        judged = await judge_attempt(
            problem["requirements"], items, flaws, {}, model=self.model
        )
        judge_oos = {j.item_id for j in judged.judgements if not j.in_requirements}
        gt_ids = list(problem["gold_out_of_scope_ids"])
        matched = [gid for gid in gt_ids if gid in judge_oos]
        recall = len(matched) / len(gt_ids) if gt_ids else 1.0
        precision = len(matched) / len(judge_oos) if judge_oos else 1.0
        return ScoreOutcome(
            gt_ids=gt_ids,
            matched_ids=matched,
            recall=recall,
            precision=precision,
            weighted_score=_f1(precision, recall),
            mean_quality=precision,
        )

    async def pairwise(
        self, problem_index: int, flaws_a: list[str], flaws_b: list[str]
    ) -> str:
        problem = _problem(problem_index)
        items = [GeneratedItem(**i) for i in problem["items"]]
        verdict = await judge_pairwise(
            problem["requirements"], items, flaws_a, flaws_b, model=self.model
        )
        return verdict.winner


def _build_pairs(synthetic: list[dict]) -> list[dict]:
    """Adjacent submissions on the same problem become head-to-head pairs."""
    pairs = []
    keyed = sorted(synthetic, key=lambda s: s["problem_index"])
    for pi, group in groupby(keyed, key=lambda s: s["problem_index"]):
        subs = list(group)
        for a, b in zip(subs, subs[1:]):
            pairs.append(
                {"problem_index": pi, "flaws_a": a["flaws"], "flaws_b": b["flaws"]}
            )
    return pairs


def build_inputs() -> dict:
    """Assemble the inputs the harness runner feeds to each analysis.

    The judge here classifies a problem's items (independent of any one
    submission), so consistency and agreement are keyed **per problem**;
    position-bias and self-preference use the synthetic submissions.
    """
    synthetic = _load("synthetic_submissions.json")
    human = {h["problem_index"]: h for h in _load("human_gold.json")}
    panel = _load("panel_models.json")

    consistency_items = [{"problem_index": pi, "flaws": []} for pi in sorted(_PROBLEMS)]
    agreement_gold = [
        {
            "problem_index": pi,
            "flaws": [],
            "human": {
                "matched_ids": human[pi]["matched_ids"],
                "recall": human[pi]["recall"],
            },
        }
        for pi in sorted(_PROBLEMS)
        if pi in human
    ]
    human_recall_by_key = {
        s["key"]: human[s["problem_index"]]["recall"]
        for s in synthetic
        if s["problem_index"] in human
    }
    return {
        "consistency_items": consistency_items,
        "agreement_gold": agreement_gold,
        "pairwise_pairs": _build_pairs(synthetic),
        "synthetic": synthetic,
        "human_recall_by_key": human_recall_by_key,
        "panel": panel,
    }
