from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.internal.intake.deps import require_service_token
from intake.crawl import crawl_site, get_crawl_job


class CrawlBody(BaseModel):
    start_url: str
    max_depth: int = 1
    max_pages: int = 5


def register_routes(router: APIRouter) -> None:
    @router.post('/crawl')
    async def crawl_route(body: CrawlBody, _auth: None = Depends(require_service_token)):
        result = await crawl_site(body.start_url, max_depth=body.max_depth, max_pages=body.max_pages)
        return {'ok': True, **result}

    @router.get('/crawl/{job_id}')
    async def crawl_job_detail(job_id: str, _auth: None = Depends(require_service_token)):
        result = get_crawl_job(job_id)
        if not result:
            raise HTTPException(status_code=404, detail='Crawl job not found')
        return {'ok': True, 'job': result}
