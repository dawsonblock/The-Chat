from __future__ import annotations

from fastapi import Header, HTTPException

from backend.config import settings


async def require_service_token(x_service_token: str | None = Header(default=None)) -> None:
    if x_service_token != settings.service_token:
        raise HTTPException(status_code=401, detail='Invalid service token')
