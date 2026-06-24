"""Assembly entry: the FastAPI app with feature routers wired in.

Run locally:  uvicorn app:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from feature_context_engineering.router import router as context_engineering_router

app = FastAPI(title="and-you")

# Open CORS for local dev (frontend dev server on another port). Tighten for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(context_engineering_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
