from __future__ import annotations

from pathlib import Path


def test_tool_dispatcher_does_not_call_event_bus_publish_directly():
    root = Path(__file__).resolve().parents[2]
    text = (root / 'core' / 'tools' / 'dispatcher.py').read_text(encoding='utf-8')
    assert 'event_bus.publish' not in text
    assert 'from core.events.emitter import emit' in text or 'core.events.emitter' in text
