"""Backend app entry — assembly point that mounts feature routers.

Run locally: `python -m uvicorn app:app --reload --port 8000` (from backend/).
Only the spec-design feature is wired here on this branch; other features mount their
own routers during full assembly.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from feature_spec_design.api import router as spec_design_router

app = FastAPI(title="and-you backend")

# Allow the Next.js dev frontend (and any configured origins) to call the API.
_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(spec_design_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
