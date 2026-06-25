"""Generator fans out N concurrent samples at the given temperature. LLM is mocked."""

import asyncio
import threading

import pytest

from feature_spec_design.generator import generate_samples
from feature_spec_design.tasks import get_task

DESIGN = "결정:\n- 언어/프레임워크: FastAPI\n- DB: PostgreSQL\n구현 스케치 ..."


class FakeGenClient:
    """Returns a fixed design; records the temperature each call received."""

    def __init__(self, content=DESIGN):
        self._content = content
        self.temperatures = []
        self._lock = threading.Lock()

    def complete(self, system, user, *, temperature=None):
        with self._lock:
            self.temperatures.append(temperature)
        return self._content


def test_generate_samples_runs_n_and_indexes():
    client = FakeGenClient()
    samples = asyncio.run(generate_samples(client, "지시", n=5, temperature=1.6))

    assert len(samples) == 5
    assert [s.index for s in samples] == [0, 1, 2, 3, 4]
    assert all(s.content == DESIGN for s in samples)
    # extreme temperature is forwarded to every call
    assert client.temperatures == [1.6] * 5


def test_generate_samples_sends_only_instruction_not_brief():
    # Linchpin: the generator must see ONLY the candidate's instruction, never the task brief.
    # Leaking the brief lets the model solve the task regardless of the instruction.
    task = get_task("login-signup")

    captured = {}

    class Capturing:
        def complete(self, system, user, *, temperature=None):
            captured["user"] = user
            return DESIGN

    asyncio.run(generate_samples(Capturing(), "PostgreSQL 사용", n=1, temperature=1.0))
    assert task.brief not in captured["user"]
    assert "PostgreSQL 사용" in captured["user"]


def test_generate_samples_rejects_nonpositive_n():
    with pytest.raises(ValueError):
        asyncio.run(generate_samples(FakeGenClient(), "x", n=0, temperature=1.0))
