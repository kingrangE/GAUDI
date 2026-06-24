# backend/CLAUDE.md

Scoped guidance for the **FastAPI backend**. The root `CLAUDE.md` (frozen) holds all repo-wide rules —
branch workflow, PR/merge gate, commit convention, testing rule. This file is **editable**; add
backend-specific conventions here as the code grows.

> Keep this file identical to `backend/AGENTS.md` (the Codex teammate reads that one).

## Stack
FastAPI (Python 3.12) + PostgreSQL. All LLM / LLM-as-judge calls live here.

## Commands
```bash
pip install -e ".[dev]"     # or: uv sync
ruff check .
pytest
pytest tests/test_x.py::test_name   # single test
```

## Conventions (fill in as the backend grows)
- Centralize LLM provider/model config in one module; never scatter model IDs.
- Secrets via `.env` only (see `.env.example`); never commit keys.
- Tests in `tests/` as `test_*.py`; **mock the LLM** in unit tests. See the `test-writing` skill.

## Coding-test grading (async, RQ)

Submitting code grades asynchronously: the API returns immediately with
`status=grading` and the client polls `GET /api/coding-test/submissions/{id}`.

- `grading_mode` (env / `app/core/config.py`): `inline` (default — grades
  in-process; used by tests and no-broker setups) or `rq` (enqueues to a worker).
- Run the async path locally:
  ```bash
  docker compose up -d redis        # from repo root
  cd backend
  GRADING_MODE=rq uvicorn app.main:app --reload
  GRADING_MODE=rq python worker.py  # separate terminal: the RQ grading worker
  ```
- Seed problems once: `python -m app.scripts.seed_problems`.

## Sandbox security (coding-test runner)

`SubprocessCodeRunner` executes untrusted candidate Python in an isolated
`python -I` child with a wall-clock timeout, `resource` limits (address space /
CPU / file descriptors), network disabled, and a temp cwd. This is
**defense-in-depth, not airtight isolation** — suitable for a proctored /
trusted-candidate demo, **never** exposed to the open internet as-is. The
`CodeRunner` interface is the seam to drop in a hardened Docker/Piston runner.
