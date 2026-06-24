"""cx-churn-radar topic: loading + scoring with ~15 items (LLM mocked).

Covers:
- Topic loads correctly with 4-6 requirements containing domain keywords.
- Direct score_items call with 15 items (5 injected flaws, 1 out-of-scope)
  produces the expected tp/fp/fn counts and an F1 in [0, 1].
- Full async generate→flag→score flow via the HTTP client with mocked LLM.
"""

import pytest

from app.features.rejection_eval import service
from app.features.rejection_eval.schemas import GenerationOutput, ItemJudgement, JudgeOutput
from app.features.rejection_eval.scoring import score_items
from app.features.rejection_eval.topics import TOPIC_COUNT, TOPICS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CX_CHURN_TOPIC_INDEX = next(
    i for i, t in enumerate(TOPICS) if "Churn" in t.title
)

_CX_TOPIC = TOPICS[CX_CHURN_TOPIC_INDEX]


def _item(item_id: str, is_flawed: bool, flaw_type: str = "none") -> dict:
    return {
        "id": item_id,
        "text": f"결정: {item_id}",
        "is_flawed": is_flawed,
        "flaw_type": flaw_type,
        "explanation": "...",
    }


# ---------------------------------------------------------------------------
# Topic-loading tests (no LLM, no DB)
# ---------------------------------------------------------------------------


def test_cx_churn_radar_topic_is_present():
    titles = [t.title for t in TOPICS]
    assert any("Churn" in title for title in titles), "cx-churn-radar topic not found in TOPICS"


def test_cx_churn_radar_requirements_count():
    assert 4 <= len(_CX_TOPIC.requirements) <= 6


def test_cx_churn_radar_requirements_have_domain_keywords():
    joined = " ".join(_CX_TOPIC.requirements)
    assert "customer_token" in joined, "requirements must mention customer_token (PII tokenisation)"
    assert any(kw in joined for kw in ("페이지네이션", "cursor", "offset")), (
        "requirements must mention pagination"
    )
    assert any(kw in joined for kw in ("ts", "타임스탬프", "late-arriving")), (
        "requirements must mention timestamp / late-arriving handling"
    )
    assert "중복" in joined, "requirements must mention duplicate-event removal"
    assert any(kw in joined for kw in ("피처", "가중치", "leakage", "노출")), (
        "requirements must mention preventing model internals from leaking"
    )


def test_topic_count_is_updated():
    # Adding the cx-churn-radar topic means there are now at least 4 topics.
    assert TOPIC_COUNT >= 4
    assert TOPIC_COUNT == len(TOPICS)


# ---------------------------------------------------------------------------
# Direct scoring tests with 15 items (no LLM)
#
# Layout:
#   item-1..5  : injected flaws (AXOps domain traps)
#   item-6..15 : correct decisions (is_flawed=False)
#
# Candidate flags item-1, item-2, item-3, item-7 (ignores item-4, item-5).
# Judge marks item-14 as out-of-scope (ML retraining pipeline not in spec).
#
# should-reject = {1,2,3,4,5} ∪ {14} = {1,2,3,4,5,14}
# caught:        {1,2,3}   → tp = 3
# missed:        {4,5,14}  → fn = 3
# false_alarm:   {7}       → fp = 1
# precision = 3/4 = 0.75 ; recall = 3/6 = 0.5 ; f1 = 0.6
# ---------------------------------------------------------------------------

_ITEMS_15 = [
    _item("item-1",  True, "wrong_direction"),   # refund를 긍정 신호로 오분류
    _item("item-2",  True, "wrong_direction"),   # PII 평문(customer_email) 응답 포함
    _item("item-3",  True, "wrong_tech"),        # 페이지네이션 없는 풀스캔
    _item("item-4",  True, "wrong_direction"),   # late-arriving 이벤트 무시
    _item("item-5",  True, "wrong_tech"),        # 모델 가중치를 응답에 노출
    *[_item(f"item-{i}", False) for i in range(6, 16)],   # item-6..15 correct
]

assert len(_ITEMS_15) == 15  # sanity-check at import time


def test_scoring_15_items_correct_tp_fp_fn():
    score = score_items(
        _ITEMS_15,
        flagged_ids=["item-1", "item-2", "item-3", "item-7"],
        out_of_scope_ids=["item-14"],
    )
    assert score["tp"] == 3
    assert score["fp"] == 1
    assert score["fn"] == 3


def test_scoring_15_items_f1_in_unit_interval():
    score = score_items(
        _ITEMS_15,
        flagged_ids=["item-1", "item-2", "item-3", "item-7"],
        out_of_scope_ids=["item-14"],
    )
    assert 0.0 <= score["f1"] <= 1.0


def test_scoring_15_items_precision_recall():
    score = score_items(
        _ITEMS_15,
        flagged_ids=["item-1", "item-2", "item-3", "item-7"],
        out_of_scope_ids=["item-14"],
    )
    assert abs(score["precision"] - 0.75) < 1e-9   # 3/4
    assert abs(score["recall"]    - 0.5)  < 1e-9   # 3/6
    assert abs(score["f1"]        - 0.6)  < 1e-9   # 2*0.75*0.5/1.25


def test_scoring_15_items_outcome_labels():
    score = score_items(
        _ITEMS_15,
        flagged_ids=["item-1", "item-2", "item-3", "item-7"],
        out_of_scope_ids=["item-14"],
    )
    by_id = {i["id"]: i for i in score["items"]}

    for caught_id in ("item-1", "item-2", "item-3"):
        assert by_id[caught_id]["outcome"] == "caught"
        assert by_id[caught_id]["flaw_source"] == "injected"

    for missed_injected in ("item-4", "item-5"):
        assert by_id[missed_injected]["outcome"] == "missed"
        assert by_id[missed_injected]["flaw_source"] == "injected"

    assert by_id["item-14"]["outcome"] == "missed"
    assert by_id["item-14"]["flaw_source"] == "out_of_scope"
    assert by_id["item-14"]["in_requirements"] is False

    assert by_id["item-7"]["outcome"] == "false_alarm"
    assert by_id["item-6"]["outcome"] == "correct_accept"


def test_scoring_perfect_catch_all_flaws():
    """Perfect candidate who catches every flaw → f1 == 1.0."""
    items = [
        _item("item-1", True,  "wrong_direction"),
        _item("item-2", True,  "wrong_tech"),
        _item("item-3", True,  "wrong_direction"),
        *[_item(f"item-{i}", False) for i in range(4, 16)],
    ]
    assert len(items) == 15
    score = score_items(items, flagged_ids=["item-1", "item-2", "item-3"])
    assert score["tp"] == 3
    assert score["fp"] == 0
    assert score["fn"] == 0
    assert score["f1"] == 1.0


# ---------------------------------------------------------------------------
# Full async flow: generate → flag → score (LLM mocked)
# ---------------------------------------------------------------------------

def _cx_churn_generation() -> GenerationOutput:
    """Deterministic stand-in for the LLM generator — 15 items, 5 injected flaws."""
    return GenerationOutput(items=[
        {"id": "item-1",
         "text": "refund 이벤트를 purchase와 동일하게 긍정 신호로 집계한다",
         "is_flawed": True, "flaw_type": "wrong_direction",
         "explanation": "refund는 환불·불만을 뜻하므로 부정 신호로 분류해야 한다"},
        {"id": "item-2",
         "text": "API 응답 payload에 customer_email 필드를 포함해 호출자에게 전달한다",
         "is_flawed": True, "flaw_type": "wrong_direction",
         "explanation": "PII 평문(이메일)은 응답에 포함하면 안 되며 customer_token만 써야 한다"},
        {"id": "item-3",
         "text": "이탈 위험 고객 Top-N 조회 시 events 테이블 전체를 풀스캔하여 집계한다",
         "is_flawed": True, "flaw_type": "wrong_tech",
         "explanation": "풀스캔은 대규모 로그에서 심각한 성능 문제를 일으키며 페이지네이션도 없다"},
        {"id": "item-4",
         "text": "ts 컬럼이 null인 이벤트는 보정 없이 그대로 집계에 포함한다",
         "is_flawed": True, "flaw_type": "wrong_direction",
         "explanation": "결측 타임스탬프 이벤트는 명시적으로 스킵하거나 보정 처리해야 한다"},
        {"id": "item-5",
         "text": "API 응답에 feature_weights 배열을 포함해 이탈 점수 근거를 투명하게 제공한다",
         "is_flawed": True, "flaw_type": "wrong_tech",
         "explanation": "내부 피처 가중치 노출은 모델 data leakage이며 요구사항에서 금지된다"},
        {"id": "item-6",
         "text": "고객 식별은 customer_token으로만 수행하며 PII 원문은 저장·응답하지 않는다",
         "is_flawed": False, "flaw_type": "none",
         "explanation": "토큰 기반 식별은 PII 보호 요구사항에 부합한다"},
        {"id": "item-7",
         "text": "cursor 기반 페이지네이션으로 Top-N 결과를 분할 반환한다",
         "is_flawed": False, "flaw_type": "none",
         "explanation": "cursor 페이지네이션은 대규모 결과셋 처리에 적합하다"},
        {"id": "item-8",
         "text": "cancel 이벤트 W일 내 누적 횟수를 이탈 위험 점수의 핵심 부정 신호로 사용한다",
         "is_flawed": False, "flaw_type": "none",
         "explanation": "cancel은 구독 해지 의향을 나타내는 명백한 이탈 징후이다"},
        {"id": "item-9",
         "text": "support_ticket이 W일 내 N건 이상이면 이탈 위험 가중치를 증가시킨다",
         "is_flawed": False, "flaw_type": "none",
         "explanation": "반복적인 지원 요청은 불만족의 신호이므로 이탈 예측에 유효하다"},
        {"id": "item-10",
         "text": "집계 전 (session_id, event_type, ts) 조합이 동일한 중복 이벤트를 제거한다",
         "is_flawed": False, "flaw_type": "none",
         "explanation": "중복 이벤트 제거는 요구사항에서 명시적으로 요구한다"},
        {"id": "item-11",
         "text": "W일 내 purchase 이벤트가 존재하면 긍정 신호로 이탈 위험 점수를 낮춘다",
         "is_flawed": False, "flaw_type": "none",
         "explanation": "purchase는 긍정 신호로 올바르게 분류된다"},
        {"id": "item-12",
         "text": "W일 내 login 활동이 없으면 부정 신호로 가중치를 추가한다",
         "is_flawed": False, "flaw_type": "none",
         "explanation": "login 부재는 이탈 징후로 올바른 처리이다"},
        {"id": "item-13",
         "text": "late-arriving 이벤트는 last_active_ts 기준 W일 윈도우에 맞춰 보정 처리한다",
         "is_flawed": False, "flaw_type": "none",
         "explanation": "late-arriving 이벤트 보정은 요구사항에 부합하는 명시적 처리이다"},
        {"id": "item-14",
         "text": "이탈 예측 모델을 API 요청마다 실시간으로 재학습시켜 최신 상태를 유지한다",
         "is_flawed": False, "flaw_type": "none",
         "explanation": "요구사항에 없는 실시간 ML 재학습 파이프라인 추가로 범위를 벗어난다"},
        {"id": "item-15",
         "text": "risk_score 내림차순으로 정렬하여 상위 N명을 반환한다",
         "is_flawed": False, "flaw_type": "none",
         "explanation": "위험도 내림차순 정렬은 Top-N API에 적합한 자연스러운 결정이다"},
    ])


@pytest.fixture
def mock_cx_churn_llm(monkeypatch):
    """Patches generate_design and judge_attempt for the cx-churn-radar flow."""

    async def fake_generate(topic_title, prompt):
        return _cx_churn_generation()

    async def fake_judge(requirements, items, flagged_ids, reasons):
        # item-14 is out-of-scope (real-time retraining not in requirements)
        return JudgeOutput(
            report="refund 오분류와 PII 평문 노출을 탐지하지 못함; 모델 재학습 범위 이탈도 미탐지",
            judgements=[
                ItemJudgement(item_id=item.id, in_requirements=(item.id != "item-14"))
                for item in items
            ],
        )

    monkeypatch.setattr(service, "generate_design", fake_generate)
    monkeypatch.setattr(service, "judge_attempt", fake_judge)


async def test_cx_churn_radar_full_flow(client, mock_cx_churn_llm):
    """generate → flag → score for the cx-churn-radar topic (15 items, LLM mocked)."""
    # --- create session ---
    resp = await client.post("/api/rejection-eval/sessions", json={})
    assert resp.status_code == 200
    body = resp.json()
    session_id = body["session_id"]

    # cx-churn-radar topic must be visible with its requirements
    topics = body["topics"]
    assert len(topics) == TOPIC_COUNT
    cx_meta = topics[CX_CHURN_TOPIC_INDEX]
    assert "Churn" in cx_meta["title"]
    assert len(cx_meta["requirements"]) >= 4

    base = f"/api/rejection-eval/sessions/{session_id}"

    # --- generate ---
    prompt = "이탈 Top-N API를 설계해줘. customer_token 기반, cursor 페이지네이션 포함."
    gen = await client.post(
        f"{base}/topics/{CX_CHURN_TOPIC_INDEX}/generate",
        json={"prompt": prompt},
    )
    assert gen.status_code == 200
    items = gen.json()["items"]
    assert len(items) == 15
    # ground-truth flags must not be visible to the candidate
    assert all(set(i.keys()) == {"id", "text"} for i in items)

    # --- submit (catches items 1-3, misses 4+5+14, false-alarms on 7) ---
    submit = await client.post(
        f"{base}/topics/{CX_CHURN_TOPIC_INDEX}/submit",
        json={"flagged_ids": ["item-1", "item-2", "item-3", "item-7"]},
    )
    assert submit.status_code == 200

    # --- score ---
    score_resp = await client.post(f"{base}/score")
    assert score_resp.status_code == 200
    result = score_resp.json()
    assert result["status"] == "scored"
    assert len(result["topics"]) == 1

    topic_result = result["topics"][0]
    assert topic_result["topic_index"] == CX_CHURN_TOPIC_INDEX

    # tp=3, fp=1, fn=3 → precision=0.75, recall=0.5, f1=0.6
    assert abs(result["precision"] - 0.75) < 1e-9
    assert abs(result["recall"]    - 0.5)  < 1e-9
    assert abs(result["f1"]        - 0.6)  < 1e-9
    assert 0.0 <= result["f1"] <= 1.0

    by_id = {i["id"]: i for i in topic_result["items"]}

    # caught injected flaws
    for caught_id in ("item-1", "item-2", "item-3"):
        assert by_id[caught_id]["outcome"] == "caught"
        assert by_id[caught_id]["flaw_source"] == "injected"

    # missed injected flaws
    for missed_id in ("item-4", "item-5"):
        assert by_id[missed_id]["outcome"] == "missed"
        assert by_id[missed_id]["flaw_source"] == "injected"

    # missed out-of-scope item
    assert by_id["item-14"]["outcome"] == "missed"
    assert by_id["item-14"]["flaw_source"] == "out_of_scope"

    # false alarm on a correct item
    assert by_id["item-7"]["outcome"] == "false_alarm"

    # a correct item accepted without flagging
    assert by_id["item-15"]["outcome"] == "correct_accept"

    # GET result returns the same scores
    fetched = await client.get(f"{base}/result")
    assert fetched.status_code == 200
    assert abs(fetched.json()["f1"] - 0.6) < 1e-9
