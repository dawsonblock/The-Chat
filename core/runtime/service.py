from __future__ import annotations

from datetime import datetime
from typing import Any

from core.events.emitter import emit
from core.events.schema import build_event
from core.runtime.state.status import RUN_STATUSES
from storage.db import SessionLocal
from storage.models import Conversation, ConversationMessage, Run, RunEvent


class RunService:
    def create_run(self, *, user_id: str, conversation_id: str | None, kind: str, input_payload: dict[str, Any]) -> Run:
        with SessionLocal() as db:
            row = Run(user_id=user_id, conversation_id=conversation_id, kind=kind, status='queued', input_payload=input_payload)
            db.add(row)
            db.flush()
            if conversation_id and input_payload.get('message'):
                convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
                if convo:
                    convo.updated_at = datetime.utcnow()
                db.add(ConversationMessage(conversation_id=conversation_id, role='user', content=input_payload['message'], run_id=row.id))
            db.commit()
            db.refresh(row)
            return row

    def get_run(self, run_id: str) -> Run | None:
        with SessionLocal() as db:
            return db.query(Run).filter(Run.id == run_id).first()

    def list_runs(self, user_id: str) -> list[Run]:
        with SessionLocal() as db:
            return db.query(Run).filter(Run.user_id == user_id).order_by(Run.created_at.desc()).all()

    def set_status(
        self,
        run_id: str,
        status: str,
        *,
        error_message: str | None = None,
        failure_class: str | None = None,
    ) -> Run:
        if status not in RUN_STATUSES:
            raise ValueError(f'invalid status {status}')
        with SessionLocal() as db:
            row = db.query(Run).filter(Run.id == run_id).first()
            row.status = status
            if status == 'running' and row.started_at is None:
                row.started_at = datetime.utcnow()
            if status in {'succeeded', 'failed', 'cancelled'}:
                row.finished_at = datetime.utcnow()
            if error_message is not None:
                row.error_message = error_message
            if failure_class is not None:
                row.failure_class = failure_class
            db.commit()
            db.refresh(row)
            return row

    def set_output(self, run_id: str, text: str) -> None:
        with SessionLocal() as db:
            row = db.query(Run).filter(Run.id == run_id).first()
            row.output_text = text
            if row.conversation_id:
                convo = db.query(Conversation).filter(Conversation.id == row.conversation_id).first()
                if convo:
                    convo.updated_at = datetime.utcnow()
                existing = (
                    db.query(ConversationMessage)
                    .filter(ConversationMessage.run_id == run_id, ConversationMessage.role == 'assistant')
                    .first()
                )
                if existing:
                    existing.content = text
                else:
                    db.add(ConversationMessage(conversation_id=row.conversation_id, role='assistant', content=text, run_id=run_id))
            db.commit()

    def request_cancel(self, run_id: str) -> None:
        with SessionLocal() as db:
            row = db.query(Run).filter(Run.id == run_id).first()
            if row:
                row.cancel_requested = True
                db.commit()

    def clear_cancel(self, run_id: str) -> None:
        with SessionLocal() as db:
            row = db.query(Run).filter(Run.id == run_id).first()
            if row:
                row.cancel_requested = False
                db.commit()

    def claim_next_queued_run(self) -> Run | None:
        with SessionLocal() as db:
            row = (
                db.query(Run)
                .filter(Run.status == 'queued', Run.cancel_requested.is_(False))
                .order_by(Run.created_at.asc())
                .first()
            )
            if not row:
                return None
            row.status = 'running'
            if row.started_at is None:
                row.started_at = datetime.utcnow()
            db.commit()
            db.refresh(row)
            return row

    def has_run_event_type(self, run_id: str, event_type: str) -> bool:
        with SessionLocal() as db:
            return (
                db.query(RunEvent)
                .filter(RunEvent.run_id == run_id, RunEvent.event_type == event_type)
                .first()
                is not None
            )

    async def emit_created_if_needed(self, run_id: str) -> None:
        if not self.has_run_event_type(run_id, 'run.created'):
            await self.emit_created(run_id)

    def fail_run(self, run_id: str, message: str, *, failure_class: str) -> None:
        self.set_status(run_id, 'failed', error_message=message, failure_class=failure_class)

    async def emit_created(self, run_id: str):
        await emit(run_id, build_event('run.created', runId=run_id))

    async def emit_status(self, run_id: str, status: str):
        await emit(run_id, build_event('run.status', runId=run_id, status=status))

    async def emit_text(self, run_id: str, text: str, chunk_size: int = 160):
        for i in range(0, len(text), chunk_size):
            await emit(run_id, build_event('message.delta', runId=run_id, text=text[i:i + chunk_size]))


run_service = RunService()
