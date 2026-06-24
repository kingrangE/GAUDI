# frontend/CLAUDE.md

Scoped guidance for the **Next.js frontend**. The root `CLAUDE.md` (frozen) holds all repo-wide rules —
branch workflow, PR/merge gate, commit convention, testing rule. This file is **editable**; add
frontend-specific conventions here as the code grows.

> Keep this file identical to `frontend/AGENTS.md` (the Codex teammate reads that one).

## Stack
Next.js (React, TypeScript). Talks to the FastAPI backend; no direct LLM calls from the client.

## Commands
```bash
npm install
npm run lint        # eslint
npm run typecheck   # tsc --noEmit
npm test            # vitest run
npm test -- src/foo.test.ts   # single test file
```

## Conventions (fill in as the frontend grows)
- Tests colocated as `*.test.ts(x)` (Vitest); Playwright for E2E.
- Keep API base URL / secrets in env (`NEXT_PUBLIC_*` only for non-sensitive values). See the `test-writing` skill for testing.
