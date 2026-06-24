"""Endpoint tests for the rejection-eval flow with the LLM mocked."""

import pytest

from app.features.rejection_eval import service
from app.features.rejection_eval.schemas import GenerationOutput, JudgeOutput
from app.features.rejection_eval.topics import TOPIC_COUNT


def _fake_generation() -> GenerationOutput:
    return GenerationOutput(
        items=[
            {"id": "a", "text": "decision a", "is_flawed": True,
             "flaw_type": "wrong_tech", "explanation": "잘못 적용"},
            {"id": "b", "text": "decision b", "is_flawed": False,
             "flaw_type": "none", "explanation": "정상"},
            {"id": "c", "text": "decision c", "is_flawed": True,
             "flaw_type": "wrong_direction", "explanation": "방향성 오류"},
        ]
    )


@pytest.fixture
def mock_llm(monkeypatch):
    async def fake_generate(topic_title, prompt):
        return _fake_generation()

    async def fake_judge(topic_title, items, flagged_ids, reasons):
        return JudgeOutput(report="잘 찾았으나 일부 놓침", bonus_item_ids=[])

    monkeypatch.setattr(service, "generate_design", fake_generate)
    monkeypatch.setattr(service, "judge_attempt", fake_judge)


async def _start_session(client) -> str:
    resp = await client.post("/api/rejection-eval/sessions", json={"candidate_name": "민수"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["topics"]) == TOPIC_COUNT
    return body["session_id"]


async def test_full_flow_scores_precision_recall(client, mock_llm):
    session_id = await _start_session(client)
    base = f"/api/rejection-eval/sessions/{session_id}"

    for idx in range(TOPIC_COUNT):
        gen = await client.post(f"{base}/topics/{idx}/generate", json={"prompt": "구체적 지시"})
        assert gen.status_code == 200
        items = gen.json()["items"]
        # ground truth must not leak to the candidate
        assert all(set(i.keys()) == {"id", "text"} for i in items)
        # flag a (caught) and b (false alarm); miss c
        await client.post(f"{base}/topics/{idx}/submit", json={"flagged_ids": ["a", "b"]})

    score = await client.post(f"{base}/score")
    assert score.status_code == 200
    result = score.json()
    assert result["candidate_name"] == "민수"
    assert result["status"] == "scored"
    # per topic: tp=1, fp=1, fn=1 -> 0.5 across the board, aggregated too
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["f1"] == 0.5
    first = result["topics"][0]
    outcomes = {i["id"]: i["outcome"] for i in first["items"]}
    assert outcomes == {"a": "caught", "b": "false_alarm", "c": "missed"}
    assert first["report"]

    # GET result returns the same scored payload
    fetched = await client.get(f"{base}/result")
    assert fetched.status_code == 200
    assert fetched.json()["f1"] == 0.5


async def test_score_before_submit_is_conflict(client, mock_llm):
    session_id = await _start_session(client)
    base = f"/api/rejection-eval/sessions/{session_id}"
    # generate only topic 0, submit nothing
    await client.post(f"{base}/topics/0/generate", json={"prompt": "x"})
    resp = await client.post(f"{base}/score")
    assert resp.status_code == 409


async def test_unknown_session_is_404(client, mock_llm):
    resp = await client.post(
        "/api/rejection-eval/sessions/does-not-exist/topics/0/generate",
        json={"prompt": "x"},
    )
    assert resp.status_code == 404


async def test_topic_index_out_of_range_is_404(client, mock_llm):
    session_id = await _start_session(client)
    resp = await client.post(
        f"/api/rejection-eval/sessions/{session_id}/topics/9/generate",
        json={"prompt": "x"},
    )
    assert resp.status_code == 404


async def test_result_before_scoring_is_conflict(client, mock_llm):
    session_id = await _start_session(client)
    resp = await client.get(f"/api/rejection-eval/sessions/{session_id}/result")
    assert resp.status_code == 409
