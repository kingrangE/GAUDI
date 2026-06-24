# .githooks/

Tracked git hooks for the team. Git ignores `.git/hooks/` (not version-controlled) and does not
auto-install hooks on clone, so each teammate enables these **once per clone**:

```bash
bash scripts/setup-hooks.sh
```

This sets `core.hooksPath=.githooks`.

## Hooks
- **`commit-msg`** — enforces the "no AI co-author" rule from `CLAUDE.md` / `AGENTS.md`: strips any
  `Co-authored-by:` line referencing an AI assistant (Claude, Codex, Copilot, Anthropic, OpenAI, …).
  Real human co-authors are kept. Runs on every `git commit`, so even if your agent appends the trailer
  by default, it never reaches the commit.
