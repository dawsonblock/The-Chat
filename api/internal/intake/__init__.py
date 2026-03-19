from __future__ import annotations

from fastapi import APIRouter, Depends

from api.internal.intake import crawl, extract, monitor
from api.internal.intake.deps import require_service_token

router = APIRouter(
    prefix='/internal/intake',
    tags=['internal-intake'],
    dependencies=[Depends(require_service_token)],
)
extract.register_routes(router)
crawl.register_routes(router)
monitor.register_routes(router)

__all__ = ['router']
