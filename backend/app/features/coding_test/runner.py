"""Execute untrusted Python only inside a restricted, disposable container."""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from threading import Event, Thread
from typing import Any, Protocol
from uuid import uuid4

from app.core.config import get_settings

DEFAULT_TIMEOUT_S = 5.0
DEFAULT_MEM_LIMIT_MB = 256
MAX_OUTPUT_BYTES = 1024 * 1024
STARTUP_TIMEOUT_S = 10
_READY = b"GAUDI_READY\n"


@dataclass(frozen=True)
class ExecResult:
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


class SandboxUnavailable(RuntimeError):
    """Infrastructure failure; never grade this as an incorrect candidate answer."""


class DockerCodeRunner:
    def execute(
        self,
        code: str,
        function_name: str,
        args: list,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        mem_limit_mb: int = DEFAULT_MEM_LIMIT_MB,
    ) -> ExecResult:
        name = f"gaudi-sandbox-{uuid4().hex}"
        command = [
            "docker",
            "run",
            "--name",
            name,
            "--pull=never",
            "-i",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--user=65534:65534",
            "--pids-limit=32",
            f"--memory={mem_limit_mb}m",
            f"--memory-swap={mem_limit_mb}m",
            "--cpus=1",
            "--ulimit",
            "fsize=1048576:1048576",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=16m",
            "--log-driver=none",
            get_settings().sandbox_image,
            "python",
            "-I",
            "/sandbox.py",
        ]
        payload = json.dumps(
            {
                "code": code,
                "function_name": function_name,
                "args": args,
                "mem_limit_mb": mem_limit_mb,
            }
        ).encode()
        output = bytearray()
        started, ready = Event(), Event()

        with tempfile.TemporaryFile() as source:
            source.write(payload)
            source.seek(0)
            try:
                proc = subprocess.Popen(
                    command,
                    stdin=source,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
            except OSError as exc:
                raise SandboxUnavailable("Docker sandbox is unavailable") from exc

            def read_output():
                header = proc.stdout.readline(len(_READY) + 1)
                if header == _READY:
                    ready.set()
                else:
                    output.extend(header)
                started.set()
                output.extend(proc.stdout.read(MAX_OUTPUT_BYTES + 1 - len(output)))
                if len(output) > MAX_OUTPUT_BYTES:
                    proc.kill()

            reader = Thread(target=read_output, daemon=True)
            reader.start()
            timed_out = False
            try:
                if not started.wait(STARTUP_TIMEOUT_S):
                    proc.kill()
                    proc.wait()
                    raise SandboxUnavailable("Docker sandbox startup timed out")
                if not ready.is_set():
                    proc.wait(timeout=1)
                    raise SandboxUnavailable("Docker sandbox did not become ready")
                proc.wait(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.kill()
                proc.wait()
            finally:
                # Killing the Docker client alone leaves its container running.
                try:
                    subprocess.run(
                        ["docker", "rm", "--force", name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=10,
                        check=True,
                    )
                except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
                    raise SandboxUnavailable("Cannot confirm sandbox cleanup") from exc
                finally:
                    reader.join(timeout=2)
                    proc.stdout.close()

        if timed_out:
            return ExecResult(False, error="timeout")
        if len(output) > MAX_OUTPUT_BYTES:
            return ExecResult(False, error="output_limit")
        if proc.returncode in (125, 126, 127):
            raise SandboxUnavailable("Docker sandbox image or daemon is unavailable")
        if proc.returncode != 0:
            return ExecResult(False, error="crashed")
        try:
            result = json.loads(output)
            if not isinstance(result, dict) or not isinstance(result.get("ok"), bool):
                raise ValueError("invalid sandbox response")
        except (ValueError, UnicodeDecodeError):
            return ExecResult(False, error="bad_output")
        return ExecResult(result["ok"], result.get("value"), result.get("error"))
