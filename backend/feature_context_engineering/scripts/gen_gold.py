"""Generate the judge-reliability gold fixtures for context-engineering.

SEED gold — human review recommended before treating κ/agreement numbers as canonical
(per references.py). Each submission is a hand-authored CLAUDE.md whose coverage is designed
to be unambiguous: it explicitly states the criteria listed in ``covered`` and omits the rest,
so the human label == the construction intent. The script validates every ``covered`` id
against the project's rubric and derives recall, then writes:

  fixtures/synthetic_submissions.json   {key, problem_index, author_model, flaws=[claude_md]}
  fixtures/human_gold.json              {key, matched_ids, recall}
  fixtures/panel_models.json            {judge_models, author_models}

Run:  python -m feature_context_engineering.scripts.gen_gold
"""

from __future__ import annotations

import json
from pathlib import Path

from feature_context_engineering.projects import list_projects
from feature_context_engineering.rubric import get_rubric

# Project index == position in list_projects() (todo-api=0, board-api=1, web-kanban=2).
_PROJECT_INDEX = {p.id: i for i, p in enumerate(list_projects())}

_TD_FULL = """\
# todo-api

FastAPI 할 일(todo) REST API.

## 명령어
- 개발 서버: `make dev` (uvicorn app.main:app --reload, http://localhost:8000)
- 테스트: `make test` (pytest)

## 구조
- 라우터는 `app/routes/`에 리소스별로 두고 `app/main.py`에서 `include_router`로 연결한다.
- `app/models.py`에 Pydantic 스키마(TodoIn/Todo)와 SQLAlchemy 모델(TodoRow)을 함께 둔다.

## 컨벤션
- 테스트는 인메모리 `app/storage.py`로 돌린다 — 실제 Postgres를 띄우지 않는다.
- 설정과 `DATABASE_URL`은 `.env`에서 읽는다(pydantic-settings); 하드코딩하지 않는다.
- 없는 리소스는 `HTTPException(status_code=404)`로 응답한다.

## 경계
- `.env`와 시크릿은 절대 커밋하지 않는다.
"""

_TD_MID = """\
# todo-api

FastAPI todo 서비스.

## 명령어
- 개발 서버 실행: `make dev`
- 테스트: `make test`

## 구조
- 라우터는 `app/routes/`에 모듈별로 두고 `app/main.py`에서 `include_router`로 연결한다.
- `app/models.py`에 Pydantic 스키마와 SQLAlchemy 모델이 함께 들어 있다.

## 참고
- 존재하지 않는 todo는 `HTTPException` 404로 응답한다.
"""

_TD_THIN = """\
# todo-api

FastAPI 기반 todo API.

- `make dev`로 개발 서버를 띄운다.
- `make test`로 테스트를 돌린다.
"""

_BD_FULL = """\
# board-api

FastAPI 게시판 CRUD API (글/댓글).

## 명령어
- 개발 서버: `make dev` (http://localhost:8000/docs)
- 테스트: `make test` (pytest)

## 구조
- 새 리소스는 `app/routers/<name>.py`에 `APIRouter(prefix=...)`로 만들고 `app/main.py`에서
  `include_router`로 연결한다.
- ORM 모델(`app/models.py`)과 Pydantic 스키마(`app/schemas.py`)를 분리한다 —
  ORM 객체를 그대로 반환하지 않는다.

## 컨벤션
- 생성(create) 엔드포인트는 HTTP 201을 반환한다.
- 없는 리소스는 `HTTPException(404)`를 반환한다.
- 목록은 `page`/`size` 쿼리로 페이지네이션한다(page는 1-based).
- 테스트는 인메모리 `app/storage.py`로 돌린다 — 실제 DB가 필요 없다.

## 경계
- `.env`와 시크릿은 절대 커밋하지 않는다.
"""

_BD_MID = """\
# board-api

게시판 CRUD API (FastAPI).

## 명령어
- 실행: `make dev`
- 테스트: `make test`

## 구조
- 리소스마다 `app/routers/<name>.py`에 `APIRouter(prefix=...)`를 만들고
  `app/main.py`에서 `include_router`한다.

## 컨벤션
- 글/댓글 생성은 201을 반환한다.
- 없는 글은 404(`HTTPException`)로 응답한다.
"""

_BD_THIN = """\
# board-api

FastAPI 게시판 API.

- `make dev`로 서버 실행.
- `make test`로 테스트.
"""

_WK_FULL = """\
# web-kanban

React + Vite + TypeScript 프론트엔드 전용 칸반 보드.

## 명령어
- 설치: `npm install`
- 개발 서버: `npm run dev` (http://localhost:5173)

## 구조
- 컴포넌트는 Board → Column → Card 구조이며, 도메인 타입은 `src/types.ts`에 둔다.

## 컨벤션
- 보드 상태는 `useBoard` 훅을 통해서만 다룬다; Column/Card는 상태 없는 presentational 컴포넌트다.
- 백엔드도 데이터 fetch도 없다 — 완전한 클라이언트 사이드 앱이다.
- 컬럼은 고정 집합 `todo`/`doing`/`done`(ColumnId)이다.
- TypeScript strict를 켜고 JSX는 자동 런타임(react-jsx)을 쓴다.

## 경계
- 백엔드/API 레이어를 추가하지 않는다; 영속화가 필요하면 클라이언트 사이드(localStorage 등)로 한다.
"""

_WK_MID = """\
# web-kanban

React + Vite + TypeScript 칸반 보드.

## 명령어
- `npm install` 후 `npm run dev`로 개발 서버 실행 (http://localhost:5173).

## 구조
- 컴포넌트 구조는 Board → Column → Card이고, 타입은 `src/types.ts`에 정의한다.

## 컨벤션
- 컬럼은 고정된 `todo`/`doing`/`done`(ColumnId) 집합이다.
- TypeScript strict 모드, JSX는 react-jsx 자동 런타임을 사용한다.
"""

_WK_THIN = """\
# web-kanban

프론트엔드 칸반 보드.

- `npm install` 후 `npm run dev`로 실행한다.
"""

# (key, project_id, author_model, claude_md, covered criterion ids)
_GOLD: list[tuple[str, str, str, str, list[str]]] = [
    ("td-full", "todo-api", "gpt-4o", _TD_FULL,
     ["cmd-run", "cmd-test", "struct-routes", "struct-models",
      "conv-inmem-tests", "conv-settings-env", "conv-404", "bound-secrets"]),
    ("td-mid", "todo-api", "gpt-4o-mini", _TD_MID,
     ["cmd-run", "cmd-test", "struct-routes", "struct-models", "conv-404"]),
    ("td-thin", "todo-api", "gpt-4o", _TD_THIN, ["cmd-run", "cmd-test"]),

    ("bd-full", "board-api", "gpt-4o-mini", _BD_FULL,
     ["cmd-run", "cmd-test", "struct-routers", "conv-orm-schema-split",
      "conv-201", "conv-404", "conv-pagination", "conv-inmem-tests", "bound-secrets"]),
    ("bd-mid", "board-api", "gpt-4o", _BD_MID,
     ["cmd-run", "cmd-test", "struct-routers", "conv-201", "conv-404"]),
    ("bd-thin", "board-api", "gpt-4o", _BD_THIN, ["cmd-run", "cmd-test"]),

    ("wk-full", "web-kanban", "gpt-4o", _WK_FULL,
     ["cmd-dev", "struct-components", "conv-state-hook", "conv-no-backend",
      "conv-columns", "conv-ts", "bound-no-api"]),
    ("wk-mid", "web-kanban", "gpt-4o-mini", _WK_MID,
     ["cmd-dev", "struct-components", "conv-columns", "conv-ts"]),
    ("wk-thin", "web-kanban", "gpt-4o-mini", _WK_THIN, ["cmd-dev"]),
]

_PANEL = {
    "_note": "Placeholder OpenAI model ids — edit to the models you actually sweep. "
             "Self-preference bias is measured across these.",
    "judge_models": ["gpt-4o-mini", "gpt-4o"],
    "author_models": ["gpt-4o-mini", "gpt-4o"],
}


def build() -> tuple[list[dict], list[dict], dict]:
    """Validate coverage labels against each project's rubric and build the fixture payloads."""

    synthetic: list[dict] = []
    gold: list[dict] = []
    for key, project_id, author_model, claude_md, covered in _GOLD:
        if project_id not in _PROJECT_INDEX:
            raise ValueError(f"{key}: unknown project {project_id}")
        criteria = get_rubric(project_id)
        valid = {c.id for c in criteria}
        bad = [cid for cid in covered if cid not in valid]
        if bad:
            raise ValueError(f"{key}: covered ids not in {project_id} rubric: {bad}")
        recall = round(len(covered) / len(criteria), 4)
        synthetic.append({
            "key": key,
            "problem_index": _PROJECT_INDEX[project_id],
            "author_model": author_model,
            "flaws": [claude_md],  # the harness interface carries the submission in flaws[0]
        })
        gold.append({"key": key, "matched_ids": covered, "recall": recall})
    return synthetic, gold, _PANEL


def main() -> None:
    fixtures_dir = Path(__file__).resolve().parents[1] / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    synthetic, gold, panel = build()
    for name, data in [
        ("synthetic_submissions.json", synthetic),
        ("human_gold.json", gold),
        ("panel_models.json", panel),
    ]:
        (fixtures_dir / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {fixtures_dir / name}")
    print(f"submissions: {len(synthetic)} | gold: {len(gold)}")


if __name__ == "__main__":
    main()
