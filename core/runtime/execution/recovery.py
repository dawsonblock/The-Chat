from __future__ import annotations

from storage.db import SessionLocal
from storage.models import ApprovalRequest, Run


def requeue_interrupted_runs() -> int:
    """After process restart, resume durable work and fail approval waits that lost in-memory waiters."""
    with SessionLocal() as db:
        n = 0
        for r in db.query(Run).filter(Run.status == 'running').all():
            r.status = 'queued'
            r.started_at = None
            n += 1
        for r in db.query(Run).filter(Run.status == 'waiting_approval').all():
            r.status = 'failed'
            r.error_message = 'Server restarted while waiting for approval; start a new run.'
            r.failure_class = 'infra'
            for ap in db.query(ApprovalRequest).filter(ApprovalRequest.run_id == r.id, ApprovalRequest.status == 'pending').all():
                ap.status = 'decided'
                ap.decision = 'expire'
            n += 1
        db.commit()
        return n
