"""Crawl job worker (v0.9).

`intake/crawl.py` remains the synchronous entry for shallow crawls. This module
will host a durable worker that claims `CrawlJob` rows, respects per-domain
throttles, and persists frontier state.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


async def crawl_worker_tick() -> None:
    log.debug('crawl_worker_tick: no queued jobs implementation yet')
