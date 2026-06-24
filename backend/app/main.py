"""FastAPI application assembly.

Registers feature routers and creates tables on startup (hackathon-simple;
Alembic comes later). Each shared feature lives under `app/features/<name>/` —
importing its router (and, for test_design, its models) so a single `create_all()`
discovers every table.

This is the single unified entrypoint for all six features. The three shared
features (coding-test, rejection-eval, test-design) plus minsu's top-level feature
packages (dev-prompting, spec-design, context-engineering — mounted from
`feature_*/`, untouched) are served by one app at `:8000`; their prefixes
(`/api/*`, `/dev-prompting/*`, `/spec-design/*`, `/api/context-engineering/*`) don't
collide. Run with `python -m uvicorn app.main:app --port 8000`. Set `DEMO_SOLVER=1`
to stub the dev-prompting solver so the flow works without an OpenAI key (demo aid only).
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import demo_solutions
from app.core.config import get_settings
from app.db.session import init_models
from app.features.coding_test.router import router as coding_test_router
from app.features.rejection_eval.router import router as rejection_eval_router
from app.features.test_design import models as _test_design_models  # noqa: F401  (register tables)
from app.features.test_design.routes import router as test_design_router
from feature_context_engineering.router import router as context_engineering_router
from feature_dev_prompting.api import get_solver_client
from feature_dev_prompting.api import router as dev_prompting_router
from feature_spec_design.api import router as spec_design_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    if get_settings().auto_seed_problems:
        from app.scripts.seed_problems import seed_if_empty

        seeded = await seed_if_empty()
        if seeded:
            print(f"auto-seeded {seeded} coding-test problems into an empty DB")
    yield


app = FastAPI(title="and-you backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rejection_eval_router)
app.include_router(coding_test_router)
app.include_router(test_design_router)
app.include_router(dev_prompting_router)
app.include_router(spec_design_router)
app.include_router(context_engineering_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if os.getenv("DEMO_SOLVER"):

    class _DemoSolver:
        """Returns the reference solution for whichever problem the prompt describes."""

        def complete(self, system: str, user: str) -> str:
            for pid, phrase in demo_solutions.DETECT.items():
                if phrase in user:
                    return demo_solutions.REFERENCE[pid]
            return "def solution(*args):\n    return None\n"

    app.dependency_overrides[get_solver_client] = lambda: _DemoSolver()
