"""Run a candidate-completed function against test cases in a constrained subprocess.

Programmers-style: we exec the candidate code, call `entry_point(*args)`, and compare the
JSON-serialized return value to the expected value. MVP isolation: separate process +
wall-clock timeout + (POSIX) CPU/optional memory rlimits. Stronger isolation (Docker,
seccomp, network off) is an open question — see SPEC.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

from feature_dev_prompting.models import CaseResult, GradingCase

try:
    import resource
except ImportError:  # pragma: no cover - non-POSIX
    resource = None

# Loads the candidate file, calls entry(*args) with args read as JSON from stdin,
# and writes the JSON-serialized return value to stdout.
_HARNESS = (
    "import json, sys\n"
    "ns = {}\n"
    "with open(sys.argv[1], encoding='utf-8') as _f:\n"
    "    exec(compile(_f.read(), sys.argv[1], 'exec'), ns)\n"
    "args = json.loads(sys.stdin.read())\n"
    "result = ns[sys.argv[2]](*args)\n"
    "sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True))\n"
)


def _preexec(cpu_sec: int, mem_mb: int | None):
    def apply() -> None:
        if resource is None:
            return
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_sec, cpu_sec))
        except (ValueError, OSError):
            pass
        if mem_mb:
            limit = mem_mb * 1024 * 1024
            try:
                resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
            except (ValueError, OSError):
                pass

    return apply


def run_solution(code: str, args: list, entry_point: str, *, timeout: float = 2.0,
                 mem_mb: int | None = None) -> tuple[str, str | None]:
    """Execute `entry_point(*args)` from `code`. Returns (status, json_result_or_None).

    status ∈ {"ok", "runtime_error", "timeout"}.
    """

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        path = f.name
    preexec = _preexec(int(timeout) + 1, mem_mb) if os.name == "posix" else None
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _HARNESS, path, entry_point],
            input=json.dumps(args),
            capture_output=True,
            text=True,
            timeout=timeout,
            preexec_fn=preexec,
        )
    except subprocess.TimeoutExpired:
        return "timeout", None
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    if proc.returncode != 0:
        return "runtime_error", None
    return "ok", proc.stdout


def _matches(got_json: str | None, expected) -> bool:
    if got_json is None:
        return False
    try:
        got = json.loads(got_json)
    except json.JSONDecodeError:
        return False
    return got == json.loads(json.dumps(expected))


def run_against_tests(code: str, tests: list[GradingCase], entry_point: str, *,
                      time_limit: float = 2.0) -> list[CaseResult]:
    """Run `code` against every case and return per-case results."""

    results: list[CaseResult] = []
    for i, tc in enumerate(tests):
        status, got = run_solution(code, tc.args, entry_point, timeout=time_limit)
        passed = status == "ok" and _matches(got, tc.expected)
        if status == "ok":
            label = "pass" if passed else "wrong_answer"
        else:
            label = status
        results.append(
            CaseResult(
                index=i,
                hidden=tc.hidden,
                passed=passed,
                status=label,
                expected=None if tc.hidden else json.dumps(tc.expected, ensure_ascii=False),
                got=None if tc.hidden else (got if got is not None else ""),
            )
        )
    return results
