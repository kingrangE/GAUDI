"""Seed the CS deep-evaluation questions into the database (idempotent).

Run from `backend/`:  python -m app.scripts.seed_cs_questions

Mirrors `seed_problems.py`: `seed_if_empty()` is the non-destructive startup
path (only fills an empty table), while the CLI `main()` does a destructive
upsert so re-running converges to the definitions in `questions.py`.
"""

import asyncio

from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal, engine, init_models
from app.features.cs_eval.models import CsQuestion
from app.features.cs_eval.questions import QUESTIONS, QuestionSeed


def _insert(db, seed: QuestionSeed) -> None:
    """Add one question to the session (no commit)."""
    db.add(
        CsQuestion(
            id=seed.id,
            domain=seed.domain,
            prompt_md=seed.prompt_md,
            reference_answer=seed.reference_answer,
            rubric=seed.rubric,
            ordinal=seed.ordinal,
        )
    )


async def _upsert(db, seed: QuestionSeed) -> None:
    existing = await db.get(CsQuestion, seed.id)
    if existing is not None:
        await db.delete(existing)
        await db.flush()
    _insert(db, seed)


async def seed_if_empty() -> int:
    """Seed questions only when the table is empty; returns how many were added.

    Non-destructive and idempotent: safe to call on every startup. It never
    deletes existing questions (so it won't touch a populated DB or its
    sessions) — it only fills a fresh/empty table.
    """
    async with AsyncSessionLocal() as db:
        count = await db.scalar(select(func.count()).select_from(CsQuestion))
        if count:
            return 0
        for seed in QUESTIONS:
            _insert(db, seed)
        await db.commit()
    return len(QUESTIONS)


async def main() -> None:
    await init_models()
    async with AsyncSessionLocal() as db:
        for seed in QUESTIONS:
            await _upsert(db, seed)
        await db.commit()
    # Dispose the engine so aiosqlite's connection thread is released and the
    # process exits cleanly (a lingering non-daemon thread would hang exit).
    await engine.dispose()
    print(f"seeded {len(QUESTIONS)} CS questions: {', '.join(q.id for q in QUESTIONS)}")


if __name__ == "__main__":
    asyncio.run(main())
