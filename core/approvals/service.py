from __future__ import annotations

import asyncio
from datetime import datetime

from storage.db import SessionLocal
from storage.models import ApprovalRequest


class ApprovalService:
    def __init__(self) -> None:
        self._waiters: dict[str, asyncio.Future] = {}

    async def wait_for_decision(self, approval_id: str) -> str:
        with SessionLocal() as db:
            row = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
            if row and row.status == 'decided' and row.decision:
                return row.decision
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._waiters[approval_id] = fut
        try:
            return await fut
        finally:
            self._waiters.pop(approval_id, None)

    def resolve(self, approval_id: str, decision: str) -> ApprovalRequest:
        with SessionLocal() as db:
            row = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
            if not row:
                raise ValueError('approval not found')
            row.status = 'decided'
            row.decision = decision
            row.decided_at = datetime.utcnow()
            db.commit()
            db.refresh(row)
        fut = self._waiters.get(approval_id)
        if fut and not fut.done():
            fut.set_result(decision)
        return row


approval_service = ApprovalService()
