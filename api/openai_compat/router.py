from __future__ import annotations

"""OpenAI-compatible surface for external UIs (e.g. Open WebUI).

**Default (Option A):** calls ``provider.generate`` directly (no ``Run`` / ``run_events``).

**Optional (Option B):** set ``OPENWEBUI_SYNTHETIC_RUNS=true`` to create a **chat** run for each completion.
Non-stream waits for a terminal status; **stream** polls ``run_events`` for ``message.delta`` chunks, then
falls back to ``output_text`` if no deltas were emitted. Requires a running worker. See ``docs/baseline.md``.
"""

import asyncio
import json
import time
import uuid
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.config import settings
from core.events.store import event_store
from core.runtime.provider import provider
from core.runtime.service import run_service

router = APIRouter(prefix='/v1', tags=['openai-compat'])


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith('Bearer '):
        return None
    return authorization[7:].strip()


def _require_openai_key(authorization: str | None) -> None:
    token = _bearer_token(authorization)
    expected = (settings.openai_proxy_api_key or '').strip()
    if not expected:
        raise HTTPException(status_code=503, detail='OpenAI proxy is disabled (set OPENAI_PROXY_API_KEY).')
    if not token or token != expected:
        raise HTTPException(status_code=401, detail='Invalid or missing API key')


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra='ignore')

    role: str
    content: str | list[Any] | None = None


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra='ignore')

    model: str = 'operator-local'
    messages: list[ChatMessage] = Field(default_factory=list)
    stream: bool = False
    max_tokens: int | None = None


def _flatten_message_content(content: str | list[Any] | None) -> str:
    if content is None:
        return ''
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get('type') == 'text':
            parts.append(str(block.get('text', '')))
        elif isinstance(block, str):
            parts.append(block)
    return '\n'.join(parts)


async def _wait_run_terminal(run_id: str):
    deadline = time.monotonic() + float(settings.run_timeout_seconds) + 60.0
    while time.monotonic() < deadline:
        row = run_service.get_run(run_id)
        if row and row.status in {'succeeded', 'failed', 'cancelled'}:
            return row
        await asyncio.sleep(0.2)
    return run_service.get_run(run_id)


def _chunk_lines(body: ChatCompletionRequest, cid: str, *, created: int):
    def chunk_base():
        return {'id': cid, 'object': 'chat.completion.chunk', 'created': created, 'model': body.model}

    return chunk_base


async def _synthetic_stream_events(body: ChatCompletionRequest, prompt: str):
    """Stream OpenAI-style chunks by polling persisted run events (message.delta)."""
    run = run_service.create_run(
        user_id=settings.openwebui_run_user_id,
        conversation_id=None,
        kind='chat',
        input_payload={'message': prompt, 'attachments': []},
    )
    run_id = run.id
    last_seq = 0
    cid = f'chatcmpl-{uuid.uuid4().hex[:12]}'
    created = int(time.time())
    chunk_base = _chunk_lines(body, cid, created=created)

    yield f'data: {json.dumps({**chunk_base(), "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]})}\n\n'

    deadline = time.monotonic() + float(settings.run_timeout_seconds) + 60.0
    streamed_any = False
    while time.monotonic() < deadline:
        events = event_store.load_after(run_id, last_seq)
        for ev in events:
            seq = ev.get('seq_no') or 0
            last_seq = max(last_seq, seq)
            if ev.get('type') == 'message.delta' and ev.get('text'):
                streamed_any = True
                piece = ev['text']
                yield f'data: {json.dumps({**chunk_base(), "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}]})}\n\n'

        row = run_service.get_run(run_id)
        if row and row.status in {'succeeded', 'failed', 'cancelled'}:
            events = event_store.load_after(run_id, last_seq)
            for ev in events:
                seq = ev.get('seq_no') or 0
                last_seq = max(last_seq, seq)
                if ev.get('type') == 'message.delta' and ev.get('text'):
                    streamed_any = True
                    piece = ev['text']
                    yield f'data: {json.dumps({**chunk_base(), "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}]})}\n\n'

            if not streamed_any:
                if row.status == 'succeeded':
                    text = (row.output_text or '').strip() or '(empty response)'
                else:
                    text = (row.error_message or 'Run failed.').strip()
                stream_chunk_chars = 80
                for i in range(0, len(text), stream_chunk_chars):
                    piece = text[i : i + stream_chunk_chars]
                    yield f'data: {json.dumps({**chunk_base(), "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}]})}\n\n'

            yield f'data: {json.dumps({**chunk_base(), "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})}\n\n'
            yield 'data: [DONE]\n\n'
            return

        await asyncio.sleep(0.12)

    yield f'data: {json.dumps({**chunk_base(), "choices": [{"index": 0, "delta": {"content": "Run timed out waiting for completion."}, "finish_reason": None}]})}\n\n'
    yield f'data: {json.dumps({**chunk_base(), "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})}\n\n'
    yield 'data: [DONE]\n\n'


def _prompt_from_messages(messages: list[ChatMessage]) -> str:
    lines: list[str] = []
    for m in messages:
        body = _flatten_message_content(m.content).strip()
        if body:
            lines.append(f'{m.role.upper()}: {body}')
    return '\n\n'.join(lines) if lines else ''


@router.get('/models')
def list_models(authorization: str | None = Header(default=None, alias='Authorization')):
    _require_openai_key(authorization)
    now = int(time.time())
    return {
        'object': 'list',
        'data': [
            {
                'id': 'operator-local',
                'object': 'model',
                'created': now,
                'owned_by': 'operator-one',
            }
        ],
    }


@router.post('/chat/completions')
async def chat_completions(
    body: ChatCompletionRequest,
    authorization: str | None = Header(default=None, alias='Authorization'),
):
    _require_openai_key(authorization)
    prompt = _prompt_from_messages(body.messages)
    if not prompt:
        raise HTTPException(status_code=400, detail='No message content provided.')

    if settings.openwebui_synthetic_runs and body.stream:
        return StreamingResponse(_synthetic_stream_events(body, prompt), media_type='text/event-stream')

    reply: str
    if settings.openwebui_synthetic_runs and not body.stream:
        run = run_service.create_run(
            user_id=settings.openwebui_run_user_id,
            conversation_id=None,
            kind='chat',
            input_payload={'message': prompt, 'attachments': []},
        )
        final = await _wait_run_terminal(run.id)
        if not final or final.status != 'succeeded':
            reply = (final.error_message if final else 'Run did not complete.') or 'Run failed.'
        else:
            reply = (final.output_text or '').strip() or '(empty response)'
    else:
        reply = await provider.generate(prompt)

    if body.stream:
        cid = f'chatcmpl-{uuid.uuid4().hex[:12]}'
        stream_chunk_chars = 80

        async def event_stream():
            created = int(time.time())

            def chunk_base():
                return {'id': cid, 'object': 'chat.completion.chunk', 'created': created, 'model': body.model}

            yield f'data: {json.dumps({**chunk_base(), "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]})}\n\n'
            for i in range(0, len(reply), stream_chunk_chars):
                piece = reply[i : i + stream_chunk_chars]
                yield f'data: {json.dumps({**chunk_base(), "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}]})}\n\n'
            yield f'data: {json.dumps({**chunk_base(), "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})}\n\n'
            yield 'data: [DONE]\n\n'

        return StreamingResponse(event_stream(), media_type='text/event-stream')

    return JSONResponse(
        {
            'id': f'chatcmpl-{uuid.uuid4().hex[:12]}',
            'object': 'chat.completion',
            'created': int(time.time()),
            'model': body.model,
            'choices': [
                {
                    'index': 0,
                    'message': {'role': 'assistant', 'content': reply},
                    'finish_reason': 'stop',
                }
            ],
            'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0},
        }
    )


@router.post('/embeddings')
def embeddings_not_supported(authorization: str | None = Header(default=None, alias='Authorization')):
    _require_openai_key(authorization)
    raise HTTPException(status_code=501, detail='Embeddings are not implemented; disable embedding-dependent features in Open WebUI or use an external embedding API.')
