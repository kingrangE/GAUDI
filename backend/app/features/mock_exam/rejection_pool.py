# ruff: noqa: E501
"""Hard-coded item pool for the rejection-eval exam step (cx-churn-radar).

30 items: 10 flawed (is_flawed=True), 20 correct (is_flawed=False).
Each generate call picks all correct items + a random 0..MAX_FLAWED subset of
the flawed items, shuffles the result, and returns it — no LLM call needed.
"""

import random
from uuid import uuid4

from app.features.rejection_eval.schemas import GeneratedItem

MAX_FLAWED = 5  # maximum flawed items included per generate call

# ── 10 flawed items ───────────────────────────────────────────────────────────
_FLAWED: list[dict] = [
    {
        "text": "API 응답에 customer_email 필드를 포함해 프론트가 고객을 식별할 수 있게 한다.",
        "flaw_type": "wrong_direction",
        "explanation": "PII 평문 노출 — 고객 식별자는 customer_token만 허용, 이메일 직접 반환 금지.",
    },
    {
        "text": "late-arriving 이벤트는 처리 비용 절감을 위해 수신 즉시 DROP한다.",
        "flaw_type": "wrong_direction",
        "explanation": "지연 이벤트 무시 — 요구사항은 명시적 처리(watermark/보정)를 요구한다.",
    },
    {
        "text": "스코어 산출 시 score_date 이후 이벤트까지 포함해 최신 신호를 반영한다.",
        "flaw_type": "wrong_direction",
        "explanation": "데이터 누수 — score_date 이후 미래 이벤트를 피처에 사용하면 실시간 누수 발생.",
    },
    {
        "text": "Top-N API는 페이지네이션 없이 상위 N명 전체를 단일 응답으로 반환한다.",
        "flaw_type": "wrong_tech",
        "explanation": "페이지네이션 누락 — 대용량 결과를 한 번에 반환하면 타임아웃·메모리 폭발 위험.",
    },
    {
        "text": "refund(환불) 이벤트는 구매 취소이므로 긍정 신호로 분류해 스코어에 반영한다.",
        "flaw_type": "wrong_direction",
        "explanation": "오분류 — refund는 부정 신호; 긍정 신호로 처리하면 이탈 탐지 정확도 저하.",
    },
    {
        "text": "이탈 Top-N API를 외부 파트너도 활용할 수 있도록 public 엔드포인트로 공개한다.",
        "flaw_type": "wrong_direction",
        "explanation": "접근 제어 부재 — 내부 서비스 전용이어야 하며 외부 호출은 차단해야 한다.",
    },
    {
        "text": "중복 이벤트 dedup 없이 집계해 처리 지연을 줄인다. 중복은 통계적으로 무시 가능하다.",
        "flaw_type": "wrong_direction",
        "explanation": "중복 미제거 — 동일 이벤트 반복 집계로 부정 신호가 과산정되어 스코어 왜곡.",
    },
    {
        "text": "이탈 스코어 산출에 사용한 피처값과 모델 가중치를 API 응답에 포함해 투명성을 높인다.",
        "flaw_type": "wrong_direction",
        "explanation": "내부 정보 노출 — 피처/가중치 노출은 요구사항 위반이며 역공학 위험.",
    },
    {
        "text": "고객 이름과 phone 필드를 응답에 포함하되 앞 두 글자만 보이도록 부분 표시한다.",
        "flaw_type": "wrong_direction",
        "explanation": "PII 부분 마스킹으로도 부족 — 고객 식별자는 customer_token으로만 노출해야 한다.",
    },
    {
        "text": "파이프라인 재실행 시 이전 스코어를 지우고 전체를 재계산한다. 체크포인트는 불필요하다.",
        "flaw_type": "wrong_direction",
        "explanation": "멱등성 미고려 — 체크포인트 없는 재실행은 중복 집계 위험과 파이프라인 불안정성을 초래.",
    },
]

# ── 20 correct items ──────────────────────────────────────────────────────────
_CORRECT: list[dict] = [
    {
        "text": "API 응답의 고객 식별자는 customer_token만 사용하며 이메일·이름 등 PII는 포함하지 않는다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "이탈 위험 상위 N명 목록은 cursor 기반 페이지네이션으로 제공한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "late-arriving 이벤트는 watermark 기반으로 처리한다: watermark 이내 지연은 스코어 재계산을 트리거한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "build_features는 score_date 이전 이벤트만 사용하며 미래 데이터를 피처에 포함하지 않는다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "동일 (customer_token, event_type, session_id, ts) 조합의 중복 이벤트는 집계 전 dedup한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "Top-N API는 내부 서비스 전용(internal_only)으로 외부 네트워크에서 직접 호출할 수 없다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "cancel은 가장 강한 부정 신호, refund는 중간 부정 신호로 차등 가중치를 부여한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "이탈 스코어는 부정 신호 누적과 긍정 신호(purchase, login) 부재 조건을 모두 반영한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "결측 ts(NULL)인 이벤트는 집계에서 제외하거나 last_active_ts로 보정해 처리한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "Top-N 파라미터는 기본값 100, 최대 1000으로 제한하며 범위를 초과하면 422로 거부한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "스코어는 배치 선계산(batch_precomputed) 방식으로 PostgreSQL에 저장한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "events 테이블에 (customer_token, ts) 복합 인덱스를 추가해 W일 윈도우 쿼리 풀스캔을 방지한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "잘못된 입력(N 범위 초과, 날짜 형식 오류)은 422 Unprocessable Entity로 거부한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "이탈 스코어 산출에 사용된 피처값과 모델 가중치는 API 응답에 포함하지 않는다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "스코어 계산은 요청 시 실시간 재계산 없이 미리 계산된 값(precomputed)을 조회한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "이벤트 수집(ingest)과 피처 생성(preprocess)을 별도 모듈로 분리해 관심사를 격리한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "알 수 없는 event_type은 집계에서 명시적으로 거부하거나 기본 가중치 정책을 적용한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "스코어 상위 K명 추출은 힙(heap) 자료구조로 O(N log k) 복잡도로 처리한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "파이프라인은 처리 완료 범위를 체크포인트로 기록해 재실행 시 중복 집계를 방지한다.",
        "flaw_type": "none",
        "explanation": "",
    },
    {
        "text": "ts 단위를 Unix seconds로 통일하고 타임존은 UTC로 보장해 윈도우 경계 오류를 방지한다.",
        "flaw_type": "none",
        "explanation": "",
    },
]


TOTAL_ITEMS = 10  # items shown to the candidate per session


def sample_items(seed: str | None = None) -> list[GeneratedItem]:
    """Return exactly TOTAL_ITEMS shuffled items: 0..MAX_FLAWED flawed + rest correct."""
    rng = random.Random(seed)
    n_flawed = rng.randint(0, MAX_FLAWED)
    chosen_flawed = rng.sample(_FLAWED, n_flawed)
    chosen_correct = rng.sample(_CORRECT, TOTAL_ITEMS - n_flawed)
    pool = chosen_correct + chosen_flawed
    rng.shuffle(pool)
    return [
        GeneratedItem(
            id=uuid4().hex[:8],
            text=item["text"],
            is_flawed=item in chosen_flawed,
            flaw_type=item["flaw_type"],
            explanation=item["explanation"],
        )
        for item in pool
    ]
