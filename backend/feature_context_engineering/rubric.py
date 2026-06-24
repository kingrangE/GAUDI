"""Ground-truth checklists per project, extracted from the gold references (references.py).

Each Criterion is a discrete, wording-independent fact a good CLAUDE.md for that project must
convey. These are the LOCKED answer key the LLM judge scores coverage against (SPEC §5).
Heavier weights mark the project's implicit (README-absent) conventions that discriminate.
"""

from __future__ import annotations

from feature_context_engineering.models import Criterion

_RUBRICS: dict[str, list[Criterion]] = {
    "todo-api": [
        Criterion(id="cmd-run", category="commands",
                  text="개발 서버 실행 방법 (예: `make dev` / uvicorn app.main:app)."),
        Criterion(id="cmd-test", category="commands",
                  text="테스트 실행 명령 (예: `make test` / pytest)."),
        Criterion(id="conv-inmem-tests", category="conventions", weight=2.0,
                  text="테스트는 인메모리 app/storage.py로 돌린다 — "
                       "실제 Postgres/DB를 띄우지 않는다."),
        Criterion(id="conv-settings-env", category="conventions", weight=1.5,
                  text="설정/DATABASE_URL은 .env에서 읽는다(pydantic-settings); "
                       "하드코딩하지 않는다."),
        Criterion(id="struct-routes", category="structure", weight=1.5,
                  text="라우터는 app/routes/에 두고 main.py에서 include_router로 연결한다."),
        Criterion(id="struct-models", category="structure",
                  text="models.py에 Pydantic 스키마와 SQLAlchemy 모델이 함께 들어 있다."),
        Criterion(id="conv-404", category="conventions",
                  text="없는 리소스는 HTTPException 404를 반환한다."),
        Criterion(id="bound-secrets", category="boundaries",
                  text=".env / 시크릿은 절대 커밋하지 않는다."),
    ],
    "board-api": [
        Criterion(id="cmd-run", category="commands",
                  text="개발 서버 실행 방법 (예: `make dev`)."),
        Criterion(id="cmd-test", category="commands",
                  text="테스트 실행 명령 (예: `make test` / pytest)."),
        Criterion(id="conv-orm-schema-split", category="conventions", weight=2.0,
                  text="ORM 모델(models.py)과 Pydantic 스키마(schemas.py)를 분리한다; "
                       "ORM 객체를 그대로 반환하지 않는다."),
        Criterion(id="struct-routers", category="structure", weight=1.5,
                  text="새 리소스는 app/routers/<name>.py에 APIRouter(prefix=...)로 만들고 "
                       "main.py에서 include_router로 연결한다."),
        Criterion(id="conv-201", category="conventions", weight=1.5,
                  text="생성(create) 엔드포인트는 HTTP 201을 반환한다."),
        Criterion(id="conv-404", category="conventions",
                  text="없는 리소스는 HTTPException 404를 반환한다."),
        Criterion(id="conv-pagination", category="conventions", weight=1.5,
                  text="목록은 page/size 쿼리로 페이지네이션한다 (page는 1-based)."),
        Criterion(id="conv-inmem-tests", category="conventions", weight=2.0,
                  text="테스트는 인메모리 app/storage.py로 돌린다 — 실제 DB가 필요 없다."),
        Criterion(id="bound-secrets", category="boundaries",
                  text=".env / 시크릿은 절대 커밋하지 않는다."),
    ],
    "web-kanban": [
        Criterion(id="cmd-dev", category="commands",
                  text="설치/개발 서버 실행 방법 (npm install / npm run dev)."),
        Criterion(id="conv-state-hook", category="conventions", weight=2.0,
                  text="보드 상태는 useBoard 훅을 통해서만 다룬다; Column/Card는 상태 없는 "
                       "표현용(presentational) 컴포넌트."),
        Criterion(id="conv-no-backend", category="conventions", weight=2.0,
                  text="백엔드도 데이터 fetch도 없다 — 완전한 클라이언트 사이드 앱."),
        Criterion(id="struct-components", category="structure",
                  text="컴포넌트 구조 Board -> Column -> Card, 타입은 src/types.ts."),
        Criterion(id="conv-columns", category="conventions",
                  text="컬럼은 고정 집합 todo/doing/done (ColumnId)."),
        Criterion(id="conv-ts", category="conventions",
                  text="TypeScript strict + react-jsx 자동 런타임."),
        Criterion(id="bound-no-api", category="boundaries", weight=1.5,
                  text="백엔드/API 레이어를 추가하지 않는다; "
                       "영속화가 필요하면 클라이언트 사이드로."),
    ],
    "cx-churn-radar": [
        # ── 명령 (3) ──────────────────────────────────────────────────────────
        Criterion(id="cmd-install", category="commands",
                  text="의존성 설치는 `uv sync` 또는 `pip install -e '.[dev]'`로 한다."),
        Criterion(id="cmd-test", category="commands",
                  text="`pytest -q`로 테스트를 실행한다 — 인메모리 폴백 사용, 실 DB 불필요."),
        Criterion(id="cmd-lint", category="commands",
                  text="린트는 `ruff check .`로 실행한다."),
        # ── 구조 (4) ──────────────────────────────────────────────────────────
        Criterion(id="struct-pipeline", category="structure", weight=1.5,
                  text="이벤트 수집·전처리 코드는 `app/pipeline/`에 둔다 "
                       "(`ingest.py`, `preprocess.py`)."),
        Criterion(id="struct-scoring", category="structure",
                  text="ML 모델 로딩과 스코어 계산은 `app/scoring/`에 둔다 "
                       "(`model.py`, `scorer.py`)."),
        Criterion(id="struct-dags", category="structure",
                  text="Airflow DAG 파일은 `dags/`에 두며 DAG ID는 "
                       "`{domain}_{task}_{schedule}` 형식을 따른다 "
                       "(예: `churn_score_daily`, `event_ingest_hourly`)."),
        Criterion(id="struct-pii-module", category="structure", weight=1.5,
                  text="PII 마스킹 로직은 `app/pii.py`에만 둔다 — "
                       "다른 모듈은 직접 마스킹 구현 없이 이 모듈을 호출한다."),
        # ── 컨벤션 (5) ────────────────────────────────────────────────────────
        Criterion(id="conv-pii-mask", category="conventions", weight=2.0,
                  text="고객 이름·이메일·전화번호는 `app.pii.mask_customer()`를 호출해 "
                       "`cust_xxxx` 토큰으로 변환 후 저장·응답한다; "
                       "전화번호는 `mask_phone()`으로 부분 마스킹(010-****-1234)한다."),
        Criterion(id="conv-inmem-test", category="conventions", weight=2.0,
                  text="테스트는 `tests/conftest.py`의 인메모리 픽스처를 사용한다; "
                       "`DATABASE_URL=sqlite:///:memory:`로 오버라이드해 "
                       "실 PostgreSQL 없이 실행한다."),
        Criterion(id="conv-dag-naming", category="conventions",
                  text="DAG ID는 `{domain}_{task}_{schedule}` 규칙을 따른다 "
                       "(예: `churn_score_daily`, `event_ingest_hourly`)."),
        Criterion(id="conv-model-version", category="conventions", weight=1.5,
                  text="ML 모델 아티팩트 파일명에 버전을 포함한다 (`model_v{n}.pkl`); "
                       "실행 경로는 `MODEL_PATH` 환경변수로 지정한다."),
        Criterion(id="conv-event-schema", category="conventions",
                  text="events 테이블 컬럼: `customer_token, event_type, ts, "
                       "session_id, metadata`; `event_type`은 "
                       "`view·cart·purchase·login·support_ticket·refund·cancel` 7가지."),
        # ── 경계 (3) ──────────────────────────────────────────────────────────
        Criterion(id="bound-no-leakage", category="boundaries", weight=2.0,
                  text="`build_features(events, score_date)`에서 `score_date` 이후 "
                       "이벤트는 절대 포함하지 않는다 — 미래 데이터 누수 금지."),
        Criterion(id="bound-no-plain-pii", category="boundaries", weight=2.0,
                  text="DB·로그·API 응답에 고객 평문 PII(이름·이메일·전화번호)를 기록하지 않는다; "
                       "반드시 `app.pii.mask_customer()`를 먼저 호출한다."),
        Criterion(id="bound-no-real-db-tests", category="boundaries", weight=1.5,
                  text="테스트에서 실제 PostgreSQL을 기동하지 않는다; "
                       "`tests/conftest.py`의 인메모리 폴백(`DATABASE_URL=sqlite:///:memory:`) "
                       "만 사용한다."),
    ],
}


def get_rubric(project_id: str) -> list[Criterion]:
    """Return the ground-truth checklist for a project (empty list if none)."""

    return _RUBRICS.get(project_id, [])
