"""Shared RQ queue accessor.

Lazy like the LLM client: importing this module never opens a Redis connection,
so tests and non-grading code paths don't require a running broker.
"""

from functools import lru_cache

from redis import Redis
from rq import Queue

from app.core.config import get_settings

GRADING_QUEUE = "grading"


@lru_cache
def get_queue() -> Queue:
    settings = get_settings()
    return Queue(GRADING_QUEUE, connection=Redis.from_url(settings.redis_url))
