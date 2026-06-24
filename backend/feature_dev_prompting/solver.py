"""Turn a candidate prompt (problem + current code + instruction) into updated code."""

from __future__ import annotations

import re

from feature_dev_prompting.models import Problem
from llm.client import LLMClient

SYSTEM_PROMPT = (
    "You are a coding assistant operating under a STRICT rule: the user's instruction is the "
    "authoritative specification for how to solve the problem. Implement exactly and only what "
    "the user's instruction describes.\n"
    "Do NOT use your own knowledge to fix, complete, or improve a vague, incomplete, or "
    "incorrect instruction — follow it faithfully even if doing so yields a wrong or incomplete "
    "solution. If the instruction does not specify an approach, do not invent a correct one on "
    "your own.\n"
    "The problem statement and current code are context only; the user's instruction governs "
    "what you write. Apply the instruction to the current code and return the FULL updated "
    "Python function — code only, no explanation, no markdown prose."
)

_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)


def extract_code(text: str) -> str:
    """Pull code out of a ```fenced``` block if present, else return the text as-is."""

    match = _FENCE.search(text)
    return (match.group(1) if match else text).strip()


def build_user_prompt(problem: Problem, user_prompt: str, current_code: str,
                      feedback: str | None = None) -> str:
    """Compose the user message: problem body + current code + the candidate's instruction."""

    parts = [
        f"# 문제\n{problem.statement}",
        f"# 현재 코드\n{current_code}",
        f"# 사용자 지시\n{user_prompt}",
    ]
    if feedback:
        parts.append(f"# 이전 시도 결과(피드백)\n{feedback}")
    return "\n\n".join(parts)


def generate_code(client: LLMClient, problem: Problem, user_prompt: str, current_code: str,
                  feedback: str | None = None) -> str:
    """Ask the LLM to update the current code and return the extracted code."""

    raw = client.complete(
        SYSTEM_PROMPT, build_user_prompt(problem, user_prompt, current_code, feedback)
    )
    return extract_code(raw)
