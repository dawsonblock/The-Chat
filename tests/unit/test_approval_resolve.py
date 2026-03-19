from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest

from core.approvals.service import approval_service
from storage.db import SessionLocal
from storage.migrate import ensure_schema
from storage.models import ApprovalRequest, Run, ToolCall


@pytest.fixture(autouse=True)
def _schema():
    ensure_schema()


def test_resolve_rejects_mismatched_run_id():
    run_a = str(uuid4())
    run_b = str(uuid4())
    tc = str(uuid4())
    with SessionLocal() as db:
        db.add(Run(user_id='u1', id=run_a, kind='chat', status='running', input_payload={}))
        db.add(Run(user_id='u1', id=run_b, kind='chat', status='running', input_payload={}))
        db.add(ToolCall(id=tc, run_id=run_a, tool_name='x', args={}, status='running', started_at=datetime.utcnow()))
        db.add(
            ApprovalRequest(
                run_id=run_a,
                tool_call_id=tc,
                title='t',
                reason='r',
                risk='low',
                args_preview={},
            )
        )
        db.commit()
        ap_id = db.query(ApprovalRequest).filter(ApprovalRequest.run_id == run_a).first().id

    with pytest.raises(ValueError, match='approval not found'):
        approval_service.resolve(ap_id, 'approve', run_id=run_b)

    row = approval_service.resolve(ap_id, 'approve', run_id=run_a)
    assert row.decision == 'approve'
