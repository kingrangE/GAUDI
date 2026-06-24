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
}


def get_project(project_id: str) -> Project | None:
    return _PROJECTS.get(project_id)


def list_projects() -> list[Project]:
    return list(_PROJECTS.values())
