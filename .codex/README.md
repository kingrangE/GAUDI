# .codex/

Support files for the teammate who develops with **Codex** (not Claude Code).

Codex auto-loads `AGENTS.md` (repo root + nested), so all repo rules already apply. This folder adds the
two team workflows as invokable Codex **slash-commands**.

## prompts/
`test-writing.md` and `ship-feature.md` are **symlinks** to the canonical skill files in
`.claude/skills/<name>/SKILL.md` — single source of truth, no duplication. Editing a `SKILL.md` updates
both the Claude Code skill and this Codex prompt.

## One-time setup
Codex reads custom prompts from `~/.codex/prompts/` (your home dir), not from the repo. Run once:

```bash
bash .codex/setup-prompts.sh
```

This links the repo's prompt files into `~/.codex/prompts/`, so `/test-writing` and `/ship-feature`
become available in Codex. Re-run after pulling if new prompts are added.

> Note: the linked files keep the skill's YAML frontmatter (`name`/`description`) at the top — harmless,
> just metadata describing the workflow.
