from __future__ import annotations

import json
import time
import uuid
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.config import settings
from core.runtime.provider import provider

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
