"""Real Docker execution; build backend/sandbox.Dockerfile before running."""

import pytest

from app.features.coding_test.runner import DockerCodeRunner

runner = DockerCodeRunner()

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


def test_memory_limit_kills_process():
    code = "def f(x):\n    big = [0] * (10 ** 9)\n    return len(big)\n"
    result = runner.execute(code, "f", [0], timeout_s=5.0, mem_limit_mb=128)
    assert result.ok is False
    assert result.error in {"mle", "crashed", "exception: MemoryError: "}


def test_host_environment_is_not_forwarded(monkeypatch):
    monkeypatch.setenv("GAUDI_SENTINEL", "must-not-leak")
    result = runner.execute(
        "import os\ndef f():\n    return os.environ.get('GAUDI_SENTINEL')",
        "f",
        [],
    )
    assert result.ok and result.value is None


def test_host_files_are_not_mounted(tmp_path):
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("must-not-leak")
    result = runner.execute(f"def f():\n    return open({str(sentinel)!r}).read()", "f", [])
    assert not result.ok and "FileNotFoundError" in result.error


def test_container_is_nonroot_and_root_filesystem_is_readonly():
    result = runner.execute("import os\ndef f():\n    return os.getuid()", "f", [])
    assert result.ok and result.value == 65534
    result = runner.execute("def f():\n    return open('/escape', 'w').write('x')", "f", [])
    assert not result.ok and ("OSError" in result.error or "PermissionError" in result.error)


def test_network_is_blocked_even_without_python_socket_patch():
    result = runner.execute(
        "import _socket\ndef f():\n    s = _socket.socket()\n"
        "    s.settimeout(0.2)\n    s.connect(('1.1.1.1', 80))\n    return True",
        "f",
        [],
    )
    assert not result.ok and "OSError" in result.error


def test_output_is_bounded():
    result = runner.execute(
        "import os\ndef f():\n    os.write(1, b'x' * (2 * 1024 * 1024))\n    return 1",
        "f",
        [],
    )
    assert not result.ok and result.error == "output_limit"


def test_missing_docker_never_falls_back(monkeypatch):
    from app.features.coding_test.runner import SandboxUnavailable

    def missing(*args, **kwargs):
        raise FileNotFoundError("docker")

    monkeypatch.setattr("app.features.coding_test.runner.subprocess.Popen", missing)
    with pytest.raises(SandboxUnavailable):
        runner.execute(_ADD, "add", [2, 3])


def test_timeout_removes_container_and_descendants():
    import subprocess

    result = runner.execute(
        "import subprocess\ndef f():\n    subprocess.Popen(['sleep', '60'])\n"
        "    while True:\n        pass",
        "f",
        [],
        timeout_s=1,
    )
    assert result.error == "timeout"
    remaining = subprocess.check_output(
        ["docker", "ps", "-aq", "--filter", "name=gaudi-sandbox-"],
        text=True,
    )
    assert remaining.strip() == ""


def test_missing_image_is_infrastructure_failure(monkeypatch):
    from app.core.config import get_settings
    from app.features.coding_test.runner import SandboxUnavailable

    monkeypatch.setattr(get_settings(), "sandbox_image", "gaudi-missing-image:audit")
    with pytest.raises(SandboxUnavailable):
        runner.execute(_ADD, "add", [1, 2])


def test_container_startup_is_not_charged_to_candidate(monkeypatch):
    """A trusted fake process emulates slow container startup, never candidate code."""
    import subprocess
    import sys

    original_popen = subprocess.Popen

    def slow_start(*args, **kwargs):
        return original_popen(
            [
                sys.executable,
                "-c",
                "import time; time.sleep(0.3); print('GAUDI_READY', flush=True); "
                'print(\'{"ok": true, "value": 5}\', flush=True)',
            ],
            stdin=kwargs["stdin"],
            stdout=kwargs["stdout"],
            stderr=kwargs["stderr"],
        )

    monkeypatch.setattr(subprocess, "Popen", slow_start)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: None)
    result = runner.execute("never executed on host", "f", [], timeout_s=0.1)
    assert result.ok and result.value == 5
