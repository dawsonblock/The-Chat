from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.config import settings
from backend.main import app


def test_v1_stream_synthetic_run_emits_done():
    with patch.object(settings, 'openwebui_synthetic_runs', True):
        with TestClient(app) as client:
            with client.stream(
                'POST',
                '/v1/chat/completions',
                headers={'Authorization': f'Bearer {settings.openai_proxy_api_key}'},
                json={'model': 'operator-local', 'messages': [{'role': 'user', 'content': 'Say hello in one word.'}], 'stream': True},
            ) as response:
                assert response.status_code == 200
                body = ''.join(response.iter_text())
                assert '[DONE]' in body
                assert 'chat.completion.chunk' in body
