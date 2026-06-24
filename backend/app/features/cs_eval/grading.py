"""CS-eval grading orchestration.

Judges each answer (response-type + score) through the `judge` seam, maps to the
deterministic point scale, then synthesizes the two session reports. This is the
inline (synchronous) path used in PR-A; PR-B also runs it from an RQ worker.

`judge_answer` / `synthesize_reports` are imported by name so tests can
monkeypatch `grading.judge_answer` with a canned stub (the coding-test pattern).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.cs_eval import scoring
from app.features.cs_eval.judge import judge_answer, synthesize_reports
from app.features.cs_eval.models import CsAnswer, CsQuestion, CsSession


async def grade_session(db: AsyncSession, session_id: str) -> None:
    """Grade every answer, aggregate the score, and write the two reports.

    On any failure the session is marked ``failed`` with an error message so the
    polling client sees a terminal state.
    """
    session = await db.get(CsSession, session_id)
    if session is None:
        return

    try:
        rows = await db.execute(
            select(CsAnswer)
            .where(CsAnswer.session_id == session_id)
            .order_by(CsAnswer.ordinal)
        )
        answers = list(rows.scalars())

        per_question: list[dict] = []
        total = 0
        for ans in answers:
            question = await db.get(CsQuestion, ans.question_id)
            judgement = await judge_answer(
                domain=question.domain if question else "",
                prompt_md=question.prompt_md if question else "",
                reference_answer=question.reference_answer if question else "",
                rubric=question.rubric if question else None,
                answer_text=ans.answer_text,
            )
            ans.response_type = judgement.response_type
            ans.score = judgement.score
            ans.matched_keywords = judgement.matched_keywords
            ans.missing_keywords = judgement.missing_keywords
            ans.rationale = judgement.rationale
            total += judgement.score
            per_question.append(
                {
                    "domain": question.domain if question else "",
                    "response_type": judgement.response_type,
                    "score": judgement.score,
                    "matched_keywords": judgement.matched_keywords,
                    "missing_keywords": judgement.missing_keywords,
                    "rationale": judgement.rationale,
                }
            )

        session.total_score = total
        session.normalized_score = scoring.normalize(total, len(answers))
        reports = await synthesize_reports(per_question=per_question)
        session.summary_report = reports.summary_report
        session.analysis_report = reports.analysis_report
        session.status = "graded"
    except Exception as exc:  # noqa: BLE001 — surface failure to the candidate
        session.status = "failed"
        session.error = f"{type(exc).__name__}: {exc}"[:300]

    await db.commit()
