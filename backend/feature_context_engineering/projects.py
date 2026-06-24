"""Built-in sample-project registry. Project sourcing/sizing is an open question (SPEC §7).

Each project is served whole (tree + every file's full content) so the left panel can show a
file's body on click. Directory nodes are inferred from file paths.
"""

from __future__ import annotations

from feature_context_engineering.models import FileNode, Project


def _build_files(contents: dict[str, str]) -> list[FileNode]:
    """Expand a {path: content} map into file nodes plus inferred directory nodes."""

    dirs: set[str] = set()
    nodes: list[FileNode] = [
        FileNode(path=path, kind="file", content=content) for path, content in contents.items()
    ]
    for path in contents:
        parts = path.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            dirs.add("/".join(parts[:i]))
    nodes.extend(FileNode(path=d, kind="dir") for d in dirs)
    nodes.sort(key=lambda n: n.path)
    return nodes


_TODO_API_FILES: dict[str, str] = {
    "README.md": (
        "# todo-api\n\n"
        "A small todo REST API built with **FastAPI**. Todos are persisted in PostgreSQL via\n"
        "SQLAlchemy; an in-memory fallback (`app/storage.py`) is used by the tests.\n\n"
        "## Quickstart\n\n"
        "    cp .env.example .env        # set DATABASE_URL\n"
        "    make install\n"
        "    make dev                    # http://localhost:8000  (docs at /docs)\n\n"
        "## Layout\n\n"
        "- `app/main.py`     — FastAPI app + router wiring\n"
        "- `app/routes/`     — one module per resource (todos)\n"
        "- `app/models.py`   — Pydantic schemas + SQLAlchemy model\n"
        "- `app/database.py` — engine/session + `get_db` dependency\n"
        "- `app/config.py`   — settings from environment\n"
        "- `tests/`          — pytest (uses the in-memory storage)\n\n"
        "## Commands\n\n"
        "| target | what |\n"
        "|---|---|\n"
        "| `make dev`  | run with autoreload |\n"
        "| `make test` | pytest |\n"
        "| `make lint` | ruff |\n"
    ),
    "pyproject.toml": (
        "[project]\n"
        'name = "todo-api"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.12"\n'
        "dependencies = [\n"
        '    "fastapi",\n'
        '    "uvicorn[standard]",\n'
        '    "sqlalchemy>=2.0",\n'
        '    "psycopg[binary]",\n'
        '    "pydantic-settings",\n'
        "]\n\n"
        "[project.optional-dependencies]\n"
        'dev = ["pytest", "httpx", "ruff"]\n\n'
        "[tool.ruff]\n"
        "line-length = 100\n\n"
        "[tool.pytest.ini_options]\n"
        'testpaths = ["tests"]\n'
        'pythonpath = ["."]\n'
    ),
    "Makefile": (
        "install:\n\tpip install -e \".[dev]\"\n\n"
        "dev:\n\tuvicorn app.main:app --reload\n\n"
        "test:\n\tpytest -q\n\n"
        "lint:\n\truff check .\n"
    ),
    ".env.example": (
        "# Copy to .env and fill in. Never commit the real .env.\n"
        "DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/todo\n"
        "APP_NAME=todo-api\n"
    ),
    "app/__init__.py": '"""todo-api application package."""\n',
    "app/config.py": (
        '"""Application settings, loaded from the environment (.env)."""\n\n'
        "from pydantic_settings import BaseSettings, SettingsConfigDict\n\n\n"
        "class Settings(BaseSettings):\n"
        '    model_config = SettingsConfigDict(env_file=".env")\n\n'
        '    app_name: str = "todo-api"\n'
        '    database_url: str = "postgresql+psycopg://user:password@localhost:5432/todo"\n\n\n'
        "settings = Settings()\n"
    ),
    "app/database.py": (
        '"""SQLAlchemy engine/session wiring + the FastAPI `get_db` dependency."""\n\n'
        "from collections.abc import Iterator\n\n"
        "from sqlalchemy import create_engine\n"
        "from sqlalchemy.orm import Session, sessionmaker\n\n"
        "from app.config import settings\n\n"
        "engine = create_engine(settings.database_url, future=True)\n"
        "SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)\n\n\n"
        "def get_db() -> Iterator[Session]:\n"
        "    db = SessionLocal()\n"
        "    try:\n"
        "        yield db\n"
        "    finally:\n"
        "        db.close()\n"
    ),
    "app/models.py": (
        '"""Pydantic schemas (API) + SQLAlchemy model (DB)."""\n\n'
        "from pydantic import BaseModel\n"
        "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n\n\n"
        "class Base(DeclarativeBase):\n"
        "    pass\n\n\n"
        "class TodoRow(Base):\n"
        '    __tablename__ = "todos"\n\n'
        "    id: Mapped[int] = mapped_column(primary_key=True)\n"
        "    title: Mapped[str] = mapped_column()\n"
        "    done: Mapped[bool] = mapped_column(default=False)\n\n\n"
        "class TodoIn(BaseModel):\n"
        "    title: str\n"
        "    done: bool = False\n\n\n"
        "class Todo(TodoIn):\n"
        "    id: int\n"
    ),
    "app/storage.py": (
        '"""In-memory todo storage for tests; the DB lives in app/database.py."""\n\n'
        "from app.models import Todo, TodoIn\n\n"
        "_TODOS: dict[int, Todo] = {}\n"
        "_NEXT_ID = 1\n\n\n"
        "def add(data: TodoIn) -> Todo:\n"
        "    global _NEXT_ID\n"
        "    todo = Todo(id=_NEXT_ID, **data.model_dump())\n"
        "    _TODOS[todo.id] = todo\n"
        "    _NEXT_ID += 1\n"
        "    return todo\n\n\n"
        "def list_all() -> list[Todo]:\n"
        "    return list(_TODOS.values())\n\n\n"
        "def get(todo_id: int) -> Todo | None:\n"
        "    return _TODOS.get(todo_id)\n"
    ),
    "app/main.py": (
        '"""FastAPI application entrypoint."""\n\n'
        "from fastapi import FastAPI\n\n"
        "from app.config import settings\n"
        "from app.routes import todos\n\n"
        "app = FastAPI(title=settings.app_name)\n"
        "app.include_router(todos.router)\n\n\n"
        '@app.get("/health")\n'
        "def health() -> dict[str, str]:\n"
        '    return {"status": "ok"}\n'
    ),
    "app/routes/__init__.py": '"""HTTP route modules, one per resource."""\n',
    "app/routes/todos.py": (
        '"""HTTP routes for todos."""\n\n'
        "from fastapi import APIRouter, HTTPException\n\n"
        "from app import storage\n"
        "from app.models import Todo, TodoIn\n\n"
        'router = APIRouter(prefix="/todos", tags=["todos"])\n\n\n'
        '@router.post("", response_model=Todo, status_code=201)\n'
        "def create_todo(data: TodoIn) -> Todo:\n"
        "    return storage.add(data)\n\n\n"
        '@router.get("", response_model=list[Todo])\n'
        "def list_todos() -> list[Todo]:\n"
        "    return storage.list_all()\n\n\n"
        '@router.get("/{todo_id}", response_model=Todo)\n'
        "def get_todo(todo_id: int) -> Todo:\n"
        "    todo = storage.get(todo_id)\n"
        "    if todo is None:\n"
        '        raise HTTPException(status_code=404, detail="todo not found")\n'
        "    return todo\n"
    ),
    "tests/__init__.py": '"""todo-api test suite."""\n',
    "tests/test_todos.py": (
        '"""Route tests using the in-memory storage (no DB required)."""\n\n'
        "from fastapi.testclient import TestClient\n\n"
        "from app.main import app\n\n"
        "client = TestClient(app)\n\n\n"
        "def test_create_then_fetch():\n"
        '    created = client.post("/todos", json={"title": "buy milk"})\n'
        "    assert created.status_code == 201\n"
        '    todo_id = created.json()["id"]\n\n'
        '    fetched = client.get(f"/todos/{todo_id}")\n'
        "    assert fetched.status_code == 200\n"
        '    assert fetched.json()["title"] == "buy milk"\n\n\n'
        "def test_missing_todo_404():\n"
        '    assert client.get("/todos/999").status_code == 404\n'
    ),
}


_BOARD_API_FILES: dict[str, str] = {
    "README.md": (
        "# board-api\n\n"
        "게시판 CRUD REST API (FastAPI). 글(post)과 댓글(comment)을 다룬다.\n"
        "저장소는 PostgreSQL(SQLAlchemy), 테스트는 인메모리 폴백을 쓴다.\n\n"
        "## Run\n\n    make dev      # http://localhost:8000/docs\n\n"
        "## Endpoints\n\n"
        "- `GET    /posts`               목록 (page, size 쿼리)\n"
        "- `POST   /posts`               글 작성\n"
        "- `GET    /posts/{id}`          글 조회\n"
        "- `POST   /posts/{id}/comments` 댓글 작성\n"
    ),
    "pyproject.toml": (
        "[project]\n"
        'name = "board-api"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.12"\n'
        "dependencies = [\n"
        '    "fastapi",\n'
        '    "uvicorn[standard]",\n'
        '    "sqlalchemy>=2.0",\n'
        '    "psycopg[binary]",\n'
        "]\n\n"
        "[project.optional-dependencies]\n"
        'dev = ["pytest", "httpx", "ruff"]\n'
    ),
    "Makefile": (
        "dev:\n\tuvicorn app.main:app --reload\n\n"
        "test:\n\tpytest -q\n\n"
        "lint:\n\truff check .\n"
    ),
    ".env.example": (
        "# Copy to .env. Never commit the real .env.\n"
        "DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/board\n"
    ),
    "app/__init__.py": '"""board-api application package."""\n',
    "app/database.py": (
        '"""SQLAlchemy engine/session + the get_db dependency."""\n\n'
        "from collections.abc import Iterator\n\n"
        "from sqlalchemy import create_engine\n"
        "from sqlalchemy.orm import Session, sessionmaker\n\n"
        'engine = create_engine("postgresql+psycopg://localhost/board", future=True)\n'
        "SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)\n\n\n"
        "def get_db() -> Iterator[Session]:\n"
        "    db = SessionLocal()\n"
        "    try:\n"
        "        yield db\n"
        "    finally:\n"
        "        db.close()\n"
    ),
    "app/models.py": (
        '"""SQLAlchemy ORM models: Post 1—N Comment."""\n\n'
        "from sqlalchemy import ForeignKey\n"
        "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship\n\n\n"
        "class Base(DeclarativeBase):\n"
        "    pass\n\n\n"
        "class Post(Base):\n"
        '    __tablename__ = "posts"\n\n'
        "    id: Mapped[int] = mapped_column(primary_key=True)\n"
        "    title: Mapped[str]\n"
        "    body: Mapped[str]\n\n\n"
        "class Comment(Base):\n"
        '    __tablename__ = "comments"\n\n'
        "    id: Mapped[int] = mapped_column(primary_key=True)\n"
        '    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))\n'
        "    body: Mapped[str]\n"
    ),
    "app/schemas.py": (
        '"""Pydantic request/response schemas."""\n\n'
        "from pydantic import BaseModel\n\n\n"
        "class PostIn(BaseModel):\n"
        "    title: str\n"
        "    body: str\n\n\n"
        "class Post(PostIn):\n"
        "    id: int\n\n\n"
        "class CommentIn(BaseModel):\n"
        "    body: str\n\n\n"
        "class Comment(CommentIn):\n"
        "    id: int\n"
        "    post_id: int\n"
    ),
    "app/storage.py": (
        '"""In-memory store for tests; production uses the DB (app/database.py)."""\n\n'
        "from app.schemas import Comment, CommentIn, Post, PostIn\n\n"
        "_POSTS: dict[int, Post] = {}\n"
        "_COMMENTS: list[Comment] = []\n"
        "_SEQ = {'post': 0, 'comment': 0}\n\n\n"
        "def _next(kind: str) -> int:\n"
        "    _SEQ[kind] += 1\n"
        "    return _SEQ[kind]\n\n\n"
        "def create_post(data: PostIn) -> Post:\n"
        "    post = Post(id=_next('post'), **data.model_dump())\n"
        "    _POSTS[post.id] = post\n"
        "    return post\n\n\n"
        "def list_posts(page: int = 1, size: int = 20) -> list[Post]:\n"
        "    start = (page - 1) * size\n"
        "    return list(_POSTS.values())[start:start + size]\n\n\n"
        "def get_post(post_id: int) -> Post | None:\n"
        "    return _POSTS.get(post_id)\n\n\n"
        "def add_comment(post_id: int, data: CommentIn) -> Comment:\n"
        "    c = Comment(id=_next('comment'), post_id=post_id, **data.model_dump())\n"
        "    _COMMENTS.append(c)\n"
        "    return c\n"
    ),
    "app/routers/__init__.py": '"""HTTP routers, one module per resource."""\n',
    "app/routers/posts.py": (
        '"""CRUD routes for posts."""\n\n'
        "from fastapi import APIRouter, HTTPException\n\n"
        "from app import storage\n"
        "from app.schemas import Post, PostIn\n\n"
        'router = APIRouter(prefix="/posts", tags=["posts"])\n\n\n'
        '@router.get("", response_model=list[Post])\n'
        "def list_posts(page: int = 1, size: int = 20) -> list[Post]:\n"
        "    return storage.list_posts(page, size)\n\n\n"
        '@router.post("", response_model=Post, status_code=201)\n'
        "def create_post(data: PostIn) -> Post:\n"
        "    return storage.create_post(data)\n\n\n"
        '@router.get("/{post_id}", response_model=Post)\n'
        "def get_post(post_id: int) -> Post:\n"
        "    post = storage.get_post(post_id)\n"
        "    if post is None:\n"
        '        raise HTTPException(status_code=404, detail="post not found")\n'
        "    return post\n"
    ),
    "app/routers/comments.py": (
        '"""Routes for comments under a post."""\n\n'
        "from fastapi import APIRouter, HTTPException\n\n"
        "from app import storage\n"
        "from app.schemas import Comment, CommentIn\n\n"
        'router = APIRouter(prefix="/posts/{post_id}/comments", tags=["comments"])\n\n\n'
        '@router.post("", response_model=Comment, status_code=201)\n'
        "def add_comment(post_id: int, data: CommentIn) -> Comment:\n"
        "    if storage.get_post(post_id) is None:\n"
        '        raise HTTPException(status_code=404, detail="post not found")\n'
        "    return storage.add_comment(post_id, data)\n"
    ),
    "app/main.py": (
        '"""FastAPI app for the board service."""\n\n'
        "from fastapi import FastAPI\n\n"
        "from app.routers import comments, posts\n\n"
        'app = FastAPI(title="board-api")\n'
        "app.include_router(posts.router)\n"
        "app.include_router(comments.router)\n"
    ),
    "tests/__init__.py": '"""board-api test suite."""\n',
    "tests/test_posts.py": (
        '"""Post CRUD tests (in-memory storage, no DB)."""\n\n'
        "from fastapi.testclient import TestClient\n\n"
        "from app.main import app\n\n"
        "client = TestClient(app)\n\n\n"
        "def test_create_then_list():\n"
        '    client.post("/posts", json={"title": "hi", "body": "first"})\n'
        '    res = client.get("/posts")\n'
        "    assert res.status_code == 200\n"
        "    assert len(res.json()) >= 1\n"
    ),
}


_WEB_KANBAN_FILES: dict[str, str] = {
    "README.md": (
        "# web-kanban\n\n"
        "프론트엔드 전용 칸반 보드 (React + Vite + TypeScript). **백엔드 없음** —\n"
        "상태는 브라우저 로컬(useState)에만 둔다.\n\n"
        "## Run\n\n"
        "    npm install\n"
        "    npm run dev      # http://localhost:5173\n\n"
        "## Layout\n\n"
        "- `src/App.tsx`            보드 셸\n"
        "- `src/components/`        Board · Column · Card\n"
        "- `src/hooks/useBoard.ts`  보드 상태(이동/추가)\n"
        "- `src/types.ts`           도메인 타입\n"
    ),
    "package.json": (
        "{\n"
        '  "name": "web-kanban",\n'
        '  "private": true,\n'
        '  "type": "module",\n'
        '  "scripts": {\n'
        '    "dev": "vite",\n'
        '    "build": "tsc && vite build",\n'
        '    "preview": "vite preview"\n'
        "  },\n"
        '  "dependencies": {\n'
        '    "react": "^18.3.1",\n'
        '    "react-dom": "^18.3.1"\n'
        "  },\n"
        '  "devDependencies": {\n'
        '    "@vitejs/plugin-react": "^4.3.0",\n'
        '    "typescript": "^5.4.0",\n'
        '    "vite": "^5.4.0"\n'
        "  }\n"
        "}\n"
    ),
    "tsconfig.json": (
        "{\n"
        '  "compilerOptions": {\n'
        '    "target": "ES2022",\n'
        '    "lib": ["ES2022", "DOM", "DOM.Iterable"],\n'
        '    "module": "ESNext",\n'
        '    "moduleResolution": "Bundler",\n'
        '    "jsx": "react-jsx",\n'
        '    "strict": true,\n'
        '    "noEmit": true\n'
        "  },\n"
        '  "include": ["src"]\n'
        "}\n"
    ),
    "vite.config.ts": (
        'import react from "@vitejs/plugin-react";\n'
        'import { defineConfig } from "vite";\n\n'
        "export default defineConfig({\n"
        "  plugins: [react()],\n"
        "});\n"
    ),
    "index.html": (
        "<!doctype html>\n"
        '<html lang="ko">\n'
        "  <head>\n"
        '    <meta charset="UTF-8" />\n'
        "    <title>web-kanban</title>\n"
        "  </head>\n"
        "  <body>\n"
        '    <div id="root"></div>\n'
        '    <script type="module" src="/src/main.tsx"></script>\n'
        "  </body>\n"
        "</html>\n"
    ),
    "src/types.ts": (
        'export type ColumnId = "todo" | "doing" | "done";\n\n'
        "export interface Card {\n"
        "  id: string;\n"
        "  title: string;\n"
        "  column: ColumnId;\n"
        "}\n"
    ),
    "src/main.tsx": (
        'import { StrictMode } from "react";\n'
        'import { createRoot } from "react-dom/client";\n\n'
        'import { App } from "./App";\n\n'
        'const root = document.getElementById("root");\n'
        "if (root) {\n"
        "  createRoot(root).render(\n"
        "    <StrictMode>\n"
        "      <App />\n"
        "    </StrictMode>,\n"
        "  );\n"
        "}\n"
    ),
    "src/hooks/useBoard.ts": (
        'import { useState } from "react";\n\n'
        'import type { Card, ColumnId } from "../types";\n\n'
        "const SEED: Card[] = [\n"
        '  { id: "1", title: "디자인 시안", column: "todo" },\n'
        '  { id: "2", title: "API 연동", column: "doing" },\n'
        "];\n\n"
        "export function useBoard() {\n"
        "  const [cards, setCards] = useState<Card[]>(SEED);\n\n"
        "  function move(id: string, column: ColumnId) {\n"
        "    setCards((cs) => cs.map((c) => (c.id === id ? { ...c, column } : c)));\n"
        "  }\n\n"
        "  function add(title: string, column: ColumnId) {\n"
        "    setCards((cs) => [...cs, { id: String(cs.length + 1), title, column }]);\n"
        "  }\n\n"
        "  return { cards, move, add };\n"
        "}\n"
    ),
    "src/components/Card.tsx": (
        'import type { Card as CardModel } from "../types";\n\n'
        "export function Card({ card }: { card: CardModel }) {\n"
        '  return <div className="card">{card.title}</div>;\n'
        "}\n"
    ),
    "src/components/Column.tsx": (
        'import type { Card as CardModel, ColumnId } from "../types";\n'
        'import { Card } from "./Card";\n\n'
        "interface ColumnProps {\n"
        "  id: ColumnId;\n"
        "  cards: CardModel[];\n"
        "}\n\n"
        "export function Column({ id, cards }: ColumnProps) {\n"
        "  return (\n"
        '    <section className="column">\n'
        "      <h2>{id}</h2>\n"
        "      {cards.map((c) => (\n"
        "        <Card key={c.id} card={c} />\n"
        "      ))}\n"
        "    </section>\n"
        "  );\n"
        "}\n"
    ),
    "src/components/Board.tsx": (
        'import { useBoard } from "../hooks/useBoard";\n'
        'import type { ColumnId } from "../types";\n'
        'import { Column } from "./Column";\n\n'
        'const COLUMNS: ColumnId[] = ["todo", "doing", "done"];\n\n'
        "export function Board() {\n"
        "  const { cards } = useBoard();\n"
        "  return (\n"
        '    <div className="board">\n'
        "      {COLUMNS.map((id) => (\n"
        "        <Column key={id} id={id} cards={cards.filter((c) => c.column === id)} />\n"
        "      ))}\n"
        "    </div>\n"
        "  );\n"
        "}\n"
    ),
    "src/App.tsx": (
        'import { Board } from "./components/Board";\n\n'
        "export function App() {\n"
        "  return (\n"
        "    <main>\n"
        "      <h1>web-kanban</h1>\n"
        "      <Board />\n"
        "    </main>\n"
        "  );\n"
        "}\n"
    ),
}


_CX_CHURN_RADAR_FILES: dict[str, str] = {
    "README.md": (
        "# cx-churn-radar\n\n"
        "구독형 커머스 고객사의 CX 로그로 **고객 이탈 징후**를 탐지하고\n"
        "위험 고객에 Agentic 대응을 트리거하는 서비스.\n\n"
        "AXOps팀(데이터 파이프라인 + 이탈 스코어링 ML + "
        "FastAPI 스코어링 API + 알림 에이전트) 운영.\n"
        "스택: Python 3.12 / FastAPI / PostgreSQL / Airflow. "
        "배치 주기: 일별(스코어링) + 시간별(수집).\n\n"
        "## 구조\n\n"
        "- `app/pipeline/` — 이벤트 수집·전처리 (`ingest.py`, `preprocess.py`)\n"
        "- `app/scoring/`  — ML 모델 로딩·스코어 계산 (`model.py`, `scorer.py`)\n"
        "- `app/api/`      — FastAPI 라우터·스키마 (`routes.py`, `schemas.py`)\n"
        "- `app/pii.py`    — PII 마스킹 헬퍼 (반드시 이 모듈을 통해 처리)\n"
        "- `app/config.py` — 환경변수 기반 설정\n"
        "- `dags/`         — Airflow DAG (DAG ID 규칙: `{domain}_{task}_{schedule}`)\n"
        "- `tests/`        — pytest, 인메모리 폴백 (실 DB 불필요)\n\n"
        "## 명령\n\n"
        "```bash\n"
        "uv sync                          # 또는 pip install -e \".[dev]\"\n"
        "ruff check .                     # 린트\n"
        "pytest -q                        # 테스트 (인메모리, DB 불필요)\n"
        "uvicorn app.main:app --reload    # 개발 서버 http://localhost:8000\n"
        "```\n\n"
        "## 이벤트 스키마\n\n"
        "| 컬럼 | 설명 |\n"
        "|---|---|\n"
        "| `customer_token` | PII 마스킹된 고객 식별자 (`cust_xxxx`) |\n"
        "| `event_type` | `view·cart·purchase·login·support_ticket·refund·cancel` 7가지 |\n"
        "| `ts` | 이벤트 발생 시각 ISO 8601 (결측 가능) |\n"
        "| `session_id` | 세션 식별자 |\n"
        "| `metadata` | 이벤트별 부가 JSON |\n\n"
        "## 중요 규칙\n\n"
        "- **평문 PII 금지**: 이름·이메일·전화번호는 "
        "`app.pii.mask_customer()` 호출 후에만 저장·응답\n"
        "- **데이터 누수 금지**: `build_features(events, score_date)`에서 "
        "`score_date` 이후 데이터 절대 사용 불가\n"
        "- **실 DB 금지(테스트)**: 테스트는 반드시 인메모리 폴백(`tests/conftest.py`) 사용\n"
        "- **모델 버저닝**: 아티팩트 파일명에 버전 포함 (`model_v{n}.pkl`), "
        "`MODEL_PATH` 환경변수로 경로 지정\n"
        "- **DAG 네이밍**: `{domain}_{task}_{schedule}` 형식 "
        "(예: `churn_score_daily`, `event_ingest_hourly`)\n"
    ),
    "pyproject.toml": (
        "[project]\n"
        'name = "cx-churn-radar"\n'
        'version = "0.3.7"\n'
        'requires-python = ">=3.12"\n'
        "dependencies = [\n"
        '    "fastapi",\n'
        '    "uvicorn[standard]",\n'
        '    "sqlalchemy>=2.0",\n'
        '    "psycopg[binary]",\n'
        '    "pydantic-settings",\n'
        '    "scikit-learn>=1.4",\n'
        "]\n\n"
        "[project.optional-dependencies]\n"
        'dev = ["pytest", "httpx", "ruff"]\n\n'
        "[tool.ruff]\n"
        "line-length = 100\n\n"
        "[tool.pytest.ini_options]\n"
        'testpaths = ["tests"]\n'
        'pythonpath = ["."]\n'
    ),
    ".env.example": (
        "# Copy to .env. Never commit the real .env.\n"
        "DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/churn\n"
        "MODEL_PATH=models/model_v1.pkl\n"
        "API_SECRET_KEY=replace-me\n"
    ),
    "app/__init__.py": '"""cx-churn-radar application package."""\n',
    "app/config.py": (
        '"""환경변수 기반 설정. 모든 설정은 .env에서 읽는다 — 코드에 하드코딩 금지."""\n\n'
        "from pydantic_settings import BaseSettings, SettingsConfigDict\n\n\n"
        "class Settings(BaseSettings):\n"
        '    model_config = SettingsConfigDict(env_file=".env")\n\n'
        '    database_url: str = "postgresql+psycopg://user:password@localhost:5432/churn"\n'
        '    model_path: str = "models/model_v1.pkl"\n'
        '    api_secret_key: str = "dev-only"\n\n\n'
        "settings = Settings()\n"
    ),
    "app/pii.py": (
        '"""PII 마스킹 헬퍼.\n\n'
        "고객 식별자(이름·이메일·전화번호)는 이 모듈을 통해서만 처리한다.\n"
        "평문 PII를 DB·로그·API 응답에 기록하는 것은 **금지된 경계**다.\n"
        "다른 모듈은 직접 마스킹 로직을 구현하지 않고 반드시 이 함수를 호출한다.\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "import hashlib\n"
        "import re\n\n"
        "_PHONE_RE = re.compile(r\"(\\d{2,3})-(\\d{3,4})-(\\d{4})\")\n\n\n"
        "def mask_customer(raw_id: str) -> str:\n"
        '    """고객 식별자를 결정론적 토큰으로 변환한다 (같은 입력 → 같은 cust_xxxx).\n\n'
        "    평문 이름·이메일·전화번호 등 어떤 PII도 입력으로 받을 수 있다;\n"
        "    반환값은 항상 `cust_<8hex>` 형식이라 재식별 불가.\n"
        '    """\n'
        "    digest = hashlib.sha256(raw_id.encode()).hexdigest()[:8]\n"
        '    return f"cust_{digest}"\n\n\n'
        "def mask_phone(phone: str) -> str:\n"
        '    """010-1234-5678 → 010-****-5678 (국번+뒷자리 보존, 가운데 마스킹)."""\n'
        '    return _PHONE_RE.sub(r"\\1-****-\\3", phone)\n\n\n'
        "def mask_email(email: str) -> str:\n"
        '    """user@example.com → us**@example.com."""\n'
        "    local, _, domain = email.partition(\"@\")\n"
        '    return f"{local[:2]}**@{domain}" if len(local) > 2 else f"**@{domain}"\n'
    ),
    "app/pipeline/__init__.py": '"""이벤트 수집·전처리 파이프라인."""\n',
    "app/pipeline/ingest.py": (
        '"""이벤트 수집 파이프라인.\n\n'
        "처리 순서:\n"
        "1. 스키마 드리프트 필터 — 알 수 없는 event_type 제거\n"
        "2. 중복 이벤트 제거 — session_id + event_type + ts 기준\n"
        "3. PII 마스킹 — customer_token은 반드시 app.pii.mask_customer() 통과 후 저장\n"
        "   (이름·이메일·전화번호 원본은 절대 저장하지 않는다)\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "import hashlib\n\n"
        "from app.pii import mask_customer\n\n"
        "EVENT_TYPES = frozenset({\n"
        '    "view", "cart", "purchase", "login",\n'
        '    "support_ticket", "refund", "cancel",\n'
        "})\n\n\n"
        "def _dedup_key(event: dict) -> str:\n"
        '    raw = f"{event.get(\'session_id\')}|{event.get(\'event_type\')}|{event.get(\'ts\')}"\n'
        "    return hashlib.md5(raw.encode()).hexdigest()\n\n\n"
        "def ingest(raw_events: list[dict]) -> list[dict]:\n"
        '    """원시 이벤트 목록을 정제하여 반환한다.\n\n'
        "    - 알 수 없는 event_type 제거 (스키마 드리프트 내성)\n"
        "    - 중복 이벤트 제거\n"
        "    - customer_token PII 마스킹 적용\n"
        "    - ts 결측(None) 허용 — preprocess 단계에서 처리\n"
        '    """\n'
        "    seen: set[str] = set()\n"
        "    out: list[dict] = []\n"
        "    for e in raw_events:\n"
        "        if e.get(\"event_type\") not in EVENT_TYPES:\n"
        "            continue\n"
        "        key = _dedup_key(e)\n"
        "        if key in seen:\n"
        "            continue\n"
        "        seen.add(key)\n"
        "        out.append({\n"
        '            "customer_token": mask_customer(e["customer_token"]),\n'
        '            "event_type": e["event_type"],\n'
        '            "ts": e.get("ts"),\n'
        '            "session_id": e.get("session_id"),\n'
        '            "metadata": e.get("metadata", {}),\n'
        "        })\n"
        "    return out\n"
    ),
    "app/pipeline/preprocess.py": (
        '"""피처 엔지니어링.\n\n'
        "주의: score_date 이전 데이터만 사용한다.\n"
        "미래 데이터 유입(데이터 누수)은 모델 성능을 부풀리므로 엄격히 금지한다.\n"
        "늦게 도착하는 이벤트(late-arriving)는 score_date 기준으로 필터링된다.\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "from datetime import datetime\n\n\n"
        "def build_features(events: list[dict], score_date: datetime) -> dict:\n"
        '    """score_date 이전 이벤트로만 피처를 계산한다.\n\n'
        "    score_date 이후 이벤트는 절대 포함하지 않는다 — 미래 데이터 누수 방지.\n"
        "    ts가 None인 이벤트는 안전하게 제외한다.\n"
        '    """\n'
        "    valid = [\n"
        "        e for e in events\n"
        "        if e.get(\"ts\") is not None\n"
        "        and datetime.fromisoformat(e[\"ts\"]) <= score_date\n"
        "    ]\n"
        "    n = len(valid)\n"
        "    n_support = sum(1 for e in valid if e[\"event_type\"] == \"support_ticket\")\n"
        "    n_cancel = sum(1 for e in valid if e[\"event_type\"] == \"cancel\")\n"
        "    last_active = max(\n"
        "        (datetime.fromisoformat(e[\"ts\"]) for e in valid), default=None\n"
        "    )\n"
        "    days_inactive = (score_date - last_active).days if last_active else 999\n"
        "    return {\n"
        '        "n_events": n,\n'
        '        "n_support": n_support,\n'
        '        "n_cancel": n_cancel,\n'
        '        "days_inactive": days_inactive,\n'
        '        "cancel_rate": round(n_cancel / n, 4) if n else 0.0,\n'
        "    }\n"
    ),
    "app/scoring/__init__.py": '"""ML 모델 로딩·스코어 계산."""\n',
    "app/scoring/model.py": (
        '"""이탈 스코어링 ML 모델 로더.\n\n'
        "모델 아티팩트는 MODEL_PATH 환경변수로 지정하며 파일명에 버전을 포함한다\n"
        "(예: model_v3.pkl). 새 모델 배포 시 MODEL_PATH 값만 갱신한다.\n"
        "로드된 모델은 프로세스 내에서 싱글톤으로 관리한다.\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "import os\n"
        "import pickle\n\n"
        "_MODEL: object | None = None\n\n\n"
        "def load_model(path: str | None = None) -> object:\n"
        '    """MODEL_PATH(또는 path 인자)에서 pkl 아티팩트를 로드한다.\n\n'
        "    파일명 규칙: model_v{n}.pkl (예: model_v1.pkl, model_v12.pkl).\n"
        '    """\n'
        "    global _MODEL\n"
        "    resolved = path or os.environ.get(\"MODEL_PATH\", \"models/model_v1.pkl\")\n"
        "    with open(resolved, \"rb\") as f:\n"
        "        _MODEL = pickle.load(f)\n"
        "    return _MODEL\n\n\n"
        "def get_model() -> object:\n"
        "    if _MODEL is None:\n"
        "        raise RuntimeError("
        "\"모델이 로드되지 않았습니다. load_model()을 먼저 호출하세요.\")\n"
        "    return _MODEL\n"
    ),
    "app/scoring/scorer.py": (
        '"""이탈 위험도 스코어 계산.\n\n'
        "규칙 기반 베이스라인. 모델 교체 시 이 모듈의 score_churn_risk 함수만 수정한다.\n"
        '"""\n\n'
        "from __future__ import annotations\n\n\n"
        "def score_churn_risk(features: dict) -> float:\n"
        '    """가중 규칙으로 이탈 위험도를 0.0~1.0으로 반환한다.\n\n'
        "    피처: cancel_rate, n_support, days_inactive (build_features 출력과 동일).\n"
        '    """\n'
        "    score = 0.0\n"
        "    score += min(features.get(\"cancel_rate\", 0.0) * 0.6, 0.3)\n"
        "    score += min(features.get(\"n_support\", 0) * 0.047, 0.3)\n"
        "    if features.get(\"days_inactive\", 0) > 30:\n"
        "        score += 0.2\n"
        "    if features.get(\"days_inactive\", 0) > 90:\n"
        "        score += 0.1\n"
        "    return round(min(score, 1.0), 4)\n"
    ),
    "app/api/__init__.py": '"""FastAPI 라우터·스키마."""\n',
    "app/api/schemas.py": (
        '"""API 요청/응답 Pydantic 스키마.\n\n'
        "응답에 평문 PII를 포함하지 않는다. customer_token(cust_xxxx 형태)만 사용.\n"
        '"""\n\n'
        "from pydantic import BaseModel\n\n\n"
        "class ScoreRequest(BaseModel):\n"
        "    customer_token: str  # cust_xxxx 형태 — 평문 이름/이메일 금지\n"
        "    score_date: str      # ISO 8601\n\n\n"
        "class ScoreResponse(BaseModel):\n"
        "    customer_token: str\n"
        "    churn_risk: float    # 0.0~1.0\n"
        "    scored_at: str       # ISO 8601\n"
    ),
    "app/api/routes.py": (
        '"""FastAPI 라우터: 이탈 스코어링 엔드포인트."""\n\n'
        "from datetime import datetime, timezone\n\n"
        "from fastapi import APIRouter, HTTPException\n\n"
        "from app.api.schemas import ScoreRequest, ScoreResponse\n"
        "from app.scoring.scorer import score_churn_risk\n\n"
        'router = APIRouter(prefix="/scores", tags=["scores"])\n\n\n'
        '@router.post("", response_model=ScoreResponse, status_code=201)\n'
        "def create_score(req: ScoreRequest) -> ScoreResponse:\n"
        "    try:\n"
        "        datetime.fromisoformat(req.score_date)\n"
        "    except ValueError:\n"
        "        raise HTTPException("
        'status_code=400, detail="score_date는 ISO 8601 형식이어야 합니다.")\n'
        "    features = {\"cancel_rate\": 0.0, \"n_support\": 0, \"days_inactive\": 0}\n"
        "    risk = score_churn_risk(features)\n"
        "    return ScoreResponse(\n"
        "        customer_token=req.customer_token,\n"
        "        churn_risk=risk,\n"
        "        scored_at=datetime.now(timezone.utc).isoformat(),\n"
        "    )\n"
    ),
    "app/main.py": (
        '"""FastAPI 앱 진입점."""\n\n'
        "from fastapi import FastAPI\n\n"
        "from app.api.routes import router\n\n"
        'app = FastAPI(title="cx-churn-radar")\n'
        "app.include_router(router)\n\n\n"
        '@app.get("/health")\n'
        "def health() -> dict[str, str]:\n"
        '    return {"status": "ok"}\n'
    ),
    "dags/__init__.py": '"""Airflow DAG 모음. DAG ID 규칙: {domain}_{task}_{schedule}."""\n',
    "dags/churn_score_daily_dag.py": (
        '"""DAG: churn_score_daily\n\n'
        "DAG ID 규칙: {domain}_{task}_{schedule}\n"
        "  domain   = churn\n"
        "  task     = score\n"
        "  schedule = daily\n\n"
        "매일 자정(KST) 전체 고객의 이탈 스코어를 갱신한다.\n"
        "score_date = 전날 자정 (미래 데이터 누수 방지용 경계값).\n"
        '"""\n\n'
        "from datetime import datetime, timedelta\n\n"
        "DAG_ID = \"churn_score_daily\"\n\n"
        "default_args = {\n"
        '    "owner": "axops",\n'
        '    "retries": 2,\n'
        "    \"retry_delay\": timedelta(minutes=5),\n"
        "}\n\n"
        "# dag = DAG(\n"
        "#     dag_id=DAG_ID,\n"
        '#     schedule_interval="0 15 * * *",  # 자정 KST\n'
        "#     start_date=datetime(2024, 3, 1),\n"
        "#     catchup=False,\n"
        '#     tags=["churn", "scoring"],\n'
        "# )\n"
    ),
    "dags/event_ingest_hourly_dag.py": (
        '"""DAG: event_ingest_hourly\n\n'
        "DAG ID 규칙: {domain}_{task}_{schedule}\n"
        "  domain   = event\n"
        "  task     = ingest\n"
        "  schedule = hourly\n\n"
        "CX 로그 소스에서 이벤트를 수집하고 인제스트 파이프라인을 실행한다.\n"
        "늦게 도착하는 이벤트(late-arriving) 처리 포함.\n"
        '"""\n\n'
        "DAG_ID = \"event_ingest_hourly\"\n"
    ),
    "tests/__init__.py": '"""cx-churn-radar 테스트 스위트."""\n',
    "tests/conftest.py": (
        '"""공유 픽스처.\n\n'
        "실제 PostgreSQL 없이 인메모리로 테스트한다.\n"
        "DATABASE_URL=sqlite:///:memory: 로 오버라이드하여 모든 DB 접근을 인메모리로 처리한다.\n"
        "절대로 테스트에서 실제 PostgreSQL 컨테이너를 기동하지 않는다.\n"
        '"""\n\n'
        "import os\n\n"
        "import pytest\n\n"
        'os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")\n'
        'os.environ.setdefault("MODEL_PATH", "tests/fixtures/model_v1.pkl")\n\n\n'
        "@pytest.fixture\n"
        "def sample_events() -> list[dict]:\n"
        '    """현실적인 더러운 이벤트 샘플 (중복·결측 ts 포함)."""\n'
        "    return [\n"
        "        {\"customer_token\": \"user_7f3a1b\", \"event_type\": \"view\",\n"
        '         "ts": "2024-03-11T09:23:47", "session_id": "s_a91c", "metadata": {}},\n'
        "        {\"customer_token\": \"user_7f3a1b\", \"event_type\": \"cart\",\n"
        '         "ts": "2024-03-11T09:31:08", "session_id": "s_a91c", "metadata": {}},\n'
        "        {\"customer_token\": \"user_7f3a1b\", \"event_type\": \"cancel\",\n"
        '         "ts": "2024-03-13T14:17:33", "session_id": "s_b02d", "metadata": {}},\n'
        "        {\"customer_token\": \"user_c82e4d\", \"event_type\": \"support_ticket\",\n"
        '         "ts": "2024-03-12T07:52:19", "session_id": "s_c13f",\n'
        '         "metadata": {"issue": "결제 오류 코드 E-2291"}},\n'
        "        # 중복 이벤트 (실제 파이프라인에서 발생하는 at-least-once 딜리버리)\n"
        "        {\"customer_token\": \"user_c82e4d\", \"event_type\": \"support_ticket\",\n"
        '         "ts": "2024-03-12T07:52:19", "session_id": "s_c13f",\n'
        '         "metadata": {"issue": "결제 오류 코드 E-2291"}},\n'
        "        # ts 결측 (센서 오류)\n"
        "        {\"customer_token\": \"user_9a4c7e\", \"event_type\": \"login\",\n"
        '         "ts": None, "session_id": "s_d24g", "metadata": {}},\n'
        "    ]\n"
    ),
    "tests/test_ingest.py": (
        '"""수집 파이프라인 단위 테스트 — 인메모리, DB 불필요."""\n\n'
        "from app.pipeline.ingest import EVENT_TYPES, ingest\n"
        "from app.pii import mask_customer, mask_phone\n\n\n"
        "def test_dedup_removes_exact_duplicates(sample_events):\n"
        "    result = ingest(sample_events)\n"
        "    tickets = [e for e in result if e[\"event_type\"] == \"support_ticket\"]\n"
        "    assert len(tickets) == 1\n\n\n"
        "def test_pii_tokenized_in_output(sample_events):\n"
        "    result = ingest(sample_events)\n"
        "    for e in result:\n"
        '        assert e["customer_token"].startswith("cust_"), e["customer_token"]\n'
        '        assert "user_" not in e["customer_token"]\n\n\n'
        "def test_null_ts_preserved(sample_events):\n"
        "    result = ingest(sample_events)\n"
        '    null_events = [e for e in result if e["ts"] is None]\n'
        "    assert len(null_events) == 1\n\n\n"
        "def test_unknown_event_type_filtered():\n"
        '    events = [{"customer_token": "u1", "event_type": "click", "ts": "2024-01-01", '
        '"session_id": "s1", "metadata": {}}]\n'
        "    assert ingest(events) == []\n\n\n"
        "def test_mask_phone_partial():\n"
        '    assert mask_phone("010-1234-5678") == "010-****-5678"\n'
        '    assert mask_phone("02-999-1234") == "02-****-1234"\n\n\n'
        "def test_mask_customer_deterministic():\n"
        '    t1 = mask_customer("user@example.com")\n'
        '    t2 = mask_customer("user@example.com")\n'
        "    assert t1 == t2\n"
        '    assert t1 != mask_customer("other@example.com")\n'
        '    assert t1.startswith("cust_")\n'
    ),
    "tests/test_scoring.py": (
        '"""스코어링·전처리 단위 테스트 — 인메모리, DB 불필요."""\n\n'
        "from datetime import datetime\n\n"
        "from app.pipeline.preprocess import build_features\n"
        "from app.scoring.scorer import score_churn_risk\n\n\n"
        "def test_high_risk_features_score_above_threshold():\n"
        "    features = {\"cancel_rate\": 0.47, \"n_support\": 6, \"days_inactive\": 53}\n"
        "    assert score_churn_risk(features) >= 0.6\n\n\n"
        "def test_active_customer_scores_below_threshold():\n"
        "    features = {\"cancel_rate\": 0.0, \"n_support\": 0, \"days_inactive\": 3}\n"
        "    assert score_churn_risk(features) < 0.15\n\n\n"
        "def test_score_bounded_0_to_1():\n"
        "    features = {\"cancel_rate\": 1.0, \"n_support\": 99, \"days_inactive\": 999}\n"
        "    assert 0.0 <= score_churn_risk(features) <= 1.0\n\n\n"
        "def test_future_events_excluded_by_score_date():\n"
        "    score_date = datetime(2024, 3, 17, 0, 0, 0)\n"
        "    events = [\n"
        "        {\"customer_token\": \"cust_ab3c\", \"event_type\": \"cancel\",\n"
        '         "ts": "2024-03-16T22:41:07", "session_id": "s1", "metadata": {}},\n'
        "        {\"customer_token\": \"cust_ab3c\", \"event_type\": \"purchase\",\n"
        '         "ts": "2024-03-18T08:13:52", "session_id": "s2", "metadata": {}},\n'
        "    ]\n"
        "    features = build_features(events, score_date)\n"
        "    assert features[\"n_events\"] == 1  # 미래 이벤트 제외\n"
        "    assert features[\"n_cancel\"] == 1\n\n\n"
        "def test_null_ts_events_excluded():\n"
        "    score_date = datetime(2024, 3, 17)\n"
        "    events = [{\"customer_token\": \"cust_xy9z\", \"event_type\": \"view\",\n"
        '              "ts": None, "session_id": "s3", "metadata": {}}]\n'
        "    features = build_features(events, score_date)\n"
        "    assert features[\"n_events\"] == 0\n"
    ),
}


_PROJECTS: dict[str, Project] = {
    "todo-api": Project(
        id="todo-api",
        title="todo-api (FastAPI)",
        brief=(
            "FastAPI로 만든 작은 할 일(todo) REST API. "
            "PostgreSQL(SQLAlchemy)로 영속화하고 테스트는 인메모리 저장소를 폴백으로 쓴다. "
            "환경설정·DB 세션·라우팅이 모듈로 분리돼 있다. "
            "에이전트가 이 프로젝트에서 효율적으로 작업하도록 CLAUDE.md를 작성하세요."
        ),
        files=_build_files(_TODO_API_FILES),
    ),
    "board-api": Project(
        id="board-api",
        title="board-api (FastAPI · 게시판 CRUD)",
        brief=(
            "FastAPI 게시판 CRUD API. 글(post)과 댓글(comment)을 다루며 목록은 페이지네이션된다. "
            "ORM 모델(models)·스키마(schemas)·라우터(routers)가 분리돼 있고 테스트는 인메모리다. "
            "에이전트가 이 프로젝트에서 효율적으로 작업하도록 CLAUDE.md를 작성하세요."
        ),
        files=_build_files(_BOARD_API_FILES),
    ),
    "web-kanban": Project(
        id="web-kanban",
        title="web-kanban (React · 프론트엔드 전용)",
        brief=(
            "백엔드 없는 프론트엔드 전용 칸반 보드. React + Vite + TypeScript로 구성되고 "
            "상태는 브라우저 로컬(useState)에만 둔다. 컴포넌트·훅·타입이 분리돼 있다. "
            "에이전트가 이 프로젝트에서 효율적으로 작업하도록 CLAUDE.md를 작성하세요."
        ),
        files=_build_files(_WEB_KANBAN_FILES),
    ),
    "cx-churn-radar": Project(
        id="cx-churn-radar",
        title="cx-churn-radar (FastAPI · ML 파이프라인 · AXOps)",
        brief=(
            "구독형 커머스 고객사의 CX 로그로 고객 이탈 징후를 탐지하고 "
            "위험 고객에 Agentic 대응을 트리거하는 서비스. "
            "AXOps팀이 운영하며 데이터 파이프라인(수집·전처리)·이탈 스코어링 ML·"
            "FastAPI 스코어링 API·Airflow DAG로 구성된다. "
            "PII 마스킹·인메모리 테스트 폴백·DAG 네이밍 컨벤션·모델 버저닝 등 "
            "팀 내 암묵적 규약이 코드 전반에 내재돼 있다. "
            "이 레포에서 에이전트가 효율적으로 일하도록 CLAUDE.md를 작성하라."
        ),
        files=_build_files(_CX_CHURN_RADAR_FILES),
    ),
}


def get_project(project_id: str) -> Project | None:
    return _PROJECTS.get(project_id)


def list_projects() -> list[Project]:
    return list(_PROJECTS.values())
