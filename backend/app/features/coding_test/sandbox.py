"""Untrusted-code sandbox child. Stdlib-only; run as `python -I sandbox.py`.

Reads a JSON job from stdin: {code, function_name, args, mem_limit_mb}.
Applies best-effort OS resource limits, execs the candidate code, calls the
named function with `args`, and writes EXACTLY ONE JSON line to the real
stdout: {"ok": true, "value": <result>} or {"ok": false, "error": <str>}.

This module imports only the standard library on purpose: `python -I` runs in
isolated mode (no cwd/PYTHONPATH on sys.path), so it cannot import `app`.
"""

import contextlib
import io
import json
import sys

# Capture the real stdout up front; candidate prints are redirected away so
# they never corrupt our single result line.
_REAL_STDOUT = sys.stdout


def _emit(payload: dict) -> None:
    _REAL_STDOUT.write(json.dumps(payload))
    _REAL_STDOUT.flush()


def _apply_limits(mem_limit_mb: int) -> None:
    """Best-effort address-space / CPU / file-descriptor caps.

    `resource` is POSIX-only and some limits are not enforced on macOS, so each
    cap is guarded — failure to set a limit must not crash the sandbox.
    """
    try:
        import resource
    except ImportError:
        return

    nbytes = mem_limit_mb * 1024 * 1024
    for res, soft in (
        (getattr(resource, "RLIMIT_AS", None), nbytes),
        (getattr(resource, "RLIMIT_CPU", None), 10),  # CPU-seconds backstop
        (getattr(resource, "RLIMIT_NOFILE", None), 64),
    ):
        if res is None:
            continue
        try:
            hard = resource.getrlimit(res)[1]
            limit = soft if hard == resource.RLIM_INFINITY else min(soft, hard)
            resource.setrlimit(res, (limit, hard))
        except (ValueError, OSError):
            pass


def _disable_network() -> None:
    """Make socket creation fail — blunt but effective against most exfil."""
    try:
        import socket

        def _blocked(*_args, **_kwargs):
            raise OSError("network disabled in sandbox")

        socket.socket = _blocked  # type: ignore[assignment]
    except Exception:
        pass


def main() -> None:
    try:
        job = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        _emit({"ok": False, "error": "bad_job"})
        return

    _apply_limits(int(job.get("mem_limit_mb", 256)))
    _disable_network()

    namespace: dict = {}
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink):
            exec(compile(job["code"], "<candidate>", "exec"), namespace)
    except Exception as exc:  # noqa: BLE001 — report any candidate error
        _emit({"ok": False, "error": f"exception: {type(exc).__name__}: {exc}"[:300]})
        return

    fn = namespace.get(job["function_name"])
    if not callable(fn):
        _emit({"ok": False, "error": "missing_function"})
        return

    try:
        with contextlib.redirect_stdout(sink):
            result = fn(*job["args"])
    except Exception as exc:  # noqa: BLE001
        _emit({"ok": False, "error": f"exception: {type(exc).__name__}: {exc}"[:300]})
        return

    try:
        json.dumps(result)  # ensure the value is serializable before emitting
    except (TypeError, ValueError):
        _emit({"ok": False, "error": "bad_output"})
        return

    _emit({"ok": True, "value": result})


if __name__ == "__main__":
    main()
