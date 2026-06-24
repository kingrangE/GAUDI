"""Deterministic Precision / Recall / F1 scoring.

Per-item outcomes and metrics are computed deterministically from the ground
truth (`is_flawed`). The judge only contributes `bonus_item_ids` — candidate
flags on non-injected items that are genuinely real flaws — which get
reclassified from false alarms to true positives.
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
    bonus_ids: Iterable[str] = (),
) -> dict:
    """Classify each item and compute P/R/F1 for one attempt.

    Returns a dict with per-item `outcome`/`flagged` plus `tp`/`fp`/`fn` and
    `precision`/`recall`/`f1`.
    """
    flagged = set(flagged_ids)
    bonus = set(bonus_ids)
    scored_items: list[dict] = []
    tp = fp = fn = 0

    for item in items:
        is_flagged = item["id"] in flagged
        is_flawed = bool(item["is_flawed"])
        if is_flawed and is_flagged:
            outcome = "caught"
            tp += 1
        elif is_flawed and not is_flagged:
            outcome = "missed"
            fn += 1
        elif (not is_flawed) and is_flagged:
            if item["id"] in bonus:
                outcome = "bonus_found"
                tp += 1
            else:
                outcome = "false_alarm"
                fp += 1
        else:
            outcome = "correct_accept"
        scored_items.append({**item, "flagged": is_flagged, "outcome": outcome})

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
    tp = sum(s["tp"] for s in attempt_scores)
    fp = sum(s["fp"] for s in attempt_scores)
    fn = sum(s["fn"] for s in attempt_scores)
    return _prf(tp, fp, fn)
