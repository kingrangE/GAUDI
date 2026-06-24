"""Hidden reference ("gold") CLAUDE.md per project — the scoring answer key.

These are NEVER exposed through the API (the router serves only `projects.py`). The scorer
(separate track, SPEC §5) uses each gold doc as the *source of the must-capture facts/
conventions* a candidate's CLAUDE.md is graded against — not as a string-match target, so
alternate wording/structure is fine. Authored from the actual repo; the gold conventions
deliberately include the project's implicit (README-absent) rules that discriminate quality.
Human review is expected before treating a doc as canonical.
"""

from __future__ import annotations

_TODO_API_GOLD = """\
# todo-api

FastAPI todo service. Postgres in prod (SQLAlchemy); tests run against the in-memory store.

## Commands
- Install: `make install`  (pip install -e ".[dev]")
- Dev: `make dev` -> http://localhost:8000 (docs at /docs)
- Test: `make test` (pytest -q). Single: `pytest tests/test_todos.py::test_create_then_fetch`
- Lint: `make lint` (ruff check .)

## Structure
- `app/main.py` — app + router wiring + `/health`
- `app/routes/` — one module per resource; add a router as `APIRouter(prefix=...)` and
  `include_router` it in `app/main.py`
- `app/models.py` — Pydantic schemas (TodoIn/Todo) AND the SQLAlchemy model (TodoRow)
- `app/database.py` — engine/session + the `get_db` dependency
- `app/config.py` — settings from `.env` via pydantic-settings
- `app/storage.py` — in-memory store

## Conventions
- Tests use the in-memory `app/storage.py` — do NOT spin up Postgres for tests.
- Settings come from `.env` (see `.env.example`); never hardcode `DATABASE_URL`.
- Endpoints return the Pydantic `Todo`; a missing id -> `HTTPException(404, detail=...)`.

## Boundaries
- Never commit `.env` or secrets.
- Don't change the `storage.py` interface without updating its tests.
"""

_BOARD_API_GOLD = """\
# board-api

FastAPI board (게시판) CRUD: posts + comments. Postgres in prod (SQLAlchemy); tests use the
in-memory store.

## Commands
- Dev: `make dev` -> http://localhost:8000/docs
- Test: `make test` (pytest -q). Single: `pytest tests/test_posts.py::test_create_then_list`
- Lint: `make lint` (ruff check .)

## Structure
- `app/main.py` — app + `include_router` for posts and comments
- `app/routers/` — one module per resource (`posts.py`, `comments.py`), each an
  `APIRouter(prefix=...)`; wire new ones in `app/main.py`
- `app/models.py` — SQLAlchemy ORM ONLY (Post, Comment, FK)
- `app/schemas.py` — Pydantic request/response ONLY (PostIn/Post, CommentIn/Comment)
- `app/storage.py` — in-memory store used by tests
- `app/database.py` — engine/session + `get_db`

## Conventions
- Keep ORM (`models.py`) and API schemas (`schemas.py`) SEPARATE — never return ORM objects.
- New resource = new `app/routers/<name>.py` (`APIRouter(prefix=...)`) wired in `main.py`.
- Create endpoints return **201**; missing resource -> `HTTPException(404, detail=...)`.
- List endpoints paginate via `page`/`size` query params (page is 1-based).
- Tests run against the in-memory `app/storage.py` — no DB needed.
- A comment must reference an existing post (404 otherwise).

## Boundaries
- Never commit `.env` or secrets.
"""

_WEB_KANBAN_GOLD = """\
# web-kanban

Frontend-only Kanban board. React + Vite + TypeScript. No backend — state lives in the
browser (useState).

## Commands
- Install: `npm install`
- Dev: `npm run dev` -> http://localhost:5173
- Build: `npm run build` (tsc && vite build)

## Structure
- `src/App.tsx` — shell
- `src/components/` — Board -> Column -> Card (presentational only)
- `src/hooks/useBoard.ts` — board state (cards, move, add)
- `src/types.ts` — domain types (Card, ColumnId)

## Conventions
- All board state goes through `useBoard`; Column/Card stay presentational (no local state).
- Columns are the fixed `COLUMNS` set (`todo`/`doing`/`done`); a card's `column` is a `ColumnId`.
- No data fetching and no backend calls — this app is fully client-side.
- TypeScript strict; JSX uses the automatic runtime (`react-jsx`, no React import needed).

## Boundaries
- Don't add a backend/API layer; any persistence stays client-side (e.g., localStorage).
- Mutate state only via the `useBoard` hook.
"""

_CX_CHURN_RADAR_GOLD = """\
# cx-churn-radar

구독형 커머스 고객사의 CX 이벤트 로그로 고객 이탈 위험을 스코어링하고 위험 고객에 대응을
트리거하는 서비스. 데이터 파이프라인 + 이탈 스코어링(ML) + FastAPI 스코어링 API + 알림.
Postgres(운영), 테스트는 인메모리. 배치는 Airflow DAG.

## Commands
- 설정: `cp .env.example .env` 후 `DATABASE_URL`(과 `MODEL_PATH`) 지정
- 설치: `make install`
- Dev: `make dev` -> http://localhost:8000 (docs at /docs)
- Test: `make test` (pytest)
- Lint: `make lint` (ruff)

## Structure
- `app/main.py` — 앱 + 라우터 와이어링 + `/health`
- `app/pipeline/` — 데이터 파이프라인: `ingest.py`(수집·중복 제거·PII 마스킹), `preprocess.py`
  (`build_features(events, score_date)` — 피처 생성)
- `app/scoring/` — `model.py`(`load_model()`), `scorer.py`(이탈 점수 산출)
- `app/api/` — `schemas.py`(Pydantic), `routes.py`(스코어링 엔드포인트)
- `app/pii.py` — PII 마스킹 모듈(`mask_customer` / `mask_phone` / `mask_email`)
- `dags/` — 배치 DAG (`churn_score_daily_dag.py`, `event_ingest_hourly_dag.py`)
- `tests/` — 인메모리 테스트(`conftest.py`)

## Conventions
- **PII 마스킹**: 고객 식별자·전화·이메일은 항상 `app/pii.py`로 마스킹한 값만 저장/응답한다.
  원본 PII는 로그·응답·DB 어디에도 평문으로 남기지 않는다(같은 고객 = 같은 토큰, 일관 토큰화).
- **인메모리 테스트**: 테스트는 `conftest.py`가 `DATABASE_URL=sqlite:///:memory:`로 오버라이드한다 —
  실제 Postgres를 띄우지 않는다.
- **DAG 네이밍**: `DAG_ID`는 파일 stem과 일치(예: `churn_score_daily`, `event_ingest_hourly`).
- **모델 버저닝**: 모델 아티팩트는 `MODEL_PATH` 환경변수로 지정하고 파일명에 버전을 포함한다
  (예: `model_v3.pkl`). 새 모델 배포 시 `MODEL_PATH`만 갱신한다.
- **이벤트 스키마**: 허용 이벤트는 `EVENT_TYPES` frozenset으로 제한하고,
  ingest에서 검증·중복 제거한다.

## Boundaries
- **데이터 누수 금지**: `build_features`는 `score_date` 이후(미래) 이벤트를 피처에 쓰지 않는다.
- **평문 PII 금지**: 원본 고객 식별자/전화/이메일을 로그·응답에 노출하지 않는다 — 항상 마스킹 먼저.
- **테스트에서 실 DB 금지**: 테스트는 인메모리만 사용하며 Postgres 기동을 요구하지 않는다.
- `.env`·시크릿·모델 아티팩트는 절대 커밋하지 않는다.
"""

_GOLD: dict[str, str] = {
    "todo-api": _TODO_API_GOLD,
    "board-api": _BOARD_API_GOLD,
    "web-kanban": _WEB_KANBAN_GOLD,
    "cx-churn-radar": _CX_CHURN_RADAR_GOLD,
}


def get_reference(project_id: str) -> str | None:
    """Return the gold CLAUDE.md for a project (answer key; never served via the API)."""

    return _GOLD.get(project_id)


def has_reference(project_id: str) -> bool:
    return project_id in _GOLD
