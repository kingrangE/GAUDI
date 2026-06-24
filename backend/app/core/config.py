"""Centralized application configuration.

All LLM provider/model selection lives here (one config module — never scatter
model IDs across files). Values come from the environment / `.env`.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve `.env` against the backend root (this file is backend/app/core/config.py),
# not the process CWD — otherwise launching uvicorn from anywhere but `backend/`
# silently fails to load the key. This is the single `.env` reader for the backend.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    # Database — defaults to a local SQLite file so the app runs without Postgres.
    # Production overrides via DATABASE_URL (e.g. postgresql+asyncpg://...).
    database_url: str = "sqlite+aiosqlite:///./and_you.db"

    # LLM provider config (OpenAI). All LLM model/provider selection is centralized
    # here (one `.env` reader); `llm/config.py` consumes these for the dev-prompting
    # solver and spec-design generator/judge instead of reading os.environ directly.
    openai_api_key: str = ""
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    # LLM-as-judge runs COLD by default: a judge must be reproducible (same submission ->
    # same verdict). Structured-output judging defaults to this; override via JUDGE_TEMPERATURE.
    judge_temperature: float = 0.0

    # dev-prompting solver — a small, *fixed* model so evaluation measures prompting
    # skill, not raw model power.
    solver_model: str = "gpt-4o-mini"
    solver_temperature: float = 0.2

    # spec-design generator — intentionally *hot* (vague instructions diverge across
    # samples); output capped so a rambling hot model can't blow up latency.
    spec_gen_model: str = "gpt-4.1-nano"
    spec_gen_temperature: float = 1.3
    spec_gen_max_tokens: int = 800

    # spec-design judge — low temperature for stable decision extraction.
    spec_judge_model: str = "gpt-5.4"
    spec_judge_temperature: float = 0.0
    spec_judge_max_tokens: int = 500

    # How many samples spec-design generates per evaluation.
    spec_samples: int = 10

    # Comma-separated list of allowed CORS origins for the frontend.
    cors_origins: str = "http://localhost:3000"

    # Optional shared secret guarding the admin read API. When set, admin
    # requests must send it as the `X-Admin-Token` header. Empty = open
    # (dev/demo default; the frontend already gates entry behind the ADMIN code).
    admin_token: str = ""

    # Background grading. "inline" runs grading in-process (default; used by
    # tests and a no-broker setup); "rq" enqueues to an RQ worker via Redis.
    redis_url: str = "redis://localhost:6379/0"
    grading_mode: Literal["inline", "rq"] = "inline"

    # On startup, seed the coding-test problems when the table is empty so a
    # fresh DB serves problems without a manual `python -m app.scripts.seed_problems`
    # step. Non-destructive (only runs when empty). Disable for prod/migrations.
    auto_seed_problems: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
