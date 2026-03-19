from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app


def test_health_and_ready():
    with TestClient(app) as client:
        h = client.get('/api/health')
        assert h.status_code == 200
        assert h.json().get('ok') is True
        r = client.get('/api/ready')
        assert r.status_code == 200
        assert r.json().get('ready') is True
