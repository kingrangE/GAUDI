"""Sandbox behavior: real subprocess execution, but no LLM involved (deterministic)."""

from feature_dev_prompting.models import GradingCase
from feature_dev_prompting.sandbox import run_against_tests, run_solution

SUM = "def solution(nums):\n    return sum(nums)\n"


def test_run_solution_ok():
    status, got = run_solution(SUM, [[1, 2, 3]], "solution")
    assert status == "ok"
    assert got == "6"


def test_run_solution_runtime_error():
    status, got = run_solution("def solution(nums):\n    raise ValueError('boom')\n",
                               [[1]], "solution")
    assert status == "runtime_error"
    assert got is None


def test_run_solution_timeout():
    status, _ = run_solution("def solution(nums):\n    while True:\n        pass\n",
                             [[1]], "solution", timeout=1.0)
    assert status == "timeout"


def test_run_against_tests_pass_and_redacts_hidden():
    tests = [
        GradingCase(args=[[1, 2, 3]], expected=6, hidden=False),
        GradingCase(args=[[-5]], expected=-5, hidden=True),
    ]
    results = run_against_tests(SUM, tests, "solution", time_limit=5.0)
    assert all(r.passed for r in results)
    assert results[0].got == "6"
    assert results[1].expected is None and results[1].got is None


def test_run_against_tests_wrong_answer():
    tests = [GradingCase(args=[[1, 2, 3]], expected=6)]
    results = run_against_tests("def solution(nums):\n    return 0\n", tests, "solution",
                                time_limit=5.0)
    assert results[0].passed is False
    assert results[0].status == "wrong_answer"


def test_run_against_tests_missing_entry_point_is_runtime_error():
    tests = [GradingCase(args=[[1]], expected=1)]
    results = run_against_tests("def other(nums):\n    return 1\n", tests, "solution",
                                time_limit=5.0)
    assert results[0].status == "runtime_error"
