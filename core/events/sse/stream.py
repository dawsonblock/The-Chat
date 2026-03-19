from __future__ import annotations

import json
from typing import Any


def format_sse_event(event: dict[str, Any]) -> str:
    seq = event.get('seq_no', '')
    typ = event.get('type', 'message')
    return f"id: {seq}\nevent: {typ}\ndata: {json.dumps(event)}\n\n"


def sse_keepalive() -> str:
    return ': keep-alive\n\n'
