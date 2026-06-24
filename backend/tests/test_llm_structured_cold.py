"""The structured-output judge defaults to COLD (temperature 0.0) for reproducibility."""

from types import SimpleNamespace

from pydantic import BaseModel

from app.llm import structured as structured_mod


class _Out(BaseModel):
    ok: bool


def _fake_client(captured):
    """A stand-in OpenAI client whose ``parse`` records the kwargs it was called with."""

    async def parse(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(parsed=_Out(ok=True)))]
        )

    return SimpleNamespace(
        beta=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=parse)))
    )


async def test_judge_defaults_to_cold(monkeypatch):
    captured = {}
    monkeypatch.setattr(structured_mod, "get_client", lambda: _fake_client(captured))

    out = await structured_mod.complete_structured("sys", "usr", _Out)

    assert out.ok is True
    assert captured["temperature"] == 0.0  # cold judge by default
    assert captured["response_format"] is _Out


async def test_temperature_override_is_honored(monkeypatch):
    captured = {}
    monkeypatch.setattr(structured_mod, "get_client", lambda: _fake_client(captured))

    await structured_mod.complete_structured("sys", "usr", _Out, temperature=0.7)

    assert captured["temperature"] == 0.7


async def test_model_override_passed_through(monkeypatch):
    captured = {}
    monkeypatch.setattr(structured_mod, "get_client", lambda: _fake_client(captured))

    await structured_mod.complete_structured("sys", "usr", _Out, model="gpt-test")

    assert captured["model"] == "gpt-test"
