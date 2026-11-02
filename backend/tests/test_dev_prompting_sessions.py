"""Stored code runs preserve accepted prompts and reject stale turn requests."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker


async def test_practice_run_appends_one_turn_and_recovers_failed_prompt(client, monkeypatch):
    from feature_dev_prompting import sessions
    from feature_dev_prompting.models import TurnResult

    response = await client.post("/dev-prompting/runs", json={"problem_id": "stepping-stones"})
    rid = response.json()["run_id"]
    calls = []

    def fail(*args):
        calls.append("failed")
        raise RuntimeError("offline")

    monkeypatch.setattr(sessions, "execute_turn", fail)
    path = f"/dev-prompting/runs/{rid}/turns"
    assert (await client.post(path, json={"prompt": "keep me", "turn": 1})).status_code == 503
    assert (await client.post(path, json={"prompt": "different", "turn": 1})).status_code == 409

    def success(problem, turns, prompt, solver):
        calls.append(prompt)
        return TurnResult(
            turn=len(turns) + 1,
            prompt=prompt,
            code="def solution(): return 1",
            passed_count=0,
            total=1,
            solved=False,
            feedback="",
            case_results=[],
        )

    monkeypatch.setattr(sessions, "execute_turn", success)
    for turn, prompt in [(1, "keep me"), (2, "next")]:
        result = await client.post(path, json={"prompt": prompt, "turn": turn})
        assert result.status_code == 200
        assert len(result.json()["turns"]) == turn
    assert calls == ["failed", "keep me", "next"]


async def test_stale_dev_request_cannot_replace_a_saved_turn(engine, monkeypatch):
    from fastapi import HTTPException
    from sqlalchemy import update

    from feature_dev_prompting import sessions

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as first, maker() as second:
        run = sessions.DevRun(problem_id="stepping-stones")
        first.add(run)
        await first.commit()
        cached = await second.get(sessions.DevRun, run.id)
        assert cached.turns == []
        await first.execute(
            update(sessions.DevRun)
            .where(sessions.DevRun.id == run.id)
            .values(turns=[{"prompt": "accepted", "code": "saved code"}])
        )
        await first.commit()

        def unexpected(*args):
            raise AssertionError("must not regenerate an accepted turn")

        monkeypatch.setattr(sessions, "execute_turn", unexpected)
        with pytest.raises(HTTPException) as exc:
            await sessions.run_turn(second, cached, "replacement", 1, object())
        assert exc.value.status_code == 409
