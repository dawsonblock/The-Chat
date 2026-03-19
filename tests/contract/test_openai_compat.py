from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app


def test_v1_models_requires_key():
    with TestClient(app) as client:
        r = client.get('/v1/models')
        assert r.status_code == 401


def test_v1_models_with_key():
    with TestClient(app) as client:
        r = client.get('/v1/models', headers={'Authorization': 'Bearer dev-openai-proxy-key'})
        assert r.status_code == 200
        data = r.json()
        assert data.get('object') == 'list'
        assert len(data.get('data', [])) >= 1
        assert data['data'][0]['id'] == 'operator-local'


def test_v1_chat_completions():
    with TestClient(app) as client:
        r = client.post(
            '/v1/chat/completions',
            headers={'Authorization': 'Bearer dev-openai-proxy-key'},
            json={
                'model': 'operator-local',
                'messages': [{'role': 'user', 'content': 'Hello world. This is a test.'}],
                'stream': False,
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get('object') == 'chat.completion'
        choice = body['choices'][0]
        assert choice['message']['role'] == 'assistant'
        assert isinstance(choice['message']['content'], str)
        assert len(choice['message']['content']) > 0
