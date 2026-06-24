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
