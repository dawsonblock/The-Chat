from __future__ import annotations

from fastapi import APIRouter


def register_routes(router: APIRouter) -> None:
    @router.post('/monitor')
    async def monitor_route(payload: dict):
        return {'ok': True, 'message': 'Monitor scaffolding is present but not fully implemented yet.', 'payload': payload}
