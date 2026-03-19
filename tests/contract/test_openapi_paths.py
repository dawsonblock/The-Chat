from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app


def test_openapi_includes_core_public_paths():
    with TestClient(app) as client:
        r = client.get('/openapi.json')
        assert r.status_code == 200
        paths = set(r.json().get('paths', {}))
    for required in ('/api/health', '/api/ready', '/api/runs', '/api/runs/chat', '/internal/intake/extract'):
        assert required in paths, f'missing {required}'
