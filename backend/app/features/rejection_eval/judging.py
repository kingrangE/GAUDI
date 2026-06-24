"""LLM judging: ground each design item against the requirements spec.

The judge receives the topic's **functional requirements** (which the generator
never saw) and decides, per item, whether the decision is called for by those
requirements. Items that are not (`in_requirements=false`) are out-of-scope
flaws the candidate should have rejected. Also writes a 1-2 line report.
Unit tests mock this function.
"""

import json

from app.features.rejection_eval.schemas import (
    GeneratedItem,
    JudgeOutput,
    PairwiseVerdict,
)
from app.llm.structured import complete_structured

_SYSTEM = """\
당신은 거부 능력 평가의 채점관입니다. 어떤 기능의 **기능 요구사항 명세**와, AI가 응시자의
프롬프트만 보고 생성한 **설계 항목 목록**이 주어집니다. (생성 AI는 이 요구사항 명세를 보지
못했습니다.)

각 항목에 대해 **요구사항 명세에 근거한 결정인지**(in_requirements)를 판정하세요:
- 요구사항이 직접 요구하거나 그 구현에 필수적인 결정 → in_requirements=true
- 요구사항이 요구하지 않은 결정(범위를 벗어난 임의 추가·불필요한 기술/방향) → in_requirements=false

판정은 항목의 기술적 옳고그름이 아니라 **요구사항에 들어있는지**만 기준으로 합니다.
모든 항목에 대해 judgements를 채우고, report에는 응시자가 무엇을 잘 거부했고 무엇을 놓쳤는지
1~2줄 한국어로 요약하세요.
"""


async def judge_attempt(
    requirements: list[str],
    items: list[GeneratedItem],
    flagged_ids: list[str],
    reasons: dict[str, str],
    model: str | None = None,
) -> JudgeOutput:
    payload = {
        "requirements": requirements,
        "items": [i.model_dump() for i in items],
        "flagged_ids": flagged_ids,
        "reasons": reasons,
    }
    user = json.dumps(payload, ensure_ascii=False)
    return await complete_structured(_SYSTEM, user, JudgeOutput, model=model)


_PAIRWISE_SYSTEM = """\
당신은 거부 능력 평가의 비교 채점관입니다. 어떤 기능의 **기능 요구사항 명세**와, AI가 생성한
**설계 항목 목록**, 그리고 두 응시자 A·B가 각각 "잘못됐다고 거부한 항목 id 목록"이 주어집니다.

요구사항에 비추어, **요구사항에 없는(범위 밖) 항목과 잘못된 설계를 더 정확히 골라 거부한** 응시자를
판정하세요. 더 많이 맞히고 오탐(정상 항목을 거부)이 적은 쪽이 낫습니다. 두 제출의 품질이 사실상
같으면 tie로 판정합니다. winner는 "A", "B", "tie" 중 하나, reason은 1줄 한국어 근거입니다.
"""


async def judge_pairwise(
    requirements: list[str],
    items: list[GeneratedItem],
    flaws_a: list[str],
    flaws_b: list[str],
    model: str | None = None,
) -> PairwiseVerdict:
    payload = {
        "requirements": requirements,
        "items": [i.model_dump() for i in items],
        "submission_a": flaws_a,
        "submission_b": flaws_b,
    }
    user = json.dumps(payload, ensure_ascii=False)
    return await complete_structured(_PAIRWISE_SYSTEM, user, PairwiseVerdict, model=model)
