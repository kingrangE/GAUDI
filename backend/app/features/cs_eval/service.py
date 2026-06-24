"""Orchestration for the CS deep-evaluation flow.

Endpoints stay thin; this module owns DB access. A submission creates one
session plus an answer row per question, then dispatches grading; the client
polls the session for the result.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.cs_eval import tasks
from app.features.cs_eval.models import CsAnswer, CsQuestion, CsSession
from app.features.cs_eval.schemas import (
    AnswerResult,
    CreateSessionRequest,
    QuestionPublic,
    SessionCreated,
    SessionResult,
)


async def list_questions(db: AsyncSession) -> list[QuestionPublic]:
    rows = await db.execute(select(CsQuestion).order_by(CsQuestion.ordinal))
    return [
        QuestionPublic(
            id=q.id, domain=q.domain, prompt_md=q.prompt_md, ordinal=q.ordinal
        )
        for q in rows.scalars()
    ]


async def create_session(
    db: AsyncSession, req: CreateSessionRequest
) -> SessionCreated:
    rows = await db.execute(select(CsQuestion))
    questions = {q.id: q for q in rows.scalars()}
    for answer in req.answers:
        if answer.question_id not in questions:
            raise HTTPException(
                status_code=404, detail=f"unknown question: {answer.question_id}"
            )

    session = CsSession(candidate_id=req.candidate_id)
    db.add(session)
    await db.flush()
    for answer in req.answers:
        db.add(
            CsAnswer(
                session_id=session.id,
                question_id=answer.question_id,
                answer_text=answer.answer_text,
                ordinal=questions[answer.question_id].ordinal,
            )
        )
    await db.commit()

    session_id = session.id
    # PR-A: inline grading completes before the response, but the client still
    # gets "grading" and polls — the same path it uses against RQ in PR-B.
    await tasks.enqueue_grading(db, session_id)
    return SessionCreated(session_id=session_id, status="grading")


async def get_session(db: AsyncSession, session_id: str) -> SessionResult:
    session = await db.get(CsSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    rows = await db.execute(
        select(CsAnswer)
        .where(CsAnswer.session_id == session_id)
        .order_by(CsAnswer.ordinal)
    )
    per_question: list[AnswerResult] = []
    for ans in rows.scalars():
        question = await db.get(CsQuestion, ans.question_id)
        per_question.append(
            AnswerResult(
                question_id=ans.question_id,
                domain=question.domain if question else "",
                response_type=ans.response_type,
                score=ans.score,
                matched_keywords=ans.matched_keywords,
                missing_keywords=ans.missing_keywords,
                rationale=ans.rationale,
            )
        )

    return SessionResult(
        id=session.id,
        candidate_id=session.candidate_id,
        status=session.status,
        total_score=session.total_score,
        normalized_score=session.normalized_score,
        summary_report=session.summary_report,
        analysis_report=session.analysis_report,
        per_question=per_question,
        error=session.error,
    )
