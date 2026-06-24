"""Built-in task registry.

Each task pairs candidate-facing **requirements** (the *what* — checkable) with a hidden
**decision rubric** whose options are quality-graded (the *how* — scored for soundness).
The brief gives the stack + requirements; it never enumerates the decision rubric.
"""

from __future__ import annotations

from feature_spec_design.models import (
    DecisionDimension,
    DimensionOption,
    Requirement,
    SpecTask,
)


def _opts(grades: dict[str, str]) -> list[DimensionOption]:
    return [DimensionOption(value=v, quality=q) for v, q in grades.items()]


_TASKS: dict[str, SpecTask] = {
    "login-signup": SpecTask(
        id="login-signup",
        title="로그인 / 회원가입 기능 구현",
        brief=(
            "우리 서비스는 백엔드로 FastAPI, 데이터베이스로 PostgreSQL을 사용합니다. "
            "이 스택 위에 로그인/회원가입 기능을 구현하도록 AI에게 지시하세요.\n\n"
            "요구사항:\n"
            "- 이메일과 비밀번호로 회원가입할 수 있어야 합니다.\n"
            "- 이미 가입된 이메일로는 다시 가입할 수 없어야 합니다.\n"
            "- 회원가입은 이메일 인증을 거쳐야 완료됩니다.\n"
            "- 로그인하면 이후 요청에서 인증된 사용자로 식별되어야 합니다.\n"
            "- 비밀번호는 평문으로 저장하면 안 됩니다.\n"
            "- 인증된 사용자만 접근 가능한 보호 엔드포인트가 하나 이상 있어야 합니다.\n"
            "- 형식 오류·필수값 누락 등 잘못된 입력은 거부해야 합니다.\n\n"
            "이 요구사항을 만족하도록 세부 설계는 직접 판단해 구체적으로 지시하세요."
        ),
        requirements=[
            Requirement(id="signup", text="이메일과 비밀번호로 회원가입할 수 있다"),
            Requirement(id="unique_email", text="이미 가입된 이메일로는 재가입이 거부된다"),
            Requirement(id="email_verification", text="회원가입은 이메일 인증을 거쳐야 완료된다"),
            Requirement(
                id="authenticated_session",
                text="로그인 후 이후 요청에서 인증된 사용자로 식별된다",
            ),
            Requirement(id="password_not_plaintext", text="비밀번호가 평문으로 저장되지 않는다"),
            Requirement(
                id="protected_endpoint",
                text="인증이 필요한 보호 엔드포인트가 하나 이상 있다",
            ),
            Requirement(
                id="input_rejection",
                text="형식 오류·필수값 누락 등 잘못된 입력을 거부한다",
            ),
        ],
        dimensions=[
            DecisionDimension(
                key="password_storage",
                label="비밀번호 저장 방식",
                description="비밀번호를 저장하는 방식 (해시 알고리즘 또는 평문).",
                options=_opts(
                    {
                        "bcrypt": "good",
                        "argon2": "good",
                        "scrypt": "good",
                        "pbkdf2": "ok",
                        "sha256": "weak",
                        "sha1": "weak",
                        "md5": "bad",
                        "plaintext": "bad",
                    }
                ),
            ),
            DecisionDimension(
                key="auth_mechanism",
                label="인증 방식",
                description="로그인 상태 유지 방식.",
                options=_opts(
                    {
                        "session": "good",
                        "jwt": "good",
                        "oauth": "ok",
                        "basic_auth": "weak",
                        "none": "bad",
                    }
                ),
            ),
            DecisionDimension(
                key="token_transport",
                label="토큰 전달/저장 위치",
                description="토큰/세션을 클라이언트에 전달·저장하는 위치.",
                options=_opts(
                    {
                        "httponly_cookie": "good",
                        "authorization_header": "good",
                        "cookie": "ok",
                        "localstorage": "weak",
                        "url_param": "bad",
                        "none": "bad",
                    }
                ),
            ),
            DecisionDimension(
                key="user_id_strategy",
                label="사용자 식별자(PK)",
                description="사용자 테이블 기본 키 전략.",
                options=_opts(
                    {
                        "uuid": "good",
                        "bigint": "good",
                        "serial": "ok",
                        "email": "weak",
                        "none": "bad",
                    }
                ),
            ),
            DecisionDimension(
                key="input_validation",
                label="입력 검증",
                description="이메일/비밀번호 형식 등 입력 유효성 검증 방식.",
                options=_opts(
                    {
                        "pydantic": "good",
                        "schema": "good",
                        "manual": "ok",
                        "none": "bad",
                    }
                ),
            ),
        ],
    ),
    "cx-churn-radar-topn": SpecTask(
        id="cx-churn-radar-topn",
        title="이탈 위험 Top-N 고객 추출 API 설계 지시",
        brief=(
            "당신은 AXOps팀의 AI 어시스턴트입니다. "
            "구독형 커머스 고객사의 CX 로그로 이탈 위험 고객을 탐지하는 서비스를 구축합니다.\n\n"
            "데이터 환경:\n"
            "- events: customer_token, "
            "event_type(view|cart|purchase|login|support_ticket|refund|cancel), "
            "ts, session_id, metadata\n"
            "- customers: customer_token, signup_ts, plan, region, last_active_ts\n"
            "- 데이터 품질 주의: 결측 ts, late-arriving 이벤트, "
            "중복 레코드, 스키마 드리프트 존재.\n"
            "- PII 규정: customer 식별자는 customer_token(토큰)으로만 처리, 평문 노출 금지.\n"
            "- 이탈 정의: 최근 W일 내 부정 신호(refund, cancel, support_ticket) 누적 "
            "+ 긍정 신호(purchase, login) 부재\n\n"
            "구현 요구사항:\n"
            "- 최근 W일 윈도우 집계로 고객별 이탈 스코어를 산출해야 합니다.\n"
            "- 지연 도착(late-arriving) 이벤트를 정의된 정책에 따라 처리해야 합니다.\n"
            "- 응답에서 고객 식별자는 customer_token으로만 노출, PII 평문 불포함.\n"
            "- 반환할 이탈 위험 상위 N을 파라미터로 지정할 수 있어야 합니다.\n"
            "- 결과 목록은 페이지네이션으로 제공되어야 합니다.\n"
            "- 내부 서비스 전용 접근 제어로 외부 호출을 차단해야 합니다.\n"
            "- 잘못된 입력(N 범위 초과, 날짜 오류 등)을 검증·거부해야 합니다.\n"
            "- 결측 ts·중복 이벤트가 있어도 스코어 산출이 안전하게 완료되어야 합니다.\n\n"
            "이 요구사항을 만족하도록 세부 설계는 직접 판단해 구체적으로 지시하세요."
        ),
        requirements=[
            Requirement(
                id="window_score",
                text="최근 W일 윈도우 집계로 고객별 이탈 스코어를 산출한다"
                "(부정신호 누적·긍정신호 부재 반영)",
            ),
            Requirement(
                id="late_event_handling",
                text="지연 도착(late-arriving) 이벤트를 정의된 정책에 따라 처리한다",
            ),
            Requirement(
                id="pii_safe",
                text="응답에서 고객 식별자는 customer_token으로만 노출되고"
                " PII 평문은 포함되지 않는다",
            ),
            Requirement(
                id="topn_param",
                text="반환할 이탈 위험 상위 N을 파라미터로 지정할 수 있다",
            ),
            Requirement(
                id="pagination",
                text="결과 목록은 페이지네이션으로 제공된다",
            ),
            Requirement(
                id="internal_access",
                text="내부 서비스 전용 접근 제어로 외부 호출을 차단한다",
            ),
            Requirement(
                id="input_validation",
                text="잘못된 입력(N 범위 초과, 날짜 오류 등)을 검증·거부한다",
            ),
            Requirement(
                id="dirty_data_defense",
                text="결측 ts·중복 이벤트가 있어도 스코어 산출이 안전하게 완료된다",
            ),
        ],
        dimensions=[
            DecisionDimension(
                key="window_aggregation",
                label="윈도우 집계 방식",
                description="이탈 스코어 산출에 사용하는 시간 윈도우 집계 전략.",
                options=_opts(
                    {
                        "streaming": "good",
                        "batch_precomputed": "good",
                        "batch_adhoc": "ok",
                        "no_window": "bad",
                    }
                ),
            ),
            DecisionDimension(
                key="late_event_policy",
                label="late-arriving 이벤트 처리 정책",
                description="집계 윈도우 마감 후 도착한 지연 이벤트를 다루는 방식.",
                options=_opts(
                    {
                        "watermark": "good",
                        "buffer": "ok",
                        "drop": "weak",
                        "ignore": "bad",
                    }
                ),
            ),
            DecisionDimension(
                key="pii_handling",
                label="PII 처리 방식",
                description="고객 식별자 및 개인정보를 API 응답에서 처리하는 방식.",
                options=_opts(
                    {
                        "tokenized": "good",
                        "partial_mask": "good",
                        "plaintext": "bad",
                        "none": "bad",
                    }
                ),
            ),
            DecisionDimension(
                key="storage",
                label="이탈 스코어 저장소",
                description="집계된 이탈 스코어를 저장·조회하는 저장소 전략.",
                options=_opts(
                    {
                        "postgres": "good",
                        "redis_cache": "good",
                        "in_memory": "weak",
                        "none": "bad",
                    }
                ),
            ),
            DecisionDimension(
                key="pagination",
                label="페이지네이션 방식",
                description="Top-N 결과 목록을 클라이언트에게 제공하는 페이지네이션 전략.",
                options=_opts(
                    {
                        "cursor": "good",
                        "offset": "ok",
                        "none": "bad",
                    }
                ),
            ),
            DecisionDimension(
                key="access_control",
                label="접근 제어",
                description="API 엔드포인트에 대한 접근 권한 제어 방식.",
                options=_opts(
                    {
                        "internal_only": "good",
                        "api_key": "ok",
                        "public": "bad",
                    }
                ),
            ),
            DecisionDimension(
                key="scoring_source",
                label="스코어 계산 방식",
                description="API 응답 시 이탈 스코어를 계산·조회하는 방식.",
                options=_opts(
                    {
                        "precomputed": "good",
                        "on_the_fly": "ok",
                        "unscored": "bad",
                    }
                ),
            ),
        ],
    ),
    "file-upload-api": SpecTask(
        id="file-upload-api",
        title="파일 업로드 API 구현",
        brief=(
            "우리 서비스는 백엔드로 FastAPI를 사용합니다. "
            "파일 업로드를 처리하는 API를 구현하도록 AI에게 지시하세요.\n\n"
            "요구사항:\n"
            "- 클라이언트가 파일을 업로드할 수 있어야 합니다.\n"
            "- 업로드한 파일을 이후에 다시 내려받을 수 있어야 합니다.\n"
            "- 허용되지 않는 형식의 파일은 거부해야 합니다.\n"
            "- 너무 큰 파일은 거부해야 합니다.\n\n"
            "이 요구사항을 만족하도록 세부 설계는 직접 판단해 구체적으로 지시하세요."
        ),
        requirements=[
            Requirement(id="upload", text="클라이언트가 파일을 업로드할 수 있다"),
            Requirement(id="download", text="업로드한 파일을 다시 내려받을 수 있다"),
            Requirement(id="type_rejection", text="허용되지 않는 형식의 파일을 거부한다"),
            Requirement(id="size_rejection", text="너무 큰 파일을 거부한다"),
        ],
        dimensions=[
            DecisionDimension(
                key="storage_backend",
                label="저장 백엔드",
                description="업로드 파일을 저장하는 위치.",
                options=_opts(
                    {
                        "s3": "good",
                        "gcs": "good",
                        "local_disk": "ok",
                        "db_blob": "weak",
                        "none": "bad",
                    }
                ),
            ),
            DecisionDimension(
                key="size_limit",
                label="크기 제한",
                description="업로드 허용 최대 크기 정책.",
                options=_opts(
                    {
                        "explicit_limit": "good",
                        "framework_default": "ok",
                        "none": "bad",
                    }
                ),
            ),
            DecisionDimension(
                key="type_validation",
                label="형식 검증",
                description="허용 파일 형식/확장자 검증 방식.",
                options=_opts(
                    {
                        "content_type_and_magic": "good",
                        "whitelist": "good",
                        "extension_check": "ok",
                        "none": "bad",
                    }
                ),
            ),
            DecisionDimension(
                key="filename_strategy",
                label="저장 파일명 전략",
                description="저장 시 파일명 처리.",
                options=_opts(
                    {
                        "uuid": "good",
                        "hash": "good",
                        "sanitized": "ok",
                        "original": "weak",
                        "none": "bad",
                    }
                ),
            ),
        ],
    ),
}


def get_task(task_id: str) -> SpecTask | None:
    return _TASKS.get(task_id)


def list_tasks() -> list[SpecTask]:
    return list(_TASKS.values())
