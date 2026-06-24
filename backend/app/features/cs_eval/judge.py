"""Judge seam for CS answers.

PR-A ships a deterministic keyword-overlap stub so the whole grading flow works
offline (no LLM). PR-B replaces these function *bodies* with `complete_structured`
calls — the names, signatures, and return types stay identical, so `grading.py`
and the tests (which monkeypatch `judge_answer` / `synthesize_reports`) are
unchanged. The honesty signature (솔직한 "모름" −2 vs 허세-오답 −5) lives in
`scoring.classify` here and moves into the LLM system prompt in PR-B.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.features.cs_eval import scoring


class AnswerJudgement(BaseModel):
    response_type: str  # correct | partial | honest_unknown | bluff_wrong
    score: int = Field(ge=-5, le=5)
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    rationale: str


class SessionReports(BaseModel):
    summary_report: str  # 부족 키워드 위주 (즉시 평가용)
    analysis_report: str  # 4~5문장 진단 (면접 심화용)


_RATIONALE = {
    "correct": "핵심 키워드를 모두 짚어 정확히 답했습니다.",
    "partial": "일부 핵심 개념은 짚었으나 빠진 부분이 있습니다.",
    "honest_unknown": "모르는 부분을 솔직히 인정했습니다(허세 없음).",
    "bluff_wrong": "내용을 적었으나 핵심 개념과 어긋난 답입니다.",
}


async def judge_answer(
    *,
    domain: str,
    prompt_md: str,
    reference_answer: str,
    rubric: dict | None,
    answer_text: str,
) -> AnswerJudgement:
    """Baseline judge: classify the answer against the rubric's key points."""
    key_points = list((rubric or {}).get("key_points", []))
    response_type, matched, missing, partial = scoring.classify(answer_text, key_points)
    return AnswerJudgement(
        response_type=response_type,
        score=scoring.score_for_type(response_type, partial),
        matched_keywords=matched,
        missing_keywords=missing,
        rationale=_RATIONALE.get(response_type, ""),
    )


async def synthesize_reports(*, per_question: list[dict]) -> SessionReports:
    """Baseline two-report synthesis (mechanical; PR-B uses one LLM call)."""
    missing = [kw for q in per_question for kw in (q.get("missing_keywords") or [])]
    deduped = list(dict.fromkeys(missing))
    if deduped:
        summary = "보완이 필요한 키워드: " + ", ".join(deduped)
    else:
        summary = "핵심 키워드를 모두 짚었습니다."

    lines = [
        f"[{q['domain']}] {q['response_type']} ({q['score']:+d}) — {q.get('rationale', '')}"
        for q in per_question
    ]
    analysis = " ".join(lines) or "제출된 답변이 없습니다."
    return SessionReports(summary_report=summary, analysis_report=analysis)
