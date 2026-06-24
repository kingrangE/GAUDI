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

## Feature layout
- **One directory per feature**: `frontend/feature_<name>/` (e.g. `feature_dev_prompting/`) holds that
  feature's components, API client, types, and colocated `*.test.tsx`. Build features in **isolation**;
  mount their routes under `app/` only during **assembly**. Don't scatter a feature across shared folders.
- Framework deps and **shared build config** (`package.json`, `tsconfig.json`, `eslint.config.js`,
  `vitest.config.ts`) live at the frontend root.
- Feature UI talks to the backend over HTTP only — never call an LLM from the client.

## Conventions (fill in as the frontend grows)
- Tests colocated as `*.test.ts(x)` (Vitest); Playwright for E2E.
- Keep API base URL / secrets in env (`NEXT_PUBLIC_*` only for non-sensitive values). See the `test-writing` skill for testing.

## Design
- All UI follows the **"judge console"** language: light cool-gray chrome + **one** dark `ink` code well
  + **one** `brand-600` accent, monospace kickers/verdicts. **Reuse the `@/components/ui` primitives and
  palette tokens (`brand`/`ink`/`good`/`bad`/`warn`) — never raw hex (`text-[#...]`).**
- Full guide (tokens, primitive catalog, Tailwind-vs-CSS-Module rule, build checklist): the
  **`frontend-design`** skill (`.claude/skills/frontend-design/SKILL.md`). Source of truth in code:
  `tailwind.config.ts` + `src/app/globals.css`.
