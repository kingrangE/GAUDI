"""Generate N samples for one instruction, concurrently, at extreme temperature.

The model is told to fill any unspecified decision itself — that's the point: at high
temperature it fills gaps differently each run, so an under-specified instruction yields
divergent samples and a precise one yields convergent samples.
"""

from __future__ import annotations

import asyncio

from feature_spec_design.models import Sample, SpecTask
from llm.client import LLMClient

SYSTEM_PROMPT = (
    "당신은 시니어 백엔드 개발자입니다. 사용자의 지시에 따라 기능을 설계·구현하세요. "
    "지시에 명시되지 않은 기술 결정은 스스로 합리적으로 선택하되, 추측한 부분을 사용자에게 "
    "되묻지 말고 바로 결정하세요. 결과의 맨 앞에 선택한 핵심 기술 결정"
    "(언어/프레임워크, 데이터베이스, 인증/저장 방식 등)을 '결정:' 목록으로 짧게 명시한 뒤, "
    "간결한 구현 스케치를 제시하세요."
)


def build_user_prompt(task: SpecTask, instruction: str) -> str:
    """Compose the message the generator sees: the brief plus the candidate's instruction."""

    return f"# 과제\n{task.brief}\n\n# 사용자 지시\n{instruction}"


async def generate_samples(
    client: LLMClient,
    task: SpecTask,
    instruction: str,
    *,
    n: int,
    temperature: float,
) -> list[Sample]:
    """Run `n` generations concurrently and return them as ordered samples.

    Order of the returned list is stable (index 0..n-1); which underlying call produced
    which slot is irrelevant — downstream analysis treats the samples as a set.
    """

    if n <= 0:
        raise ValueError("n must be positive")

    system = SYSTEM_PROMPT
    user = build_user_prompt(task, instruction)

    async def one() -> str:
        return await asyncio.to_thread(client.complete, system, user, temperature=temperature)

    contents = await asyncio.gather(*(one() for _ in range(n)))
    return [Sample(index=i, content=c) for i, c in enumerate(contents)]
