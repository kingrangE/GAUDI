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
