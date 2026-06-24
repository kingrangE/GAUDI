"""LLM-as-judge for CS 서술형 answers + the two-report synthesis.

Each answer is classified into one of four response types and scored on the
README rubric. The honesty signature — 솔직한 "모름"(−2) vs 허세-오답(−5) — is the
crux of this feature, so the system prompt makes that distinction explicit. The
discrete score is reconciled with the type in code (`scoring.score_for_type`) so
the LLM can't drift off the rubric. A single session-level call then writes the
요약·분석 reports. Unit tests mock `complete_structured`; `grading.py` depends only
on these names (and can be monkeypatched at the seam).
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field

from app.features.cs_eval import scoring
from app.llm.structured import complete_structured


class AnswerJudgement(BaseModel):
    response_type: Literal["correct", "partial", "honest_unknown", "bluff_wrong"]
    score: int = Field(ge=-5, le=5)
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    rationale: str


class SessionReports(BaseModel):
    summary_report: str  # 부족 키워드 위주 (즉시 평가용)
    analysis_report: str  # 4~5문장 진단 (면접 심화용)


_SYSTEM = """\
당신은 CS 서술형 답안 채점관입니다. 문항, 채점 루브릭(핵심 키워드·흔한 실수), 모범답안,
응시자 답안이 주어집니다. 정답 여부를 넘어 '이해의 깊이'와 '정직함'을 평가하세요.

응답을 다음 네 유형 중 하나로 분류하고 그에 맞는 점수를 매기세요:
- correct(+5): 핵심 개념을 정확히 설명함.
- partial(+1~+4): 아는 만큼만 부분적으로 맞게 설명함(맞은 정도에 비례).
- honest_unknown(-2): 모른다고 솔직히 인정함.
- bluff_wrong(-5): 모르면서 아는 척 장황하게 딴소리하거나 핵심과 어긋나게 틀림.

**가장 중요**: honest_unknown(솔직한 "모름")과 bluff_wrong(허세-오답)을 반드시 구분하세요.
모른다고 정직하게 인정한 답은, 아는 척하며 틀린 답보다 더 높게 평가합니다.

한국어로 다음을 산출하세요:
- response_type: 위 네 유형 중 하나.
- score: 유형에 맞는 점수(correct=5, honest_unknown=-2, bluff_wrong=-5, partial=1~4).
- matched_keywords: 응시자가 짚은 핵심 키워드.
- missing_keywords: 빠뜨린 핵심 키워드.
- rationale: 한 문장 근거.
"""

_SYNTH_SYSTEM = """\
당신은 CS 서술형 평가의 종합 리포트 작성자입니다. 문항별 채점 결과(도메인·유형·점수·
짚은/빠뜨린 키워드·근거)가 주어집니다. 두 리포트를 한국어로 작성하세요:
- summary_report: 부족한 키워드 위주의 간결한 요약(즉시 평가용).
- analysis_report: 응시자의 이해 수준을 4~5문장으로 진단(면접 심화 질문에 쓸 수 있게).
"""


async def judge_answer(
    *,
    domain: str,
    prompt_md: str,
    reference_answer: str,
    rubric: dict | None,
    answer_text: str,
) -> AnswerJudgement:
    """Classify and score one answer; reconcile the score with the type."""
    payload = {
        "question": {
            "domain": domain,
            "prompt": prompt_md,
            "rubric": rubric or {},
            "reference_answer": reference_answer,
        },
        "candidate_answer": answer_text,
    }
    user = json.dumps(payload, ensure_ascii=False)
    judgement = await complete_structured(_SYSTEM, user, AnswerJudgement)
    # The point scale is owned by the rubric, not the LLM — keep them consistent.
    reconciled = scoring.score_for_type(judgement.response_type, judgement.score)
    return judgement.model_copy(update={"score": reconciled})


async def synthesize_reports(*, per_question: list[dict]) -> SessionReports:
    """One session-level call producing the 요약·분석 reports."""
    user = json.dumps({"per_question": per_question}, ensure_ascii=False)
    return await complete_structured(_SYNTH_SYSTEM, user, SessionReports)
