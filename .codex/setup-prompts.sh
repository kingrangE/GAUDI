#!/usr/bin/env bash
# One-time setup for the Codex-using teammate.
# Links this repo's committed prompt files into your Codex prompts dir (~/.codex/prompts),
# so `test-writing` and `ship-feature` are available as /slash-commands in Codex.
#
# The committed files in .codex/prompts/ are symlinks to the canonical
# .claude/skills/<name>/SKILL.md, so there is a single source of truth — editing a SKILL.md
# updates the Claude skill AND your Codex prompt at once.
#
# Usage:  bash .codex/setup-prompts.sh
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dest="${CODEX_HOME:-$HOME/.codex}/prompts"
mkdir -p "$dest"

for f in "$repo_root"/.codex/prompts/*.md; do
  name="$(basename "$f")"
  ln -sfn "$f" "$dest/$name"
  echo "linked $dest/$name -> $f"
done

echo "Done. In Codex, /test-writing and /ship-feature are now available."
