"""FastAPI application assembly.

Registers feature routers and creates tables on startup (hackathon-simple;
Alembic comes later). Each feature lives under `app/features/<name>/` — importing
its router also imports its models so `create_all()` discovers every table.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.session import init_models
from app.features.rejection_eval.router import router as rejection_eval_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    yield


app = FastAPI(title="and-you backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rejection_eval_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
