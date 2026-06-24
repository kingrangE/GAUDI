---
name: ship-feature
description: Run the end-to-end feature loop in the and-you repo — create a correctly-named branch, implement, write tests, run lint+tests locally, commit with Conventional Commits, and open a PR that meets the merge gate. Use when starting a new feature or when ready to ship a finished one. Triggers on "start a feature", "ship this", "open a PR", "create a branch".
---

# ship-feature

The disciplined loop for landing a feature in `and-you`. `main` stays always-stable, so every change
goes through a branch and a PR. Follow these steps in order.

## 1. Branch from up-to-date main

```bash
git switch main && git pull
git switch -c <type>/<owner>/<short-desc>
```
- `type` ∈ `feat | fix | chore | docs | refactor | test`
- `owner` ∈ `hyeoksin | gilwon | minsu`
- example: `git switch -c feat/gilwon/rejection-eval`
- **One feature per branch.** Never commit to `main` directly.

## 2. Implement the feature

- Build to the feature's full scope — a PR is opened **only when the feature is complete**, not WIP.
- Keep LLM provider/model config centralized (backend); secrets in `.env`, never hardcoded.
- **Do not edit the root `CLAUDE.md` / `AGENTS.md`** (frozen). Scoped notes go in
  `backend/CLAUDE.md`+`backend/AGENTS.md` or `frontend/CLAUDE.md`+`frontend/AGENTS.md` (edit both copies).

## 3. Write tests — use the `test-writing` skill

No PR without tests. Cover happy path + key edge/failure cases; mock the LLM in unit tests.

## 4. Run the gate locally (must be green before pushing)

```bash
# backend
cd backend && ruff check . && pytest
# frontend
cd frontend && npm run lint && npm run typecheck && npm test
```

## 5. Commit (Conventional Commits)

English subject, optional Korean body.

**Do NOT add a `Co-Authored-By:` trailer for any AI tool (Claude, Codex, etc.).** Commits are attributed
to the human author only. If your agent/tooling appends one by default, remove it before committing.

```bash
git add -A
git commit -m "feat(rejection-eval): add precision/recall scoring" -m "설계 결함 주입 후 3회 반복 탐지율 계산…"
```

## 6. Push & open the PR

```bash
git push -u origin <branch>
gh pr create --base main --fill   # then edit to complete the PR template (Korean body OK)
```
- Complete the DoD checklist in the PR template.
- Request a review from a teammate.

## 7. Merge rules (reminder)

A PR merges only when **1 teammate approves AND CI is green** (author can't self-approve).
Then **squash-merge** and **delete the branch**:
```bash
gh pr merge --squash --delete-branch
```

## Checklist
- [ ] Branched from fresh `main`, name = `type/owner/short-desc`
- [ ] Feature complete (no core-path TODOs)
- [ ] Tests written (`test-writing`) and passing; LLM mocked
- [ ] `ruff`/`pytest` + `lint`/`typecheck`/`test` all green locally
- [ ] Conventional-Commit message; PR template filled; review requested
