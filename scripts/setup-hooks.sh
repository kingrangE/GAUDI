#!/usr/bin/env bash
# One-time per clone: point git at the repo's tracked hooks (.githooks/).
# Git does not auto-install hooks on clone (security), so every teammate runs this once.
#
# Usage:  bash scripts/setup-hooks.sh
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
git -C "$repo_root" config core.hooksPath .githooks
chmod +x "$repo_root"/.githooks/* 2>/dev/null || true

echo "Git hooks installed (core.hooksPath=.githooks)."
echo "commit-msg hook will strip AI co-author trailers automatically."
