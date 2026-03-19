from __future__ import annotations

from storage.db import SessionLocal
from storage.models import Run


class CancellationService:
    def is_cancelled(self, run_id: str) -> bool:
        with SessionLocal() as db:
            row = db.query(Run).filter(Run.id == run_id).first()
            return bool(row and row.cancel_requested)


cancellation_service = CancellationService()
