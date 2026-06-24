"""Seed the coding-test problems into the database (idempotent).

Run from `backend/`:  python -m app.scripts.seed_problems

Upserts each problem by slug — deleting an existing problem (cascade-removing
its test cases) and re-inserting — so re-running always converges to the seed
definitions in `problems.py`.
"""

import asyncio
import json

from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal, engine, init_models
from app.features.coding_test.models import Problem, TestCase
from app.features.coding_test.problems import PROBLEMS, ProblemSeed


def _insert(db, seed: ProblemSeed) -> None:
    """Add one problem and its test cases to the session (no commit)."""
    db.add(
        Problem(
            id=seed.id,
            title=seed.title,
            description_md=seed.description_md,
            function_name=seed.function_name,
            starter_code=seed.starter_code,
            difficulty=seed.difficulty,
            reference_solution=seed.reference_solution,
            rubric=seed.rubric,
            comparison=seed.comparison,
        )
    )
    ordinal = 0
    for kind, cases in (("sample", seed.samples), ("grading", seed.grading)):
        for case in cases:
            db.add(
                TestCase(
                    problem_id=seed.id,
                    kind=kind,
                    args_json=json.dumps(case.args),
                    expected_json=json.dumps(case.expected),
                    ordinal=ordinal,
                )
            )
            ordinal += 1


async def _upsert(db, seed: ProblemSeed) -> None:
    existing = await db.get(Problem, seed.id)
    if existing is not None:
        await db.delete(existing)  # cascade removes its test cases
        await db.flush()
    _insert(db, seed)


async def seed_if_empty() -> int:
    """Seed problems only when the table is empty; returns how many were added.

    Non-destructive and idempotent: safe to call on every startup. Unlike the
    CLI's `_upsert`, this never deletes existing problems (so it won't touch a
    populated DB or its submissions) — it only fills a fresh/empty table.
    """
    async with AsyncSessionLocal() as db:
        count = await db.scalar(select(func.count()).select_from(Problem))
        if count:
            return 0
        for seed in PROBLEMS:
            _insert(db, seed)
        await db.commit()
    return len(PROBLEMS)


async def main() -> None:
    await init_models()
    async with AsyncSessionLocal() as db:
        for seed in PROBLEMS:
            await _upsert(db, seed)
        await db.commit()
    # Dispose the engine so aiosqlite's connection thread is released and the
    # process exits cleanly (a lingering non-daemon thread would hang exit).
    await engine.dispose()
    print(f"seeded {len(PROBLEMS)} problems: {', '.join(p.id for p in PROBLEMS)}")


if __name__ == "__main__":
    asyncio.run(main())
