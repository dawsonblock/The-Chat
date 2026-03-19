from __future__ import annotations

import asyncio
import logging

from backend.config import settings
from core.events.emitter import emit
from core.events.schema import build_event
from core.runtime.engine import RuntimeEngine
from core.runtime.run_queue_signal import QUEUE_KEY
from core.runtime.service import run_service

log = logging.getLogger(__name__)


def _brpop_run_id(timeout: int = 2) -> str | None:
    url = (settings.redis_url or '').strip()
    if not url:
        return None
    try:
        import redis

        r = redis.Redis.from_url(url, decode_responses=True)
        item = r.brpop(QUEUE_KEY, timeout=timeout)
        return item[1] if item else None
    except Exception:
        log.warning('redis brpop failed', exc_info=True)
        return None


async def runtime_worker_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            run = None
            rid = await asyncio.to_thread(_brpop_run_id, 2)
            if rid:
                run = run_service.try_claim_queued_run(rid)
            if not run:
                run = run_service.claim_next_queued_run()
            if not run:
                try:
                    await asyncio.wait_for(stop.wait(), timeout=settings.worker_poll_interval_seconds)
                except asyncio.TimeoutError:
                    pass
                continue
            try:
                await asyncio.wait_for(RuntimeEngine().run(run.id), timeout=settings.run_timeout_seconds)
            except asyncio.TimeoutError:
                run_service.fail_run(run.id, 'Run exceeded timeout.', failure_class='timeout')
                await run_service.emit_status(run.id, 'failed')
                await emit(
                    run.id,
                    build_event(
                        'run.failed',
                        runId=run.id,
                        error={'code': 'timeout', 'message': 'Run exceeded timeout.', 'retryable': True},
                    ),
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception('runtime worker tick failed')
            await asyncio.sleep(settings.worker_poll_interval_seconds)
