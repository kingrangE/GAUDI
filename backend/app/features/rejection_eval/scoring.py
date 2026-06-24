"""Deterministic Precision / Recall / F1 scoring.

An item must be rejected if it is **either** an injected wrong design
(`is_flawed`) **or** a decision the functional requirements do not call for
(`out_of_scope`, decided by the judge). The candidate should flag every such
item. Per-item outcomes and metrics are computed deterministically from that
union.
"""

from collections.abc import Iterable, Mapping


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def score_items(
    items: Iterable[Mapping],
    flagged_ids: Iterable[str],
    out_of_scope_ids: Iterable[str] = (),
) -> dict:
    """Classify each item and compute P/R/F1 for one attempt.

    `out_of_scope_ids` are items the judge ruled not grounded in the
    requirements. Returns per-item `flaw_source`/`in_requirements`/`flagged`/
    `outcome` plus `tp`/`fp`/`fn` and `precision`/`recall`/`f1`.
    """
    flagged = set(flagged_ids)
    out_of_scope = set(out_of_scope_ids)
    scored_items: list[dict] = []
    tp = fp = fn = 0

    for item in items:
        is_flagged = item["id"] in flagged
        is_injected = bool(item["is_flawed"])
        is_out_of_scope = item["id"] in out_of_scope
        should_reject = is_injected or is_out_of_scope

        if is_injected:
            flaw_source = "injected"
        elif is_out_of_scope:
            flaw_source = "out_of_scope"
        else:
            flaw_source = "none"

        if should_reject and is_flagged:
            outcome = "caught"
            tp += 1
        elif should_reject and not is_flagged:
            outcome = "missed"
            fn += 1
        elif (not should_reject) and is_flagged:
            outcome = "false_alarm"
            fp += 1
        else:
            outcome = "correct_accept"

        scored_items.append(
            {
                **item,
                "in_requirements": not is_out_of_scope,
                "flaw_source": flaw_source,
                "flagged": is_flagged,
                "outcome": outcome,
            }
        )

    precision, recall, f1 = _prf(tp, fp, fn)
    return {
        "items": scored_items,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def aggregate(attempt_scores: Iterable[Mapping]) -> tuple[float, float, float]:
    """Micro-average P/R/F1 across attempts (sum the confusion counts)."""
    scores = list(attempt_scores)
    tp = sum(s["tp"] for s in scores)
    fp = sum(s["fp"] for s in scores)
    fn = sum(s["fn"] for s in scores)
    return _prf(tp, fp, fn)
