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
}


def get_rubric(project_id: str) -> list[Criterion]:
    """Return the ground-truth checklist for a project (empty list if none)."""

    return _RUBRICS.get(project_id, [])
