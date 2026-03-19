"""Lightweight additive migrations for existing databases."""

from __future__ import annotations

from sqlalchemy import inspect, text

from storage.db import Base, engine


def _sqlite_columns(table: str) -> set[str]:
    insp = inspect(engine)
    return {c['name'] for c in insp.get_columns(table)}


def ensure_schema() -> None:
    """Create any missing tables (e.g. new models on old SQLite files), then apply SQLite ALTERs."""
    import storage.models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    url = str(engine.url)
    if not url.startswith('sqlite'):
        return

    insp = inspect(engine)
    tables = set(insp.get_table_names())
    if 'runs' not in tables:
        return

    with engine.begin() as conn:
        runs = _sqlite_columns('runs')
        if 'failure_class' not in runs:
            conn.execute(text('ALTER TABLE runs ADD COLUMN failure_class VARCHAR'))
        if 'cancel_requested' not in runs:
            conn.execute(text('ALTER TABLE runs ADD COLUMN cancel_requested BOOLEAN NOT NULL DEFAULT 0'))

        if 'tool_calls' in tables:
            tools = _sqlite_columns('tool_calls')
            if 'idempotency_key' not in tools:
                conn.execute(text('ALTER TABLE tool_calls ADD COLUMN idempotency_key VARCHAR'))
            if 'attempt_count' not in tools:
                conn.execute(text('ALTER TABLE tool_calls ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0'))

        if 'tool_results' in tables:
            results = _sqlite_columns('tool_results')
            if 'failure_class' not in results:
                conn.execute(text('ALTER TABLE tool_results ADD COLUMN failure_class VARCHAR'))
            if 'retryable' not in results:
                conn.execute(text('ALTER TABLE tool_results ADD COLUMN retryable BOOLEAN'))
