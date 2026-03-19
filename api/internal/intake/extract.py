from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.internal.intake.deps import require_service_token
from intake.extract import extract_page


class ExtractBody(BaseModel):
    url: str
    render_js: bool = False
    include_html: bool = True


def register_routes(router: APIRouter) -> None:
    @router.post('/extract')
    async def extract_route(body: ExtractBody, _auth: None = Depends(require_service_token)):
        doc = await extract_page(body.url, render_js=body.render_js, include_html=body.include_html)
        return {'ok': True, 'document': doc.model_dump()}
