from __future__ import annotations

from fastapi import APIRouter

from api.internal.intake import crawl, extract, monitor

router = APIRouter(prefix='/internal/intake', tags=['internal-intake'])
extract.register_routes(router)
crawl.register_routes(router)
monitor.register_routes(router)

__all__ = ['router']
