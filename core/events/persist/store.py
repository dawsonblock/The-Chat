"""Re-export authoritative event persistence ([`core.events.store`](../store.py))."""

from core.events.store import EventStore, event_store

__all__ = ['EventStore', 'event_store']
