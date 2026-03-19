from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from sqlalchemy import func, select

from storage.db import SessionLocal
from storage.models import RunEvent


class EventStore:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def append(self, run_id: str, event: dict[str, Any]) -> dict[str, Any]:
        async with self._locks[run_id]:
            with SessionLocal() as db:
                max_seq = db.scalar(select(func.max(RunEvent.seq_no)).where(RunEvent.run_id == run_id)) or 0
                row = RunEvent(run_id=run_id, seq_no=max_seq + 1, event_type=event['type'], payload=event)
                db.add(row)
                db.commit()
                db.refresh(row)
                stored = {'id': row.id, 'seq_no': row.seq_no, **row.payload, 'created_at': row.created_at.isoformat()}
                return stored

    def load_after(self, run_id: str, last_seq: int = 0) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            rows = db.query(RunEvent).filter(RunEvent.run_id == run_id, RunEvent.seq_no > last_seq).order_by(RunEvent.seq_no.asc()).all()
            return [{'id': r.id, 'seq_no': r.seq_no, **r.payload, 'created_at': r.created_at.isoformat()} for r in rows]


event_store = EventStore()
