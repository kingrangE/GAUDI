# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> ⚠️ **FROZEN ROOT DOC — DO NOT EDIT.**
> This file is the canonical, frozen governance for the repo. Do **not** modify it during feature work.
> `CLAUDE.md` and `AGENTS.md` (repo root) **must stay byte-for-byte identical** — if you ever change one,
> change the other in the same commit. Verify with `diff CLAUDE.md AGENTS.md` (must print nothing).
> Need rules scoped to a part of the codebase? Put them in `frontend/CLAUDE.md` + `frontend/AGENTS.md`
> or `backend/CLAUDE.md` + `backend/AGENTS.md` (those are auto-loaded and editable). Never put scoped
> rules here.

## Project

`and-you` — entry for the 14th AI SW Hackathon (제 14회 AI SW 해커톤 출품작). An **AI Agent
development-competency evaluation platform**: it evaluates how well a person directs/verifies AI agents
(prompt engineering, design specs, context engineering, rejection of wrong AI output) alongside
traditional coding/CS depth, with LLM-as-a-judge scoring.

Built by a 3-person team — **hyeoksin (혁신)**, **gilwon (길원)**, **minsu (민수)** — who all develop
with coding agents (2 on Claude Code, 1 on Codex) and divide work **by feature, not by fixed role**.

## Stack

- **Frontend**: Next.js (React, TypeScript) — `frontend/`
- **Backend**: FastAPI (Python) — `backend/`. All LLM / LLM-as-judge calls live here.
- **Database**: PostgreSQL
- Single **monorepo**. LLM provider/model config is centralized in the backend.

## Branch workflow

Everything is built on short-lived feature branches; `main` is always stable and demo-able.

- **Always branch from an up-to-date `main`**: `git switch main && git pull` before creating a branch.
- **One feature per branch.** Don't mix unrelated changes.
- **Branch name**: `type/owner/short-desc` (kebab-case).
  - `type` ∈ `feat | fix | chore | docs | refactor | test`
  - `owner` ∈ `hyeoksin | gilwon | minsu`
  - examples: `feat/gilwon/rejection-eval`, `fix/minsu/login-token`, `chore/hyeoksin/ci`
- **Never push directly to `main`** — it is branch-protected. All changes land via PR.

## Commit convention

[Conventional Commits](https://www.conventionalcommits.org/). **Subject line in English**; body may be Korean.

```
feat(rejection-eval): add precision/recall scoring for injected design flaws

설계 결함을 0~N개 무작위 주입하고 3회 반복하여 탐지율을 계산. LLM 호출은 …
```

- Types match the branch types: `feat, fix, chore, docs, refactor, test`.
- Scope = the feature/module (e.g. `rejection-eval`, `auth`, `admin`).
- **No AI co-author trailers.** Never add `Co-Authored-By: Claude` (or any AI tool) to commits — attribute
  to the human author only. If your agent appends one by default, strip it before committing.

## PR & merge rules

**Open a PR only when the feature is fully implemented, tested, and stable** — not for work-in-progress.

A PR may merge into `main` only when **both** gates pass:
1. **1 human approval** from another teammate (the author may **not** approve their own PR).
2. **Green CI** (lint + type-check + tests for both backend and frontend).

- Fill the PR description using the template (`.github/pull_request_template.md`); description in Korean is fine.
- **Squash-merge**, then **delete the branch**.
- Keep `main` linear and always releasable.

### Definition of Done (must all be true before opening a PR)
- [ ] Feature is fully implemented (no TODO stubs for the feature's core path).
- [ ] Tests written for the feature's core behavior and **passing locally**.
- [ ] Lint + type-check clean.
- [ ] PR description filled; ready for review.

## Testing rule

**No feature is "done" without tests, and no PR is opened without them.** See the **`test-writing`** skill
for conventions and the LLM-mocking pattern.

- Bar = **behavior coverage, not a percentage**: test the happy path + key edge/failure cases of the
  feature's core logic.
- **Mock the LLM in unit tests** (deterministic, fast, free); add a *small* number of real integration
  tests for end-to-end LLM behavior.
- Backend tests: `pytest` in `backend/tests/` (`test_*.py`). Frontend tests: Vitest (`*.test.ts(x)`),
  Playwright for any E2E.

## Commands

```bash
# Backend (run from backend/)
pip install -e ".[dev]"     # or: uv sync
ruff check .                # lint
pytest                      # tests
pytest path/to/test_x.py::test_name   # single test

# Frontend (run from frontend/)
npm install
npm run lint                # eslint
npm run typecheck           # tsc --noEmit
npm test                    # vitest run
npm test -- src/foo.test.ts # single test file
```

## Secrets & config

- **Never commit secrets.** API keys / DB URLs live in `.env` (git-ignored). Commit `.env.example` with keys but no values.
- Centralize LLM provider/model selection in the backend (one config module) — don't scatter model IDs across files.

## Skills

The detailed workflows live as plain-markdown skill files under `.claude/skills/`. The repo-wide *rules*
themselves are already in this doc, so all three teammates follow them regardless of tool; the skill
files just add step-by-step detail and (on Claude Code) one-command invocation.

- **`test-writing`** (`.claude/skills/test-writing/SKILL.md`) — how to write tests for a feature (frameworks, behavior bar, LLM mocking). Use at the end of every feature, before opening a PR.
- **`ship-feature`** (`.claude/skills/ship-feature/SKILL.md`) — the end-to-end loop: branch → implement → write tests → run lint+tests → commit → open PR. Use when starting/finishing a feature.

**Claude Code**: these are auto-discovered and invokable as skills.

**Codex** (`.claude/skills/` is not scanned by Codex): the same workflows are committed as Codex
slash-commands under `.codex/prompts/` (symlinks to the same `SKILL.md` files — single source of truth).
Run `bash .codex/setup-prompts.sh` once to link them into `~/.codex/prompts/`, then use `/test-writing`
and `/ship-feature` in Codex. See `.codex/README.md`.

## One-time setup: branch protection

After the repo has a GitHub remote, enable the merge gate (replace `{owner}`):

```bash
gh api -X PUT repos/{owner}/and-you/branches/main/protection \
  -f required_status_checks.strict=true \
  -f 'required_status_checks.contexts[]=backend' \
  -f 'required_status_checks.contexts[]=frontend' \
  -F enforce_admins=true \
  -F required_pull_request_reviews.required_approving_review_count=1 \
  -F restrictions=null
```
