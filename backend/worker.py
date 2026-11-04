"""RQ worker entry point.  Run from `backend/`:  python worker.py

Processes the grading queue. Requires Redis (see docker-compose.yml) and the
backend env (`REDIS_URL`, `OPENAI_API_KEY`, `DATABASE_URL`). Importing the
feature models registers their tables for any DB access in jobs.
"""

from redis import Redis
from rq import Queue, Worker

import app.features.coding_test.models  # noqa: F401  (register tables on Base)
from app.core.config import get_settings
from app.queue import DEMO_QUEUE, GRADING_QUEUE


def main() -> None:
    connection = Redis.from_url(get_settings().redis_url)
    worker = Worker(
        [Queue(name, connection=connection) for name in (GRADING_QUEUE, DEMO_QUEUE)],
        connection=connection,
    )
    worker.work()


if __name__ == "__main__":
    main()
