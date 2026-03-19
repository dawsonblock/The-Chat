"""Persisted run events (matrix alias for ``core.events.store``)."""

from core.events.persist.store import EventStore, event_store

__all__ = ['EventStore', 'event_store']
