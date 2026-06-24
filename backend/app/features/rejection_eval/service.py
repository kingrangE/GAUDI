"""Orchestration for the rejection-ability evaluation flow.

One session = three fixed topics, run in order. Per topic: the candidate writes
a prompt -> the LLM generates a flawed design -> the candidate flags items.
After all three are submitted, scoring runs the judge and computes P/R/F1.
"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.rejection_eval.generation import generate_design
from app.features.rejection_eval.judging import judge_attempt
from app.features.rejection_eval.models import RejectionAttempt, RejectionSession
from app.features.rejection_eval.schemas import (
    CreateSessionResponse,
    GeneratedItem,
    GenerateResponse,
    PublicItem,
    ResultItem,
    ResultResponse,
    ResultTopic,
    SubmitRequest,
    SubmitResponse,
    TopicMeta,
)
from app.features.rejection_eval.scoring import aggregate, score_items
from app.features.rejection_eval.topics import TOPIC_COUNT, TOPICS


async def _get_session(db: AsyncSession, session_id: str) -> RejectionSession:
    session = await db.get(RejectionSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session


async def _get_attempt(db: AsyncSession, session_id: str, topic_index: int) -> RejectionAttempt:
    if not 0 <= topic_index < TOPIC_COUNT:
        raise HTTPException(status_code=404, detail="topic not found")
    result = await db.execute(
        select(RejectionAttempt).where(
            RejectionAttempt.session_id == session_id,
            RejectionAttempt.topic_index == topic_index,
        )
    )
    attempt = result.scalar_one_or_none()
    if attempt is None:
        raise HTTPException(status_code=404, detail="attempt not found")
    return attempt


async def create_session(
    db: AsyncSession, candidate_name: str | None = None
) -> CreateSessionResponse:
    name = (candidate_name or "").strip() or "익명"
    session = RejectionSession(candidate_name=name)
    db.add(session)
    await db.flush()  # assign session.id before linking attempts
    for index, topic in enumerate(TOPICS):
        db.add(
            RejectionAttempt(
                session_id=session.id, topic_index=index, topic_title=topic.title
            )
        )
    await db.commit()
    return CreateSessionResponse(
        session_id=session.id,
        candidate_name=name,
        topics=[
            TopicMeta(
                index=i,
                title=t.title,
                description=t.description,
                requirements=list(t.requirements),
            )
            for i, t in enumerate(TOPICS)
        ],
    )


async def generate_for_topic(
    db: AsyncSession, session_id: str, topic_index: int, prompt: str
) -> GenerateResponse:
    attempt = await _get_attempt(db, session_id, topic_index)
    output = await generate_design(attempt.topic_title, prompt)
    attempt.prompt = prompt
    attempt.generated_items = [item.model_dump() for item in output.items]
    await db.commit()
    return GenerateResponse(
        topic_index=topic_index,
        items=[PublicItem(id=i.id, text=i.text) for i in output.items],
    )


async def submit_for_topic(
    db: AsyncSession, session_id: str, topic_index: int, req: SubmitRequest
) -> SubmitResponse:
    attempt = await _get_attempt(db, session_id, topic_index)
    if attempt.generated_items is None:
        raise HTTPException(status_code=409, detail="generate before submitting")
    attempt.selections = {"flagged_ids": req.flagged_ids, "reasons": req.reasons}
    await db.commit()
    return SubmitResponse(topic_index=topic_index, submitted=True)


async def score_session(db: AsyncSession, session_id: str) -> ResultResponse:
    session = await _get_session(db, session_id)
    result = await db.execute(
        select(RejectionAttempt)
        .where(RejectionAttempt.session_id == session_id)
        .order_by(RejectionAttempt.topic_index)
    )
    attempts = list(result.scalars())

    per_attempt_scores: list[dict] = []
    for attempt in attempts:
        if attempt.generated_items is None or attempt.selections is None:
            raise HTTPException(
                status_code=409, detail="all topics must be generated and submitted"
            )
        items = [GeneratedItem(**i) for i in attempt.generated_items]
        flagged_ids = list(attempt.selections.get("flagged_ids", []))
        reasons = dict(attempt.selections.get("reasons", {}))
        requirements = list(TOPICS[attempt.topic_index].requirements)
        judge = await judge_attempt(requirements, items, flagged_ids, reasons)
        out_of_scope_ids = [
            j.item_id for j in judge.judgements if not j.in_requirements
        ]
        scored = score_items(attempt.generated_items, flagged_ids, out_of_scope_ids)
        attempt.judge_result = {
            "report": judge.report,
            "items": scored["items"],
            "tp": scored["tp"],
            "fp": scored["fp"],
            "fn": scored["fn"],
        }
        attempt.precision = scored["precision"]
        attempt.recall = scored["recall"]
        attempt.f1 = scored["f1"]
        per_attempt_scores.append(scored)

    precision, recall, f1 = aggregate(per_attempt_scores)
    session.precision, session.recall, session.f1 = precision, recall, f1
    session.status = "scored"
    await db.commit()
    return await get_result(db, session_id)


async def get_result(db: AsyncSession, session_id: str) -> ResultResponse:
    session = await _get_session(db, session_id)
    if session.status != "scored":
        raise HTTPException(status_code=409, detail="session not scored yet")
    result = await db.execute(
        select(RejectionAttempt)
        .where(RejectionAttempt.session_id == session_id)
        .order_by(RejectionAttempt.topic_index)
    )
    attempts = list(result.scalars())

    topics: list[ResultTopic] = []
    for attempt in attempts:
        judge_result = attempt.judge_result or {}
        topics.append(
            ResultTopic(
                topic_index=attempt.topic_index,
                topic_title=attempt.topic_title,
                prompt=attempt.prompt or "",
                items=[ResultItem(**i) for i in judge_result.get("items", [])],
                precision=attempt.precision or 0.0,
                recall=attempt.recall or 0.0,
                f1=attempt.f1 or 0.0,
                report=judge_result.get("report", ""),
            )
        )

    return ResultResponse(
        session_id=session.id,
        candidate_name=session.candidate_name,
        status=session.status,
        precision=session.precision or 0.0,
        recall=session.recall or 0.0,
        f1=session.f1 or 0.0,
        topics=topics,
    )
