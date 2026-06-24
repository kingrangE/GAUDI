"""Pure grading logic: comparison + pass/fail counting (no subprocess)."""

from app.features.coding_test.grading import CaseOutcome, compare, run_test_cases
from app.features.coding_test.runner import ExecResult


class _ScriptedRunner:
    """Returns pre-set ExecResults in call order — isolates counting logic."""

    def __init__(self, results):
        self._results = list(results)
        self._i = 0

    def execute(self, *_args, **_kwargs):
        result = self._results[self._i]
        self._i += 1
        return result


# --- compare -----------------------------------------------------------------
def test_compare_exact():
    assert compare([0, 1], [0, 1], "exact") is True
    assert compare([1, 0], [0, 1], "exact") is False
    assert compare(True, True, "exact") is True


def test_compare_unordered_outer_and_inner():
    actual = [["tan", "nat"], ["bat"], ["eat", "tea", "ate"]]
    expected = [["eat", "ate", "tea"], ["bat"], ["nat", "tan"]]
    assert compare(actual, expected, "unordered") is True


def test_compare_unordered_detects_real_difference():
    assert compare([["a", "b"]], [["a", "c"]], "unordered") is False


# --- run_test_cases ----------------------------------------------------------
def test_run_test_cases_counts_outcomes():
    cases = [([1], 1), ([2], 2), ([3], 3)]
    runner = _ScriptedRunner(
        [
            ExecResult(ok=True, value=1),  # correct
            ExecResult(ok=True, value=99),  # wrong answer
            ExecResult(ok=False, error="timeout"),  # runtime failure
        ]
    )
    outcomes = run_test_cases(runner, "code", "f", cases, "exact")
    assert outcomes == [
        CaseOutcome(passed=True),
        CaseOutcome(passed=False, error="wrong_answer"),
        CaseOutcome(passed=False, error="timeout"),
    ]


def test_run_test_cases_all_pass():
    cases = [([1], 1), ([2], 2)]
    runner = _ScriptedRunner([ExecResult(ok=True, value=1), ExecResult(ok=True, value=2)])
    outcomes = run_test_cases(runner, "code", "f", cases, "exact")
    assert all(o.passed for o in outcomes)
