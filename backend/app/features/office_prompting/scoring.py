"""Deterministic set-based scoring for office-prompting.

The candidate's prompt makes the LLM return a set of ids; we compare that set
to the problem's precomputed ground-truth set. No judge LLM — scoring is pure
set arithmetic. Reuses the generic confusion-count helpers from rejection_eval.
"""

from collections.abc import Iterable

from app.features.rejection_eval.scoring import _prf, aggregate

__all__ = ["score_id_set", "aggregate"]


def score_id_set(predicted_ids: Iterable[str], truth_ids: Iterable[str]) -> dict:
    """Compare a predicted id set to the ground-truth set.

    tp = correctly found, fp = wrongly included, fn = missed. Returns per-attempt
    counts + Precision/Recall/F1 and the candidate-facing ``correct_count``.
    """
    pred = set(predicted_ids)
    truth = set(truth_ids)
    tp = len(pred & truth)
    fp = len(pred - truth)
    fn = len(truth - pred)
    precision, recall, f1 = _prf(tp, fp, fn)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "correct_count": tp,
        "predicted_count": len(pred),
        "truth_count": len(truth),
    }
