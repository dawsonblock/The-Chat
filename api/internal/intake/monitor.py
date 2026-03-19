from __future__ import annotations

from fastapi import APIRouter, Depends

from api.internal.intake.deps import require_service_token


def register_routes(router: APIRouter) -> None:
    @router.post('/monitor')
    async def monitor_route(payload: dict, _auth: None = Depends(require_service_token)):
        return {'ok': True, 'message': 'Monitor scaffolding is present but not fully implemented yet.', 'payload': payload}
