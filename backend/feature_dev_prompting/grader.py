"""Scoring: pass-rate component (해결 여부) + understanding component (이해도, turn efficiency).

Understanding is proxied by how few turns it took to solve; prompt-quality scoring is an
open question (see SPEC) and intentionally not part of the core path yet.
"""

from __future__ import annotations

from feature_dev_prompting.models import CaseResult, ScoreBreakdown, TurnResult

PASS_WEIGHT = 70.0
UNDERSTANDING_WEIGHT = 30.0


def summarize_run(case_results: list[CaseResult]) -> tuple[int, int]:
    """Return (passed_count, total)."""

    return sum(1 for c in case_results if c.passed), len(case_results)


def evaluation_score(turns: list[TurnResult]) -> ScoreBreakdown:
    """Combine the best pass-rate across turns with a turn-efficiency bonus."""

    if not turns:
        return ScoreBreakdown(
            total=0.0, pass_score=0.0, understanding_score=0.0,
            best_pass_rate=0.0, solved=False, solved_turn=None,
        )

    rates = [(t.passed_count / t.total) if t.total else 0.0 for t in turns]
    best = max(rates)
    solved_turn = next((t.turn for t in turns if t.total and t.passed_count == t.total), None)
    solved = solved_turn is not None

    pass_score = round(best * PASS_WEIGHT, 1)
    efficiency = max(0.4, 1.0 - 0.2 * (solved_turn - 1)) if solved else 0.0
    understanding_score = round(efficiency * UNDERSTANDING_WEIGHT, 1)

    return ScoreBreakdown(
        total=round(pass_score + understanding_score, 1),
        pass_score=pass_score,
        understanding_score=understanding_score,
        best_pass_rate=round(best, 4),
        solved=solved,
        solved_turn=solved_turn,
    )
