from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth.service import get_current_user
from storage.db import SessionLocal
from storage.models import Conversation, ConversationMessage, Run
from datetime import datetime

router = APIRouter(prefix='/api/conversations', tags=['conversations'])


class ConversationBody(BaseModel):
    title: str = 'New conversation'


@router.get('')
def list_conversations(user=Depends(get_current_user)):
    with SessionLocal() as db:
        rows = db.query(Conversation).filter(Conversation.user_id == user.user_id).order_by(Conversation.updated_at.desc()).all()
        return [{'id': row.id, 'title': row.title, 'created_at': row.created_at.isoformat(), 'updated_at': row.updated_at.isoformat()} for row in rows]


@router.post('')
def create_conversation(body: ConversationBody, user=Depends(get_current_user)):
    with SessionLocal() as db:
        row = Conversation(user_id=user.user_id, title=body.title, updated_at=datetime.utcnow())
        db.add(row)
        db.commit()
        db.refresh(row)
        return {'id': row.id, 'title': row.title, 'created_at': row.created_at.isoformat(), 'updated_at': row.updated_at.isoformat()}


@router.get('/{conversation_id}')
def get_conversation(conversation_id: str, user=Depends(get_current_user)):
    with SessionLocal() as db:
        convo = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.user_id).first()
        if not convo:
            raise HTTPException(status_code=404, detail='Conversation not found')
        messages = db.query(ConversationMessage).filter(ConversationMessage.conversation_id == conversation_id).order_by(ConversationMessage.created_at.asc()).all()
        return {
            'id': convo.id,
            'title': convo.title,
            'messages': [{'id': m.id, 'role': m.role, 'content': m.content, 'run_id': m.run_id, 'created_at': m.created_at.isoformat()} for m in messages],
        }


@router.get('/{conversation_id}/runs')
def list_conversation_runs(conversation_id: str, user=Depends(get_current_user)):
    with SessionLocal() as db:
        convo = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.user_id).first()
        if not convo:
            raise HTTPException(status_code=404, detail='Conversation not found')
        rows = db.query(Run).filter(Run.conversation_id == conversation_id, Run.user_id == user.user_id).order_by(Run.created_at.desc()).all()
        return [
            {
                'id': run.id,
                'kind': run.kind,
                'status': run.status,
                'output_text': run.output_text,
                'error_message': run.error_message,
                'created_at': run.created_at.isoformat(),
                'started_at': run.started_at.isoformat() if run.started_at else None,
                'finished_at': run.finished_at.isoformat() if run.finished_at else None,
            }
            for run in rows
        ]
