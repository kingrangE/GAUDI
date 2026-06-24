"""Centralized application configuration.

All LLM provider/model selection lives here (one config module — never scatter
model IDs across files). Values come from the environment / `.env`.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database — defaults to a local SQLite file so the app runs without Postgres.
    # Production overrides via DATABASE_URL (e.g. postgresql+asyncpg://...).
    database_url: str = "sqlite+aiosqlite:///./and_you.db"

    # LLM provider config (OpenAI). The model ID is centralized here and
    # overridable via the LLM_MODEL env var.
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # Comma-separated list of allowed CORS origins for the frontend.
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
