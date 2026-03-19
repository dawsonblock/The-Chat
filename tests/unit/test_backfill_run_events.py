from __future__ import annotations

from datetime import datetime

from storage.db import SessionLocal
from storage.migrate import backfill_run_events_from_tool_calls, ensure_schema
from storage.models import Run, RunEvent, ToolCall, ToolResult


def test_backfill_inserts_tool_events_idempotent():
    ensure_schema()
    with SessionLocal() as db:
        run = Run(user_id='u1', kind='chat', status='succeeded', input_payload={'message': 'hi'})
        db.add(run)
        db.flush()
        tc = ToolCall(
            id='tc-backfill-1',
            run_id=run.id,
            tool_name='extract_page',
            args={'url': 'https://example.com'},
            status='succeeded',
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
        )
        db.add(tc)
        db.add(ToolResult(tool_call_id=tc.id, ok=True, output={'x': 1}))
        db.commit()
        rid = run.id

    c1 = backfill_run_events_from_tool_calls()
    assert c1['tool.started'] >= 1
    assert c1['tool.finished'] >= 1

    with SessionLocal() as db:
        evs = db.query(RunEvent).filter(RunEvent.run_id == rid).order_by(RunEvent.seq_no.asc()).all()
        types = [e.event_type for e in evs]
        assert 'tool.started' in types
        assert 'tool.finished' in types

    c2 = backfill_run_events_from_tool_calls()
    assert c2['tool.started'] == 0
    assert c2['tool.finished'] == 0
