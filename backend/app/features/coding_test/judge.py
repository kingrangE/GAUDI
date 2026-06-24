"""LLM-as-judge: code-quality report for a graded submission.

The deterministic test score is computed elsewhere and only handed to the judge
as grounding — the judge never decides pass/fail. It produces 요약 키워드
(strengths/weaknesses), a 4~5문장 분석 리포트, and a code-quality score that is
*independent* of the test pass rate so tied scorers can be differentiated
(동점자 변별). Unit tests mock `complete_structured`.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from app.llm.structured import complete_structured


class JudgeOutput(BaseModel):
    """Structured judge result persisted onto the submission."""

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    analysis_report: str
    # 0-100, independent of the test pass rate (코드 품질 자체).
    code_quality_score: int = Field(ge=0, le=100)


_SYSTEM = """\
당신은 코딩 테스트 채점관입니다. 문제 설명, 채점 루브릭, 모범답안, 응시자의 Python 코드,
그리고 히든 테스트 케이스별 통과/실패 결과가 주어집니다.

테스트 통과 여부는 이미 결정적으로 계산되어 제공됩니다. 당신은 통과율을 다시 매기지 말고,
'코드 자체의 품질과 이해도'를 평가하세요. 부분 정답인 경우 어디서 어긋났는지(예: 경계조건,
부호 하나, 접근 자체의 오류)를 구분하세요.

다음을 한국어로 산출하세요:
- strengths: 잘한 점 키워드 목록(간결한 구/단어).
- weaknesses: 부족한 점 키워드 목록(다 맞았더라도 개선점이 있으면 포함).
- analysis_report: 응시자의 역량을 4~5문장으로 서술(면접 심화 질문에 쓸 수 있을 만큼 구체적으로).
- code_quality_score: 0~100의 코드 품질 점수. **테스트 통과율과 무관하게** 가독성·효율성·구조·
  엣지케이스 처리 관점에서 매기세요(동점자 변별용).
"""


async def judge_submission(
    *,
    title: str,
    description_md: str,
    rubric: dict | None,
    reference_solution: str,
    function_name: str,
    code: str,
    test_passed: int,
    test_total: int,
    case_breakdown: list[dict],
) -> JudgeOutput:
    """Build the grounded prompt and return the parsed structured judgement."""
    payload = {
        "problem": {
            "title": title,
            "description": description_md,
            "function_name": function_name,
            "rubric": rubric or {},
            "reference_solution": reference_solution,
        },
        "candidate_code": code,
        "test_score": {"passed": test_passed, "total": test_total},
        "case_breakdown": case_breakdown,
    }
    user = json.dumps(payload, ensure_ascii=False)
    return await complete_structured(_SYSTEM, user, JudgeOutput)
