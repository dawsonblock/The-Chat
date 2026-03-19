from __future__ import annotations

import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class LocalHeuristicProvider:
    async def generate(self, prompt: str, *, max_chars: int = 1200) -> str:
        text = re.sub(r'\s+', ' ', prompt).strip()
        if not text:
            return 'No content was available to summarize.'
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) == 1:
            words = text.split()
            return ' '.join(words[: min(len(words), 80)])
        picked = sentences[:3]
        summary = ' '.join(picked)
        return summary[:max_chars]


class OpenAICompatibleHttpProvider:
    """Call a local or remote OpenAI-compatible `/v1/chat/completions` API (Ollama, LM Studio, vLLM, etc.)."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 120.0,
        transport: Any = None,
    ) -> None:
        self._base = base_url.rstrip('/')
        self._model = model
        self._api_key = (api_key or '').strip() or None
        self._timeout = timeout
        self._transport = transport
        self._http: httpx.AsyncClient | None = None

    async def _post_completion(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        max_chars: int,
    ) -> str:
        try:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        except httpx.HTTPStatusError as e:
            detail = ''
            try:
                detail = e.response.text[:500]
            except Exception:
                detail = ''
            logger.warning('local_llm_http_error status=%s body=%s', e.response.status_code, detail)
            return f'Local model HTTP {e.response.status_code}. Is the model pulled and the URL correct?'
        except httpx.RequestError as e:
            logger.warning('local_llm_unreachable: %s', e)
            return f'Could not reach local LLM at {self._base}: {e!s}'

        try:
            choices = data.get('choices') or []
            if not choices:
                return 'Local model returned an empty response.'
            msg = choices[0].get('message') or {}
            content = msg.get('content')
            if content is None:
                return 'Local model returned no message content.'
            if not isinstance(content, str):
                content = str(content)
            return content[:max_chars] if max_chars else content
        except (TypeError, KeyError, IndexError) as e:
            logger.warning('local_llm_bad_json: %s data_keys=%s', e, list(data.keys()) if isinstance(data, dict) else type(data))
            return 'Local model returned an unexpected response shape.'

    async def generate(self, prompt: str, *, max_chars: int = 1200) -> str:
        text = prompt.strip()
        if not text:
            return 'No content was available to summarize.'
        url = f'{self._base}/chat/completions'
        headers: dict[str, str] = {'Content-Type': 'application/json'}
        if self._api_key:
            headers['Authorization'] = f'Bearer {self._api_key}'
        payload: dict[str, Any] = {
            'model': self._model,
            'messages': [{'role': 'user', 'content': text}],
            'stream': False,
        }
        if self._transport is not None:
            async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as client:
                return await self._post_completion(client, url, headers, payload, max_chars)
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=self._timeout)
        return await self._post_completion(self._http, url, headers, payload, max_chars)


def _build_provider() -> LocalHeuristicProvider | OpenAICompatibleHttpProvider:
    from backend.config import settings

    mode = (settings.llm_backend or 'heuristic').strip().lower()
    if mode in {'openai_compatible', 'local', 'ollama'}:
        return OpenAICompatibleHttpProvider(
            base_url=settings.local_llm_base_url,
            model=settings.local_llm_model,
            api_key=settings.local_llm_api_key or None,
            timeout=settings.local_llm_timeout_seconds,
        )
    return LocalHeuristicProvider()


provider: LocalHeuristicProvider | OpenAICompatibleHttpProvider = _build_provider()
