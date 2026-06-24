"""Backend app entrypoint (assembly): mounts feature routers + CORS.

Run: `python -m uvicorn main:app --port 8000`

Demo mode: set `DEMO_SOLVER=1` to override the dev-prompting solver with a canned
stub so the flow works without an OpenAI key. This is a demo aid only — it returns a
fixed solution regardless of the prompt, so it does NOT represent real evaluation.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import demo_solutions
from feature_dev_prompting.api import get_solver_client, router

app = FastAPI(title="and-you backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
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
