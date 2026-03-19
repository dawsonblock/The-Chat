from __future__ import annotations

import asyncio
import logging
import os

from backend.config import settings
from core.observability import configure_logging
from core.runtime.worker import runtime_worker_loop
from storage.bootstrap import init_db
from core.runtime.execution.recovery import requeue_interrupted_runs

configure_logging(json_logs=os.environ.get('JSON_LOGS', '').lower() in {'1', 'true', 'yes'})
log = logging.getLogger(__name__)


async def _run() -> None:
    init_db()
    requeue_interrupted_runs()
    log.info('standalone_worker_started poll=%s', settings.worker_poll_interval_seconds)
    stop = asyncio.Event()
    await runtime_worker_loop(stop)


def main() -> None:
    asyncio.run(_run())


if __name__ == '__main__':
    main()
