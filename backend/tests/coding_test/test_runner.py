"""Real subprocess sandbox behavior (the core untrusted-code execution path).

These spawn actual `python -I` children, so they are the trust anchor for the
runner. Timeouts are kept small to keep the suite fast.
"""

import sys

import pytest

from app.features.coding_test.runner import SubprocessCodeRunner

runner = SubprocessCodeRunner()

_ADD = "def add(a, b):\n    return a + b\n"


def test_correct_value_is_returned():
    result = runner.execute(_ADD, "add", [2, 3])
    assert result.ok is True
    assert result.value == 5


def test_complex_value_round_trips():
    code = "def f(xs):\n    return sorted(xs)\n"
    result = runner.execute(code, "f", [[3, 1, 2]])
    assert result.ok is True
    assert result.value == [1, 2, 3]


def test_candidate_stdout_does_not_corrupt_result():
    code = "def f(x):\n    print('noise')\n    return x * 2\n"
    result = runner.execute(code, "f", [21])
    assert result.ok is True
    assert result.value == 42


def test_exception_is_classified():
    code = "def f(x):\n    return 1 / 0\n"
    result = runner.execute(code, "f", [1])
    assert result.ok is False
    assert result.error.startswith("exception: ZeroDivisionError")


def test_missing_function():
    result = runner.execute("def other():\n    return 1\n", "add", [1, 2])
    assert result.ok is False
    assert result.error == "missing_function"


def test_syntax_error_is_classified():
    result = runner.execute("def f(:\n    pass", "f", [])
    assert result.ok is False
    assert result.error.startswith("exception:")


def test_non_serializable_output():
    code = "def f(x):\n    return {1, 2, 3}\n"  # a set is not JSON-serializable
    result = runner.execute(code, "f", [0])
    assert result.ok is False
    assert result.error == "bad_output"


def test_timeout_is_enforced():
    code = "def f(x):\n    while True:\n        pass\n"
    result = runner.execute(code, "f", [0], timeout_s=1.0)
    assert result.ok is False
    assert result.error == "timeout"


@pytest.mark.skipif(sys.platform != "linux", reason="RLIMIT_AS reliably enforced on Linux")
def test_memory_limit_kills_process():
    code = "def f(x):\n    big = [0] * (10 ** 9)\n    return len(big)\n"
    result = runner.execute(code, "f", [0], timeout_s=5.0, mem_limit_mb=128)
    assert result.ok is False
    assert result.error in {"mle", "crashed", "exception: MemoryError: "}
