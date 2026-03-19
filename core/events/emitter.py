from __future__ import annotations

from typing import Any

from core.events.bus import event_bus


async def emit(run_id: str, event: dict[str, Any]) -> dict[str, Any]:
    """Persist `RunEvent` and fan out to SSE subscribers (single write path for runtime/tool events).

    Prefer this over calling ``event_store`` + ``event_bus`` separately.
    """
    return await event_bus.publish(run_id, event)


__all__ = ['emit']
