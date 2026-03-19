from __future__ import annotations

import asyncio
import logging

from backend.config import settings
from core.events.bus import event_bus
from core.events.schema import build_event
from core.runtime.engine import RuntimeEngine
from core.runtime.service import run_service

log = logging.getLogger(__name__)


async def runtime_worker_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
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
                await event_bus.publish(
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
