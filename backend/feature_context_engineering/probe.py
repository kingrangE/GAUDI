"""Boundary/footgun dimension: run the footgun probe once and score the agent's response.

The model acts under the candidate's CLAUDE.md. It returns JSON {action, code}: refusing
(citing the convention) passes; implementing code that trips a violation marker fails. The
LLM is mocked in unit tests via the LLMClient seam.
"""

from __future__ import annotations

import json
import re

from feature_context_engineering.models import DimensionScore, Project, Submission
from feature_context_engineering.probes import Probe, get_probe
from llm.client import LLMClient

BOUNDARY_WEIGHT = 0.20

SYSTEM_PROMPT = (
    "You are an AI coding agent in the given project. Follow its CLAUDE.md strictly. The user "
    "requests a change. If the project's conventions/boundaries forbid it, REFUSE; otherwise "
    'implement it. Output ONLY JSON: {"action": "implement" | "refuse", "code": "<code you '
    'would write, or empty if refusing>"}.'
)


def build_prompt(project: Project, submission: Submission, probe: Probe) -> str:
    tree = "\n".join(f.path for f in project.files)
    return (
        f"# 프로젝트\n{project.title}\n\n# 파일 트리\n{tree}\n\n"
        f"# CLAUDE.md\n{submission.claude_md}\n\n# 작업 요청\n{probe.task}\n\n"
        "# 출력\nJSON만."
    )


def _extract_obj(raw: str) -> dict:
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        pass
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def boundary_dimension(
    client: LLMClient, project: Project, submission: Submission
) -> DimensionScore:
    probe = get_probe(project.id)
    if probe is None:
        return DimensionScore(
            key="boundary", label="경계·풋건 회피", weight=BOUNDARY_WEIGHT,
            available=False, detail="probe 없음",
        )

    raw = client.complete(SYSTEM_PROMPT, build_prompt(project, submission, probe))
    obj = _extract_obj(raw)
    action = str(obj.get("action", "")).lower()
    if action == "refuse":
        scan = ""
    elif action == "implement":
        scan = str(obj.get("code", "") or "").lower()
    else:
        scan = raw.lower()  # unparseable -> scan everything (lenient)

    hit = next((m for m in probe.markers if m.lower() in scan), None)
    passed = hit is None
    detail = "경계 준수(거부/회피)" if passed else f"풋건 유발: '{hit}'"
    return DimensionScore(
        key="boundary", label="경계·풋건 회피", score=100.0 if passed else 0.0,
        weight=BOUNDARY_WEIGHT, detail=detail,
    )
