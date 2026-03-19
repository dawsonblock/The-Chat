from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from core.events.store import event_store


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[asyncio.Queue]] = defaultdict(list)

    async def publish(self, run_id: str, event: dict[str, Any]) -> dict[str, Any]:
        stored = await event_store.append(run_id, event)
        for queue in list(self._subs.get(run_id, [])):
            await queue.put(stored)
        return stored

    def subscribe(self, run_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subs[run_id].append(q)
        return q

    def unsubscribe(self, run_id: str, q: asyncio.Queue) -> None:
        if run_id in self._subs and q in self._subs[run_id]:
            self._subs[run_id].remove(q)
            if not self._subs[run_id]:
                del self._subs[run_id]


event_bus = EventBus()
