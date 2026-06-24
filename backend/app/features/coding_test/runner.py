"""Pluggable code execution: the `CodeRunner` interface + a subprocess impl.

The MVP runs untrusted candidate Python in a sandboxed child process (hard
wall-clock timeout, `resource` limits, no network, temp cwd). The interface is
the seam: a Docker/Piston-backed runner can replace `SubprocessCodeRunner`
later without touching grading or the API.

SECURITY: the subprocess sandbox is defense-in-depth, NOT airtight isolation.
It suits a proctored/trusted-candidate demo; never expose it to the open
internet as-is. See backend/CLAUDE.md.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

# Standalone sandbox script (stdlib-only) invoked by path so it runs under
# `python -I` (isolated mode strips cwd/PYTHONPATH, so it must not import `app`).
_SANDBOX_SCRIPT = str(Path(__file__).parent / "sandbox.py")

DEFAULT_TIMEOUT_S = 5.0
DEFAULT_MEM_LIMIT_MB = 256


@dataclass(frozen=True)
class ExecResult:
    """Outcome of running the candidate function once for a single case.

    `ok` means the function returned a JSON-serializable value (in `value`).
    `error` classifies a failure: "timeout" | "mle" | "missing_function" |
    "bad_output" | "exception: <Type>: <msg>" | "crashed".
    """

    ok: bool
    value: Any = None
    error: str | None = None


class CodeRunner(Protocol):
    def execute(
        self,
        code: str,
        function_name: str,
        args: list,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        mem_limit_mb: int = DEFAULT_MEM_LIMIT_MB,
    ) -> ExecResult: ...


class SubprocessCodeRunner:
    """Runs each case in an isolated `python -I` subprocess via sandbox.py."""

    def execute(
        self,
        code: str,
        function_name: str,
        args: list,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        mem_limit_mb: int = DEFAULT_MEM_LIMIT_MB,
    ) -> ExecResult:
        payload = json.dumps(
            {
                "code": code,
                "function_name": function_name,
                "args": args,
                "mem_limit_mb": mem_limit_mb,
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            try:
                proc = subprocess.run(
                    [sys.executable, "-I", _SANDBOX_SCRIPT],
                    input=payload,
                    capture_output=True,
                    text=True,
                    timeout=timeout_s,
                    cwd=tmp,
                )
            except subprocess.TimeoutExpired:
                return ExecResult(ok=False, error="timeout")

        line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
        if not line:
            # No structured output → killed by a resource limit or crashed.
            err = "mle" if proc.returncode and proc.returncode < 0 else "crashed"
            return ExecResult(ok=False, error=err)
        try:
            out = json.loads(line)
        except json.JSONDecodeError:
            return ExecResult(ok=False, error="crashed")

        if out.get("ok"):
            return ExecResult(ok=True, value=out.get("value"))
        return ExecResult(ok=False, error=out.get("error") or "crashed")
