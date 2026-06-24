"""LLM judging: reconcile candidate flags and write a short report.

Per-item correctness is scored deterministically elsewhere. The judge only
decides whether any candidate-flagged item that was *not* an injected flaw is
nonetheless a genuine real flaw (-> bonus), and writes a 1-2 line report.
Unit tests mock this function.
"""

import json

from app.features.rejection_eval.schemas import GeneratedItem, JudgeOutput
from app.llm.structured import complete_structured

_SYSTEM = """\
당신은 거부 능력 평가의 채점관입니다. 설계 항목 목록(각 항목의 정답 is_flawed 포함)과
응시자가 '잘못됐다'고 표시한 항목 id 목록이 주어집니다.

할 일:
1. 응시자가 표시했지만 is_flawed=false인 항목 중, 실제로는 진짜 결함이라고 판단되는 항목의
   id를 bonus_item_ids에 담으세요(없으면 빈 배열).
2. report: 응시자의 거부 능력을 1~2줄 한국어로 요약하세요(무엇을 잘 찾고 무엇을 놓쳤는지).
"""


async def judge_attempt(
    topic_title: str,
    items: list[GeneratedItem],
    flagged_ids: list[str],
    reasons: dict[str, str],
) -> JudgeOutput:
    payload = {
        "topic": topic_title,
        "items": [i.model_dump() for i in items],
        "flagged_ids": flagged_ids,
        "reasons": reasons,
    }
    user = json.dumps(payload, ensure_ascii=False)
    return await complete_structured(_SYSTEM, user, JudgeOutput)
