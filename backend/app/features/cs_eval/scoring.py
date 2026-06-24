"""Deterministic scoring math + the offline keyword-overlap stub judge.

The README rubric maps a response *type* to a score:
  정확히 맞춤 → +5 · 솔직히 모름 → −2 · 부분적 → 부분 점수(+1~+4) · 허세-오답 → −5.

`score_for_type` / `normalize` are pure and never change between PRs. `classify`
is the PR-A baseline judge (keyword overlap against the rubric's key points) so
the whole grading flow runs offline; PR-B swaps it for the LLM judge behind the
`judge.py` seam while reusing this same scoring math.
"""

from __future__ import annotations

import re

# Discrete buckets from the README rubric.
SCORE_BY_TYPE: dict[str, int] = {"correct": 5, "honest_unknown": -2, "bluff_wrong": -5}
PARTIAL_MIN, PARTIAL_MAX = 1, 4
MIN_PER_Q, MAX_PER_Q = -5, 5

# Phrases that signal an honest "I don't know" (worth −2, not −5).
_UNKNOWN_MARKERS = ("모르", "모름", "잘 모", "기억 안", "don't know", "no idea", "dunno")


def score_for_type(response_type: str, partial_score: int | None = None) -> int:
    """Map a response type to its signed score; clamp partial into +1..+4."""
    if response_type == "partial":
        s = PARTIAL_MIN if partial_score is None else partial_score
        return max(PARTIAL_MIN, min(PARTIAL_MAX, s))
    return SCORE_BY_TYPE.get(response_type, -5)


def normalize(total: int, question_count: int) -> int:
    """Scale the signed total into a 0-100 display score."""
    if question_count <= 0:
        return 0
    lo, hi = MIN_PER_Q * question_count, MAX_PER_Q * question_count
    pct = round((total - lo) / (hi - lo) * 100)
    return max(0, min(100, pct))


def _key_tokens(key_point: str) -> list[str]:
    return [t for t in re.split(r"[\s,/·()]+", key_point) if len(t) >= 2]


def _matches(answer_lower: str, key_point: str) -> bool:
    if key_point.lower() in answer_lower:
        return True
    return any(t.lower() in answer_lower for t in _key_tokens(key_point))


def classify(
    answer_text: str, key_points: list[str]
) -> tuple[str, list[str], list[str], int | None]:
    """Heuristic baseline judge → (response_type, matched, missing, partial_score).

    Distinguishes an honest blank/"모르겠다" (−2) from confident-but-empty
    rambling (−5): the same matched/missing split the LLM judge will later refine.
    """
    answer = (answer_text or "").strip()
    low = answer.lower()
    matched = [kp for kp in key_points if _matches(low, kp)]
    missing = [kp for kp in key_points if kp not in matched]

    said_unknown = any(m in low for m in _UNKNOWN_MARKERS)
    blankish = len(answer) < 10

    if not matched and (said_unknown or blankish):
        return ("honest_unknown", matched, missing, None)
    if key_points and len(matched) == len(key_points):
        return ("correct", matched, missing, None)
    if not matched:
        # Wrote something substantive but hit none of the key points.
        return ("bluff_wrong", matched, missing, None)
    ratio = len(matched) / len(key_points) if key_points else 0.0
    partial = max(PARTIAL_MIN, min(PARTIAL_MAX, round(1 + ratio * 3)))
    return ("partial", matched, missing, partial)
