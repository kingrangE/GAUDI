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

_GOLD: dict[str, str] = {
    "todo-api": _TODO_API_GOLD,
    "board-api": _BOARD_API_GOLD,
    "web-kanban": _WEB_KANBAN_GOLD,
}


def get_reference(project_id: str) -> str | None:
    """Return the gold CLAUDE.md for a project (answer key; never served via the API)."""

    return _GOLD.get(project_id)


def has_reference(project_id: str) -> bool:
    return project_id in _GOLD
