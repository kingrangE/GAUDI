"""Fixed, human-authored topics for the rejection-ability evaluation.

Each topic carries a fixed **functional-requirements spec** ("문제"). The spec is
**shown to the candidate** but is **never given to the generator** — the AI designs
only from the candidate's prompt. Anything in the generated design that the spec
does not call for is an out-of-scope flaw the candidate must reject; the spec is
the ground truth at evaluation time.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    title: str
    description: str
    requirements: tuple[str, ...]


TOPICS: tuple[Topic, ...] = (
    Topic(
        title="로그인 / 회원가입 기능",
        description="아래 기능 요구사항을 만족하도록 AI에게 설계를 지시하세요.",
        requirements=(
            "이메일과 비밀번호로 회원가입한다.",
            "비밀번호는 안전한 해시(bcrypt 등)로 저장한다.",
            "로그인 성공 시 인증 토큰(JWT 등)을 발급한다.",
            "이미 가입된 이메일의 중복 가입을 막는다.",
        ),
    ),
    Topic(
        title="게시글 CRUD + 이미지 업로드 API",
        description="아래 기능 요구사항을 만족하도록 AI에게 설계를 지시하세요.",
        requirements=(
            "게시글의 생성·조회·수정·삭제를 제공한다.",
            "작성자 본인만 자신의 글을 수정·삭제할 수 있다.",
            "이미지 업로드를 지원하고 파일 크기·형식을 검증한다.",
            "목록 조회는 페이지네이션을 제공한다.",
        ),
    ),
    Topic(
        title="실시간 알림 시스템",
        description="아래 기능 요구사항을 만족하도록 AI에게 설계를 지시하세요.",
        requirements=(
            "사용자에게 실시간으로 알림을 전달한다.",
            "오프라인 사용자는 재접속 시 놓친 알림을 받는다.",
            "알림의 읽음·안읽음 상태를 관리한다.",
            "사용자 수 증가에 맞춰 수평 확장이 가능해야 한다.",
        ),
    ),
    Topic(
        title="이탈 Top-N API (CX Churn-Radar)",
        description=(
            "구독형 커머스 CX 로그 기반 고객 이탈 징후 탐지 서비스(AXOps팀)입니다. "
            "아래 기능 요구사항을 만족하도록 AI에게 설계를 지시하세요."
        ),
        requirements=(
            "events 테이블의 부정 신호(cancel, refund, support_ticket) 누적 빈도와 "
            "긍정 신호(purchase, login) 부재를 결합해 고객별 이탈 위험 점수를 계산한다.",
            "고객 식별은 일관된 customer_token(토큰화 처리)만 사용하며, "
            "평문 이메일·이름 등 PII는 API 응답에 포함하지 않는다.",
            "이탈 위험 상위 N명을 반환하는 API는 cursor 기반 또는 offset/limit "
            "페이지네이션을 제공한다.",
            "결측 타임스탬프(ts=null)와 지연 도착(late-arriving) 이벤트는 "
            "명시적으로 처리(스킵하거나 last_active_ts 기준 보정)한다.",
            "중복 이벤트(동일 session_id·event_type·ts 조합)는 집계 전 중복 제거한다.",
            "이탈 위험 점수 산출에 사용된 내부 피처나 모델 가중치는 API 응답에 노출하지 않는다.",
        ),
    ),
)

TOPIC_COUNT = len(TOPICS)
