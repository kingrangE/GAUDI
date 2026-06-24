"""Deterministic scoring axes (no LLM): grounding/accuracy and conciseness/anti-bloat.

Grounding (agents-lint style): of the file paths and commands the candidate's CLAUDE.md
references, how many actually exist in the project? Hallucinated references are penalized;
prose that merely contains a slash (e.g. "request/response") is ignored, not counted.
Conciseness: over-long/bloated docs measurably hurt agents, so length is capped.
"""

from __future__ import annotations

import json
import re

from feature_context_engineering.models import DimensionScore, Project, Submission

GROUNDING_WEIGHT = 0.25
EFFICIENCY_WEIGHT = 0.15

# CLAUDE.md is loaded into context on EVERY new conversation, so its token footprint is a
# recurring input cost. Reward a small footprint; penalize bloat.
_EFF_FULL_TOKENS = 600  # at/under this -> full score
_EFF_FLOOR_TOKENS = 2500  # at/over this -> floor score
_EFF_FLOOR = 30.0

_BACKTICK = re.compile(r"`([^`]+)`")
_TOKEN_SPLIT = re.compile(r"[\s,()\[\]<>\"'*]+")
_CLEAN = re.compile(r"[\w./\-]+")
# A real-looking file path: optional leading dot, name, optional dirs, then a .ext (1-5).
_FILEPATH = re.compile(r"\.?[\w-]+(?:/[\w.-]+)*\.[A-Za-z]{1,5}")
_EXT_ONLY = re.compile(r"\.[A-Za-z]{1,5}")


def _tokens(text: str) -> set[str]:
    raw = {m.strip() for m in _BACKTICK.findall(text)}
    raw.update(t.strip() for t in _TOKEN_SPLIT.split(text))
    out: set[str] = set()
    for tok in raw:
        tok = tok.strip().strip("`").rstrip(".:;,")
        if tok and "://" not in tok and not tok.startswith(("http", "@")) and _CLEAN.fullmatch(tok):
            out.add(tok)
    return out


def _valid_commands(project: Project) -> set[str]:
    contents = {f.path: (f.content or "") for f in project.files if f.kind == "file"}
    valid: set[str] = set()
    for path, body in contents.items():
        if path == "Makefile" or path.endswith("/Makefile"):
            valid.update(f"make {t}" for t in re.findall(r"(?m)^([A-Za-z][\w-]*):", body))
        if path == "package.json" or path.endswith("/package.json"):
            try:
                scripts = json.loads(body).get("scripts", {})
            except json.JSONDecodeError:
                scripts = {}
            valid.update(f"npm run {k}" for k in scripts)
            valid.update({"npm install", "npm test"})
        if path.endswith("pyproject.toml"):
            valid.update({"pytest", "ruff check", "ruff check ."})
    return valid


def _candidate_commands(text: str) -> set[str]:
    cmds: set[str] = set()
    for m in _BACKTICK.findall(text):
        m = m.strip()
        if re.match(r"(make |npm run |npm install|npm test|pytest|ruff)", m):
            cmds.add(m)
    return cmds


def grounding_dimension(project: Project, submission: Submission) -> DimensionScore:
    """Fraction of referenced paths/commands that are real in the project (0 if no refs)."""

    full = {f.path for f in project.files}
    basenames = {f.path.split("/")[-1] for f in project.files}

    real_paths: set[str] = set()
    halluc_paths: set[str] = set()
    for tok in _tokens(submission.claude_md):
        norm = tok.rstrip("/")
        if not any(c.isalpha() for c in norm):
            continue
        if norm in full or norm.split("/")[-1] in basenames:
            real_paths.add(norm)
        elif _FILEPATH.fullmatch(norm) and not _EXT_ONLY.fullmatch(norm):
            halluc_paths.add(norm)  # looks like a file path but doesn't exist
        # else: prose with a slash / bare words -> not a path reference, ignored

    valid_cmds = _valid_commands(project)
    cmds = _candidate_commands(submission.claude_md)
    real_cmds = {c for c in cmds if any(c.startswith(v) or v.startswith(c) for v in valid_cmds)}
    halluc_cmds = cmds - real_cmds

    total = len(real_paths) + len(halluc_paths) + len(cmds)
    correct = len(real_paths) + len(real_cmds)
    score = round(correct / total * 100, 1) if total else 0.0
    halluc = halluc_paths | halluc_cmds
    detail = f"refs {correct}/{total} 실재"
    if halluc:
        detail += f"; 환각: {', '.join(sorted(halluc))}"
    if total == 0:
        detail = "참조한 파일/명령 없음 (grounding 0)"
    return DimensionScore(
        key="grounding", label="정확성(grounding)", score=score,
        weight=GROUNDING_WEIGHT, detail=detail,
    )


def estimate_tokens(text: str) -> int:
    """Token count of the doc. Uses tiktoken when available; else a char-based heuristic."""

    try:
        import tiktoken

        return len(tiktoken.get_encoding("o200k_base").encode(text))
    except Exception:
        # Fallback: ~4 chars/token, but CJK is denser (~1.5), so weight non-ASCII higher.
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        cjk_chars = len(text) - ascii_chars
        return max(1, round(ascii_chars / 4 + cjk_chars / 1.6))


def efficiency_dimension(submission: Submission) -> DimensionScore:
    """Token efficiency: the doc is loaded every conversation, so its token cost recurs."""

    tokens = estimate_tokens(submission.claude_md)
    if tokens <= _EFF_FULL_TOKENS:
        score = 100.0
    elif tokens >= _EFF_FLOOR_TOKENS:
        score = _EFF_FLOOR
    else:
        span = _EFF_FLOOR_TOKENS - _EFF_FULL_TOKENS
        score = round(100 - (tokens - _EFF_FULL_TOKENS) * ((100 - _EFF_FLOOR) / span), 1)
    return DimensionScore(
        key="efficiency", label="효율성(토큰 비용)", score=score,
        weight=EFFICIENCY_WEIGHT, detail=f"~{tokens} 토큰 · 매 대화 로드",
    )
