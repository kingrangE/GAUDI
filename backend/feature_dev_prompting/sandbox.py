"""Development prompting uses the same container boundary as the coding test."""

from __future__ import annotations

import json

from app.features.coding_test.runner import DEFAULT_MEM_LIMIT_MB, DockerCodeRunner
from feature_dev_prompting.models import CaseResult, GradingCase


def run_solution(
    code: str, args: list, entry_point: str, *, timeout: float = 2.0, mem_mb: int | None = None
) -> tuple[str, str | None]:
    result = DockerCodeRunner().execute(
        code,
        entry_point,
        args,
        timeout,
        mem_mb or DEFAULT_MEM_LIMIT_MB,
    )
    if result.ok:
        return "ok", json.dumps(result.value, ensure_ascii=False, sort_keys=True)
    return ("timeout" if result.error == "timeout" else "runtime_error"), None


def run_against_tests(
    code: str, tests: list[GradingCase], entry_point: str, *, time_limit: float = 2.0
) -> list[CaseResult]:
    results: list[CaseResult] = []
    for i, tc in enumerate(tests):
        status, got = run_solution(code, tc.args, entry_point, timeout=time_limit)
        passed = status == "ok" and json.loads(got) == json.loads(json.dumps(tc.expected))
        results.append(
            CaseResult(
                index=i,
                hidden=tc.hidden,
                passed=passed,
                status=("pass" if passed else "wrong_answer") if status == "ok" else status,
                expected=None if tc.hidden else json.dumps(tc.expected, ensure_ascii=False),
                got=None if tc.hidden else (got or ""),
            )
        )
    return results
