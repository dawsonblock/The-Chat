from __future__ import annotations

from collections import deque
from datetime import datetime
from urllib.parse import urlparse

from storage.db import SessionLocal
from storage.models import CrawlJob, CrawlPage, ExtractedDocument
from intake.extract import extract_page


async def crawl_site(start_url: str, *, max_depth: int = 1, max_pages: int = 5) -> dict:
    with SessionLocal() as db:
        job = CrawlJob(start_url=start_url, status='running', max_depth=max_depth, max_pages=max_pages, started_at=datetime.utcnow())
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id

    parsed = urlparse(start_url)
    origin = f'{parsed.scheme}://{parsed.netloc}'
    frontier = deque([(start_url, 0)])
    seen = {start_url}
    fetched = []
    failures = []

    while frontier and len(fetched) < max_pages:
        url, depth = frontier.popleft()
        try:
            doc = await extract_page(url, render_js=False, include_html=False)
            page = {
                'url': url,
                'depth': depth,
                'title': doc.title,
                'link_count': len(doc.links),
                'text_preview': doc.text_content[:300],
                'content_hash': doc.content_hash,
            }
            fetched.append(page)
            with SessionLocal() as db:
                stored_doc = db.query(ExtractedDocument).filter(ExtractedDocument.content_hash == doc.content_hash).first()
                db.add(CrawlPage(
                    crawl_job_id=job_id,
                    url=url,
                    depth=depth,
                    status='fetched',
                    title=doc.title,
                    link_count=len(doc.links),
                    text_preview=doc.text_content[:300],
                    document_id=stored_doc.id if stored_doc else None,
                ))
                db.commit()
            if depth < max_depth:
                for link in doc.links:
                    if link.startswith(origin) and link not in seen and len(seen) < max_pages * 8:
                        seen.add(link)
                        frontier.append((link, depth + 1))
        except Exception as exc:
            failures.append({'url': url, 'depth': depth, 'error': str(exc)})
            with SessionLocal() as db:
                db.add(CrawlPage(
                    crawl_job_id=job_id,
                    url=url,
                    depth=depth,
                    status='failed',
                    title=None,
                    link_count=0,
                    text_preview=str(exc)[:300],
                    document_id=None,
                ))
                db.commit()

    summary = f"Crawled {len(fetched)} page(s) from {start_url}."
    result = {'job_id': job_id, 'pages_fetched': len(fetched), 'pages': fetched, 'failures': failures, 'summary': summary}
    with SessionLocal() as db:
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        job.status = 'succeeded' if not failures else 'partial_success'
        job.pages_fetched = len(fetched)
        job.summary = summary
        job.result_json = result
        job.finished_at = datetime.utcnow()
        db.commit()

    return result


def list_crawl_jobs(limit: int = 50) -> list[dict]:
    with SessionLocal() as db:
        rows = db.query(CrawlJob).order_by(CrawlJob.created_at.desc()).limit(limit).all()
        return [
            {
                'id': row.id,
                'start_url': row.start_url,
                'status': row.status,
                'max_depth': row.max_depth,
                'max_pages': row.max_pages,
                'pages_fetched': row.pages_fetched,
                'summary': row.summary,
                'created_at': row.created_at.isoformat(),
                'finished_at': row.finished_at.isoformat() if row.finished_at else None,
            }
            for row in rows
        ]


def get_crawl_job(job_id: str) -> dict | None:
    with SessionLocal() as db:
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not job:
            return None
        pages = db.query(CrawlPage).filter(CrawlPage.crawl_job_id == job_id).order_by(CrawlPage.depth.asc(), CrawlPage.created_at.asc()).all()
        return {
            'id': job.id,
            'start_url': job.start_url,
            'status': job.status,
            'max_depth': job.max_depth,
            'max_pages': job.max_pages,
            'pages_fetched': job.pages_fetched,
            'summary': job.summary,
            'result': job.result_json,
            'created_at': job.created_at.isoformat(),
            'finished_at': job.finished_at.isoformat() if job.finished_at else None,
            'pages': [
                {
                    'id': page.id,
                    'url': page.url,
                    'depth': page.depth,
                    'status': page.status,
                    'title': page.title,
                    'link_count': page.link_count,
                    'text_preview': page.text_preview,
                    'document_id': page.document_id,
                }
                for page in pages
            ],
        }
