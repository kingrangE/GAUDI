"""Endpoint tests for the CS-eval flow (deterministic stub judge, no LLM)."""

from app.features.cs_eval import scoring
from app.features.cs_eval.questions import QUESTIONS

QMAP = {q.id: q for q in QUESTIONS}
BASE = "/api/cs-eval"


def _all_key_points(qid: str) -> str:
    return " ".join(QMAP[qid].rubric["key_points"])


async def test_list_questions_hides_ground_truth(cs_client):
    resp = await cs_client.get(f"{BASE}/questions")
    assert resp.status_code == 200
    body = resp.json()
    assert {q["id"] for q in body} == {
        "ds-hashmap",
        "os-process-thread",
        "net-tcp-handshake",
        "db-index",
    }
    for q in body:
        assert q["prompt_md"] and q["domain"]
        # judge-only grounding must never leak to the candidate
        assert "reference_answer" not in q
        assert "rubric" not in q


async def test_submit_grades_each_response_type(cs_client):
    answers = [
        # all key points present → correct (+5)
        {"question_id": "ds-hashmap", "answer_text": _all_key_points("ds-hashmap")},
        # honest "I don't know" → −2
        {"question_id": "os-process-thread", "answer_text": "잘 모르겠습니다"},
        # substantive but hits no key point → bluff (−5)
        {
            "question_id": "net-tcp-handshake",
            "answer_text": "핵심을 비껴가는 장황하고 관련 없는 서술을 적습니다",
        },
        # two of five key points → partial
        {
            "question_id": "db-index",
            "answer_text": " ".join(QMAP["db-index"].rubric["key_points"][:2]),
        },
    ]
    created = await cs_client.post(
        f"{BASE}/sessions", json={"candidate_id": "민수", "answers": answers}
    )
    assert created.status_code == 202
    assert created.json()["status"] == "grading"
    session_id = created.json()["session_id"]

    result = await cs_client.get(f"{BASE}/sessions/{session_id}")
    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "graded"

    by_q = {a["question_id"]: a for a in body["per_question"]}
    assert by_q["ds-hashmap"]["response_type"] == "correct"
    assert by_q["ds-hashmap"]["score"] == 5
    assert by_q["os-process-thread"]["response_type"] == "honest_unknown"
    assert by_q["os-process-thread"]["score"] == -2
    assert by_q["net-tcp-handshake"]["response_type"] == "bluff_wrong"
    assert by_q["net-tcp-handshake"]["score"] == -5
    assert by_q["db-index"]["response_type"] == "partial"
    assert 1 <= by_q["db-index"]["score"] <= 4

    expected_total = sum(a["score"] for a in body["per_question"])
    assert body["total_score"] == expected_total
    assert body["normalized_score"] == scoring.normalize(expected_total, 4)
    # both reports are produced
    assert body["summary_report"]
    assert body["analysis_report"]
    # missing keywords from the partial/unknown answers surface in the summary
    assert "체이닝" in body["summary_report"] or "스캔" in body["summary_report"]


async def test_honest_unknown_beats_bluff(cs_client):
    """The signature behaviour: admitting ignorance (−2) scores above bluffing (−5)."""

    async def _score(answer_text: str) -> int:
        created = await cs_client.post(
            f"{BASE}/sessions",
            json={
                "candidate_id": "c",
                "answers": [
                    {"question_id": "net-tcp-handshake", "answer_text": answer_text}
                ],
            },
        )
        sid = created.json()["session_id"]
        body = (await cs_client.get(f"{BASE}/sessions/{sid}")).json()
        return body["per_question"][0]["score"]

    honest = await _score("이 부분은 잘 모르겠습니다")
    bluff = await _score("자신있게 적지만 실제로는 핵심과 무관한 장황한 답변입니다")
    assert honest == -2
    assert bluff == -5
    assert honest > bluff


async def test_unknown_question_is_404(cs_client):
    created = await cs_client.post(
        f"{BASE}/sessions",
        json={"candidate_id": "x", "answers": [{"question_id": "nope", "answer_text": "a"}]},
    )
    assert created.status_code == 404


async def test_unknown_session_is_404(cs_client):
    assert (await cs_client.get(f"{BASE}/sessions/does-not-exist")).status_code == 404


async def test_missing_fields_are_422(cs_client):
    assert (await cs_client.post(f"{BASE}/sessions", json={})).status_code == 422
    # empty answers list is rejected
    assert (
        await cs_client.post(
            f"{BASE}/sessions", json={"candidate_id": "x", "answers": []}
        )
    ).status_code == 422
