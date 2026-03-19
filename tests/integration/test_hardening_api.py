from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from backend.config import settings
from backend.main import app


def _token(client: TestClient) -> str:
    r = client.post('/api/auth/login', json={'email': 'hardening@test.local'})
    assert r.status_code == 200
    return r.json()['token']


def test_post_api_runs_requires_auth():
    with TestClient(app) as client:
        r = client.post('/api/runs', json={'kind': 'chat', 'input': {'message': 'hi'}})
        assert r.status_code == 401


def test_post_api_runs_chat_creates_run():
    with TestClient(app) as client:
        tok = _token(client)
        r = client.post(
            '/api/runs',
            json={'kind': 'chat', 'input': {'message': 'hello from generic create'}},
            headers={'Authorization': f'Bearer {tok}'},
        )
        assert r.status_code == 200
        data = r.json()
        assert 'run_id' in data
        assert data['status'] == 'queued'


def test_post_api_runs_workflow_requires_version():
    with TestClient(app) as client:
        tok = _token(client)
        r = client.post(
            '/api/runs',
            json={'kind': 'workflow', 'input': {}},
            headers={'Authorization': f'Bearer {tok}'},
        )
        assert r.status_code == 400


def test_internal_intake_requires_service_token():
    with TestClient(app) as client:
        r = client.post('/internal/intake/extract', json={'url': 'https://example.com'})
        assert r.status_code == 401


def test_internal_intake_accepts_service_token():
    fake_doc = MagicMock()
    fake_doc.model_dump.return_value = {'url': 'https://example.com', 'text': ''}
    with patch('api.internal.intake.extract.extract_page', new_callable=AsyncMock) as m:
        m.return_value = fake_doc
        with TestClient(app) as client:
            r = client.post(
                '/internal/intake/extract',
                json={'url': 'https://example.com', 'render_js': False, 'include_html': False},
                headers={'X-Service-Token': settings.service_token},
            )
            assert r.status_code == 200
            assert r.json().get('ok') is True
