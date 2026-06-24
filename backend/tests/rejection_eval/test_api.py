"""Endpoint tests for the rejection-eval flow with the LLM mocked."""

import pytest

from app.features.rejection_eval import service
from app.features.rejection_eval.schemas import GenerationOutput, ItemJudgement, JudgeOutput
from app.features.rejection_eval.topics import TOPIC_COUNT


def _fake_generation() -> GenerationOutput:
    return GenerationOutput(
        items=[
            {"id": "a", "text": "decision a", "is_flawed": True,
             "flaw_type": "wrong_tech", "explanation": "잘못 적용"},
            {"id": "b", "text": "decision b", "is_flawed": False,
             "flaw_type": "none", "explanation": "정상"},
            {"id": "c", "text": "decision c", "is_flawed": False,
             "flaw_type": "none", "explanation": "정상"},
        ]
    )


@pytest.fixture
def mock_llm(monkeypatch):
    async def fake_generate(topic_title, prompt):
        return _fake_generation()

    async def fake_judge(requirements, items, flagged_ids, reasons):
        # b is not in the requirements -> out of scope; a, c are grounded.
        return JudgeOutput(
            report="잘 찾았으나 일부 놓침",
            judgements=[
                ItemJudgement(item_id="a", in_requirements=True),
                ItemJudgement(item_id="b", in_requirements=False),
                ItemJudgement(item_id="c", in_requirements=True),
            ],
        )

    monkeypatch.setattr(service, "generate_design", fake_generate)
    monkeypatch.setattr(service, "judge_attempt", fake_judge)


async def _start_session(client) -> str:
    # No candidate name is sent — sessions are anonymous.
    resp = await client.post("/api/rejection-eval/sessions", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["candidate_name"] == "익명"
    assert len(body["topics"]) == TOPIC_COUNT
    # requirements (the "문제") are sent to the candidate
    assert isinstance(body["topics"][0]["requirements"], list)
    assert body["topics"][0]["requirements"]
    return body["session_id"]


async def test_single_topic_flow_unions_injected_and_out_of_scope(client, mock_llm):
    # The candidate picks and completes ONE topic (topic 0), then scores.
    session_id = await _start_session(client)
    base = f"/api/rejection-eval/sessions/{session_id}"

    gen = await client.post(f"{base}/topics/0/generate", json={"prompt": "구체적 지시"})
    assert gen.status_code == 200
    items = gen.json()["items"]
    # ground truth must not leak to the candidate
    assert all(set(i.keys()) == {"id", "text"} for i in items)
    # should-reject set = {a (injected), b (out of scope)}.
    # flag a (caught) and c (false alarm); miss b.
    await client.post(f"{base}/topics/0/submit", json={"flagged_ids": ["a", "c"]})

    score = await client.post(f"{base}/score")
    assert score.status_code == 200
    result = score.json()
    assert result["candidate_name"] == "익명"
    assert result["status"] == "scored"
    # only the one completed topic appears in the result
    assert len(result["topics"]) == 1
    # tp=1 (a), fp=1 (c), fn=1 (b) -> 0.5 everywhere
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["f1"] == 0.5
    first = result["topics"][0]
    assert first["topic_index"] == 0
    by_id = {i["id"]: i for i in first["items"]}
    assert by_id["a"]["outcome"] == "caught"
    assert by_id["a"]["flaw_source"] == "injected"
    assert by_id["b"]["outcome"] == "missed"
    assert by_id["b"]["flaw_source"] == "out_of_scope"
    assert by_id["c"]["outcome"] == "false_alarm"
    assert first["report"]

    fetched = await client.get(f"{base}/result")
    assert fetched.status_code == 200
    assert fetched.json()["f1"] == 0.5


async def test_score_before_submit_is_conflict(client, mock_llm):
    session_id = await _start_session(client)
    base = f"/api/rejection-eval/sessions/{session_id}"
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
