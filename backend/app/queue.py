"""Shared RQ queue accessor.

Lazy like the LLM client: importing this module never opens a Redis connection,
so tests and non-grading code paths don't require a running broker.
"""

from functools import lru_cache

from redis import Redis
from redis.backoff import NoBackoff
from redis.retry import Retry
from rq import Queue

from app.core.config import get_settings

GRADING_QUEUE = "grading"
DEMO_QUEUE = "demo"


@lru_cache
def get_queue() -> Queue:
    settings = get_settings()
    return Queue(GRADING_QUEUE, connection=Redis.from_url(settings.redis_url))


@lru_cache
def get_demo_queue() -> Queue:
    connection = Redis.from_url(
        get_settings().redis_url,
        socket_connect_timeout=3,
        socket_timeout=3,
        retry=Retry(NoBackoff(), 0),
    )
    return Queue(DEMO_QUEUE, connection=connection)
