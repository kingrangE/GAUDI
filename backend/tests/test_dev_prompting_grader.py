"""Scoring logic — pure and deterministic, no LLM or subprocess."""

from feature_dev_prompting.grader import evaluation_score, summarize_run
from feature_dev_prompting.models import CaseResult, TurnResult


def _turn(turn: int, passed: int, total: int) -> TurnResult:
    return TurnResult(
        turn=turn, prompt="p", code="c", passed_count=passed, total=total,
        solved=(passed == total), feedback="", case_results=[],
    )


def test_summarize_run_counts_passes():
    crs = [
        CaseResult(index=0, hidden=False, passed=True, status="pass"),
        CaseResult(index=1, hidden=True, passed=False, status="wrong_answer"),
    ]
    assert summarize_run(crs) == (1, 2)


def test_score_solved_first_turn_is_perfect():
    s = evaluation_score([_turn(1, 3, 3)])
    assert s.solved and s.solved_turn == 1
    assert s.pass_score == 70.0
    assert s.understanding_score == 30.0
    assert s.total == 100.0


def test_score_solved_later_turn_lowers_understanding():
    s = evaluation_score([_turn(1, 1, 3), _turn(2, 3, 3)])
    assert s.solved and s.solved_turn == 2
    assert s.best_pass_rate == 1.0
    assert s.understanding_score == 24.0  # efficiency 0.8 * 30


def test_score_unsolved_uses_best_pass_rate_only():
    s = evaluation_score([_turn(1, 2, 4)])
    assert not s.solved and s.solved_turn is None
    assert s.best_pass_rate == 0.5
    assert s.pass_score == 35.0
    assert s.understanding_score == 0.0


def test_score_empty_turns():
    s = evaluation_score([])
    assert s.total == 0.0 and not s.solved and s.solved_turn is None
