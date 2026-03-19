from __future__ import annotations

from pathlib import Path


def test_core_runtime_avoids_direct_event_bus_publish():
    """Run lifecycle and worker paths must fan out through ``emit()`` (see ``core/events/emitter.py``)."""
    root = Path(__file__).resolve().parents[2] / 'core' / 'runtime'
    for path in sorted(root.rglob('*.py')):
        text = path.read_text(encoding='utf-8')
        assert 'event_bus.publish' not in text, f'{path.relative_to(root.parents[1])} must use emit(), not event_bus.publish'
