"""Seed the coding-test problems into the database (idempotent).

Run from `backend/`:  python -m app.scripts.seed_problems

Upserts each problem by slug — deleting an existing problem (cascade-removing
its test cases) and re-inserting — so re-running always converges to the seed
definitions in `problems.py`.
"""

import asyncio
import json

from app.db.session import AsyncSessionLocal, engine, init_models
from app.features.coding_test.models import Problem, TestCase
from app.features.coding_test.problems import PROBLEMS, ProblemSeed


async def _upsert(db, seed: ProblemSeed) -> None:
    existing = await db.get(Problem, seed.id)
    if existing is not None:
        await db.delete(existing)  # cascade removes its test cases
        await db.flush()

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
