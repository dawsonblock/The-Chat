"""Lightweight additive migrations for existing databases."""

from __future__ import annotations

from sqlalchemy import func, inspect, select, text

from storage.db import Base, SessionLocal, engine


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


def _existing_tool_event_ids_for_run(db, run_id: str) -> tuple[set[str], set[str]]:
    """Return (started_ids, finished_ids) from ``run_events`` payloads."""
    from storage.models import RunEvent

    started: set[str] = set()
    finished: set[str] = set()
    rows = db.query(RunEvent).filter(RunEvent.run_id == run_id).all()
    for row in rows:
        p = row.payload if isinstance(row.payload, dict) else {}
        if row.event_type == 'tool.started':
            t = p.get('tool') if isinstance(p.get('tool'), dict) else {}
            tid = t.get('id')
            if tid:
                started.add(tid)
        elif row.event_type == 'tool.finished':
            res = p.get('result') if isinstance(p.get('result'), dict) else {}
            tid = res.get('toolCallId')
            if tid:
                finished.add(tid)
    return started, finished


def _next_run_event_seq(db, run_id: str) -> int:
    from storage.models import RunEvent

    m = db.scalar(select(func.max(RunEvent.seq_no)).where(RunEvent.run_id == run_id))
    return (m or 0) + 1


def backfill_run_events_from_tool_calls() -> dict[str, int]:
    """Insert missing ``tool.started`` / ``tool.finished`` rows into ``run_events`` from relational tool tables.

    Idempotent: safe to run multiple times. Does not delete or modify existing events.
    See ``docs/schema-collapse.md``.
    """
    from core.events.schema import build_event
    from storage.models import RunEvent, ToolCall, ToolResult

    counts = {'tool.started': 0, 'tool.finished': 0}
    with SessionLocal() as db:
        calls = db.query(ToolCall).order_by(ToolCall.created_at.asc()).all()
        for tc in calls:
            run_id = tc.run_id
            started_ids, finished_ids = _existing_tool_event_ids_for_run(db, run_id)
            if tc.id not in started_ids:
                ev = build_event(
                    'tool.started',
                    runId=run_id,
                    tool={
                        'id': tc.id,
                        'toolName': tc.tool_name,
                        'args': tc.args or {},
                        'status': tc.status,
                    },
                )
                db.add(
                    RunEvent(
                        run_id=run_id,
                        seq_no=_next_run_event_seq(db, run_id),
                        event_type='tool.started',
                        payload=ev,
                    )
                )
                db.commit()
                counts['tool.started'] += 1
            tr = db.query(ToolResult).filter(ToolResult.tool_call_id == tc.id).first()
            if tr:
                _, finished_ids = _existing_tool_event_ids_for_run(db, run_id)
                if tc.id not in finished_ids:
                    payload = {
                        'toolCallId': tc.id,
                        'ok': tr.ok,
                        'output': tr.output if tr.ok else None,
                        'error': None
                        if tr.ok
                        else {'code': tr.error_code, 'message': tr.error_message or ''},
                        'artifacts': [],
                    }
                    ev = build_event('tool.finished', runId=run_id, result=payload)
                    db.add(
                        RunEvent(
                            run_id=run_id,
                            seq_no=_next_run_event_seq(db, run_id),
                            event_type='tool.finished',
                            payload=ev,
                        )
                    )
                    db.commit()
                    counts['tool.finished'] += 1
    return counts
