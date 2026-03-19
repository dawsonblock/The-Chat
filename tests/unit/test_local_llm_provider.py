from __future__ import annotations

import asyncio

import httpx

from core.runtime.provider import OpenAICompatibleHttpProvider


def test_openai_compatible_parses_assistant_message():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).endswith('/chat/completions')
        return httpx.Response(
            200,
            json={'choices': [{'message': {'role': 'assistant', 'content': 'Summarized.'}}]},
        )

    p = OpenAICompatibleHttpProvider(
        base_url='http://example.test/v1',
        model='m',
        transport=httpx.MockTransport(handler),
    )
    out = asyncio.run(p.generate('hello'))
    assert out == 'Summarized.'


def test_openai_compatible_http_error_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text='boom')

    p = OpenAICompatibleHttpProvider(
        base_url='http://example.test/v1',
        model='m',
        transport=httpx.MockTransport(handler),
    )
    out = asyncio.run(p.generate('hello'))
    assert 'HTTP 500' in out
