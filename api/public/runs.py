from __future__ import annotations

import asyncio
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.approvals.service import approval_service
from core.events.sse.stream import format_sse_event, sse_keepalive
from core.auth.runs import require_run_for_user
from core.auth.service import get_current_user
from core.events.bus import event_bus
from core.events.store import event_store
from core.runtime.control import cancel_run
from core.runtime.service import run_service
from core.workflows.service import workflow_service
from storage.db import SessionLocal
from storage.models import ApprovalRequest, Artifact, Run, RunEvent, ToolCall, ToolResult

router = APIRouter(prefix='/api/runs', tags=['runs'])


class CreateRunBody(BaseModel):
    kind: Literal['chat', 'workflow']
    input: dict[str, Any]


class ChatRunBody(BaseModel):
    message: str
    conversation_id: str | None = None
    attachments: list[str] = []


class ApprovalBody(BaseModel):
    approval_id: str
    decision: str


@router.get('')
def list_runs(user=Depends(get_current_user)):
    rows = run_service.list_runs(user.user_id)
    return [
        {
            'id': r.id,
            'kind': r.kind,
            'status': r.status,
            'created_at': r.created_at.isoformat(),
            'started_at': r.started_at.isoformat() if r.started_at else None,
            'finished_at': r.finished_at.isoformat() if r.finished_at else None,
            'conversation_id': r.conversation_id,
            'output_text': r.output_text,
            'error_message': r.error_message,
            'failure_class': r.failure_class,
        }
        for r in rows
    ]


@router.post('')
def create_run(body: CreateRunBody, user=Depends(get_current_user)):
    if body.kind == 'chat':
        message = (body.input.get('message') or '').strip()
        conversation_id = body.input.get('conversation_id')
        attachments = body.input.get('attachments') or []
        if not isinstance(attachments, list):
            raise HTTPException(status_code=400, detail='attachments must be a list')
        run = run_service.create_run(
            user_id=user.user_id,
            conversation_id=conversation_id,
            kind='chat',
            input_payload={'message': message, 'attachments': attachments},
        )
        return {'run_id': run.id, 'status': run.status}
    if body.kind == 'workflow':
        wv = body.input.get('workflow_version_id')
        if not wv:
            raise HTTPException(status_code=400, detail='workflow run requires input.workflow_version_id')
        inputs = body.input.get('inputs') or {}
        if not isinstance(inputs, dict):
            raise HTTPException(status_code=400, detail='inputs must be an object')
        run = workflow_service.create_run(user_id=user.user_id, workflow_version_id=str(wv), inputs=inputs)
        return {'run_id': run.id, 'status': run.status}
    raise HTTPException(status_code=400, detail='invalid kind')


@router.post('/chat')
def create_chat_run(body: ChatRunBody, user=Depends(get_current_user)):
    return create_run(
        CreateRunBody(
            kind='chat',
            input={'message': body.message, 'conversation_id': body.conversation_id, 'attachments': body.attachments},
        ),
        user,
    )


@router.get('/{run_id}')
def get_run(run_id: str, user=Depends(get_current_user)):
    run = run_service.get_run(run_id)
    if not run or run.user_id != user.user_id:
        raise HTTPException(status_code=404, detail='Run not found')
    return {
        'id': run.id,
        'kind': run.kind,
        'status': run.status,
        'conversation_id': run.conversation_id,
        'input_payload': run.input_payload,
        'output_text': run.output_text,
        'error_message': run.error_message,
        'failure_class': run.failure_class,
        'created_at': run.created_at.isoformat(),
        'started_at': run.started_at.isoformat() if run.started_at else None,
        'finished_at': run.finished_at.isoformat() if run.finished_at else None,
    }


@router.get('/{run_id}/bundle')
def get_run_bundle(run_id: str, user=Depends(get_current_user)):
    require_run_for_user(run_id, user.user_id)
    with SessionLocal() as db:
        run = db.query(Run).filter(Run.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail='Run not found')
        events = db.query(RunEvent).filter(RunEvent.run_id == run_id).order_by(RunEvent.seq_no.asc()).all()
        tools = db.query(ToolCall).filter(ToolCall.run_id == run_id).order_by(ToolCall.created_at.asc()).all()
        results = db.query(ToolResult).join(ToolCall, ToolCall.id == ToolResult.tool_call_id).filter(ToolCall.run_id == run_id).all()
        artifacts = db.query(Artifact).filter(Artifact.run_id == run_id).order_by(Artifact.created_at.asc()).all()
        approvals = db.query(ApprovalRequest).filter(ApprovalRequest.run_id == run_id).order_by(ApprovalRequest.created_at.asc()).all()
        return {
            'run': {
                'id': run.id,
                'kind': run.kind,
                'status': run.status,
                'output_text': run.output_text,
                'error_message': run.error_message,
                'failure_class': run.failure_class,
                'input_payload': run.input_payload,
                'conversation_id': run.conversation_id,
            },
            'events': [{'id': e.id, 'seq_no': e.seq_no, **e.payload, 'created_at': e.created_at.isoformat()} for e in events],
            'tool_calls': [{'id': t.id, 'tool_name': t.tool_name, 'args': t.args, 'status': t.status} for t in tools],
            'tool_results': [{'tool_call_id': r.tool_call_id, 'ok': r.ok, 'output': r.output, 'error_code': r.error_code, 'error_message': r.error_message} for r in results],
            'artifacts': [{'id': a.id, 'kind': a.kind, 'name': a.name, 'mime_type': a.mime_type, 'uri': a.uri, 'preview': a.preview, 'metadata': a.meta_json} for a in artifacts],
            'approvals': [{'id': a.id, 'status': a.status, 'decision': a.decision, 'title': a.title, 'reason': a.reason, 'args_preview': a.args_preview} for a in approvals],
        }


@router.post('/{run_id}/approve')
def approve_run(run_id: str, body: ApprovalBody, user=Depends(get_current_user)):
    require_run_for_user(run_id, user.user_id)
    try:
        row = approval_service.resolve(body.approval_id, body.decision, run_id=run_id)
        return {'ok': True, 'approval_id': row.id, 'decision': row.decision}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post('/{run_id}/cancel')
def cancel_run_route(run_id: str, user=Depends(get_current_user)):
    run = require_run_for_user(run_id, user.user_id)
    cancel_run(run_id)
    if run.status == 'queued':
        run_service.set_status(run_id, 'cancelled', failure_class='cancelled')
    return {'ok': True}


@router.get('/{run_id}/events')
async def stream_run_events(run_id: str, request: Request, user=Depends(get_current_user)):
    require_run_for_user(run_id, user.user_id)
    last_seq = int(request.query_params.get('last_event_id', '0') or 0)

    async def event_generator():
        for event in event_store.load_after(run_id, last_seq):
            yield format_sse_event(event)
        q = event_bus.subscribe(run_id)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15)
                    yield format_sse_event(event)
                except asyncio.TimeoutError:
                    yield sse_keepalive()
        finally:
            event_bus.unsubscribe(run_id, q)

    return StreamingResponse(event_generator(), media_type='text/event-stream')
