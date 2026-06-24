"""Deterministic scoring for the test-design evaluation.

Given the judge's per-flaw match decisions (which are the *only* LLM-derived
input), all metrics are computed deterministically and reproducibly here:

- recall    = 결함 발견율 = matched flaws / total ground-truth flaws (headline)
- precision = candidate flaws that hit a real flaw / total candidate flaws
- mean_quality   = average 0-2 quality over matched flaws
- weighted_score = severity-weighted, quality-scaled recall in [0, 1]
                   = Σ_matched w·(quality/2) / Σ_all w

These functions are pure (no LLM, no DB) and unit-tested directly.
"""

from collections.abc import Iterable, Mapping, Sequence

SEVERITY_WEIGHT: dict[str, int] = {"low": 1, "medium": 2, "high": 3}


def _clamp_quality(value: object) -> int:
    try:
        q = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
    return max(0, min(2, q))


def score_submission(
    gt_flaws: Sequence[Mapping],
    candidate_flaws: Sequence[str],
    matches: Iterable[Mapping],
    report: str = "",
) -> dict:
    """Score one problem submission.

    ``gt_flaws``: ground-truth flaws as mappings ``{id, text, severity, category}``.
    ``candidate_flaws``: the candidate's free-text flaw descriptions.
    ``matches``: judge verdicts ``{ground_truth_id, matched, candidate_index, quality}``.

    Returns per-flaw results, the false-positive submissions, raw confusion
    counts (for session-level micro-averaging), and the aggregate metrics.
    """
    gt = list(gt_flaws)
    candidate = list(candidate_flaws)
    match_by_gt = {m["ground_truth_id"]: m for m in matches}

    scored_flaws: list[dict] = []
    matched_count = 0
    quality_sum = 0
    weighted_earned = 0.0
    weighted_total = 0.0
    used_candidate_idx: set[int] = set()

    for flaw in gt:
        weight = SEVERITY_WEIGHT.get(flaw["severity"], 1)
        weighted_total += weight
        match = match_by_gt.get(flaw["id"])
        found = bool(match and match.get("matched"))
        quality = _clamp_quality(match.get("quality")) if found else 0

        matched_text = None
        if found:
            idx = match.get("candidate_index")
            if isinstance(idx, int) and 0 <= idx < len(candidate):
                matched_text = candidate[idx]
                used_candidate_idx.add(idx)
            matched_count += 1
            quality_sum += quality
            weighted_earned += weight * (quality / 2)

        scored_flaws.append(
            {
                "id": flaw["id"],
                "text": flaw["text"],
                "severity": flaw["severity"],
                "category": flaw["category"],
                "found": found,
                "quality": quality,
                "matched_candidate_text": matched_text,
            }
        )

    total = len(gt)
    num_claims = len(candidate)
    tp_candidate = len(used_candidate_idx)
    false_positives = [t for i, t in enumerate(candidate) if i not in used_candidate_idx]

    recall = matched_count / total if total else 1.0
    precision = tp_candidate / num_claims if num_claims else 1.0
    mean_quality = quality_sum / matched_count if matched_count else 0.0
    weighted_score = weighted_earned / weighted_total if weighted_total else 1.0

    return {
        "flaws": scored_flaws,
        "false_positives": false_positives,
        "report": report,
        # raw counts for micro-averaging across a session
        "matched_count": matched_count,
        "total": total,
        "tp_candidate": tp_candidate,
        "num_claims": num_claims,
        "weighted_earned": weighted_earned,
        "weighted_total": weighted_total,
        # per-problem aggregate metrics
        "recall": recall,
        "precision": precision,
        "mean_quality": mean_quality,
        "weighted_score": weighted_score,
    }


def aggregate(problem_scores: Iterable[Mapping]) -> tuple[float, float, float]:
    """Micro-average (recall, precision, weighted_score) across problem scores."""
    scores = list(problem_scores)
    matched = sum(s["matched_count"] for s in scores)
    total = sum(s["total"] for s in scores)
    tp = sum(s["tp_candidate"] for s in scores)
    claims = sum(s["num_claims"] for s in scores)
    earned = sum(s["weighted_earned"] for s in scores)
    weight_total = sum(s["weighted_total"] for s in scores)

    recall = matched / total if total else 1.0
    precision = tp / claims if claims else 1.0
    weighted = earned / weight_total if weight_total else 1.0
    return recall, precision, weighted
