"""Optional Redis wake-up for the run worker (LPUSH when a run is queued)."""

from __future__ import annotations

import logging

from backend.config import settings

log = logging.getLogger(__name__)

QUEUE_KEY = 'operator_one:queued_runs'


def notify_run_queued(run_id: str) -> None:
    url = (settings.redis_url or '').strip()
    if not url:
        return
    try:
        import redis

        r = redis.Redis.from_url(url, decode_responses=True)
        r.lpush(QUEUE_KEY, run_id)
    except Exception:
        log.warning('notify_run_queued redis failed run_id=%s', run_id, exc_info=True)
