from __future__ import annotations

import time

from storage.db import SessionLocal
from storage.models import ExtractedDocument, FetchLog

from intake.extract.fetch import SSRFBlocked, http_get_html
from intake.extract.parse import parse_html, sanitize_html_for_preview
from intake.normalize.document import NormalizedDocument, content_hash


async def extract_page(url: str, *, render_js: bool = False, include_html: bool = True) -> NormalizedDocument:
    start = time.perf_counter()
    mode = 'rendered' if render_js else 'http'
    status_code = None
    if render_js:
        raise NotImplementedError('render_js requires a browser runtime (v0.8+).')

    try:
        html, final_url, status_code = await http_get_html(url)
        parsed = parse_html(html, final_url)
        h = content_hash(parsed['text'])
        with SessionLocal() as db:
            existing = db.query(ExtractedDocument).filter(ExtractedDocument.content_hash == h).first()
            if existing:
                meta = dict(existing.meta_json or {})
                meta.setdefault('dedupe_of', existing.source_url)
                meta['requested_url'] = url
                prev_final = meta.get('final_url') or final_url
                doc = NormalizedDocument(
                    source_url=url,
                    final_url=prev_final,
                    title=existing.title,
                    text_content=existing.text_content,
                    html_content=existing.html_content if include_html else None,
                    links=list(existing.links or []),
                    metadata={**meta, 'status_code': status_code, 'fetch_mode': mode, 'deduplicated': True},
                    content_hash=h,
                )
                db.add(
                    FetchLog(
                        url=url,
                        status_code=status_code,
                        fetch_mode=mode,
                        render_js=render_js,
                        duration_ms=int((time.perf_counter() - start) * 1000),
                        success=True,
                    )
                )
                db.commit()
                return doc

        meta = {'status_code': status_code, 'fetch_mode': mode, 'final_url': final_url}
        preview_html = sanitize_html_for_preview(html) if include_html else None
        doc = NormalizedDocument(
            source_url=url,
            final_url=final_url,
            title=parsed['title'],
            text_content=parsed['text'],
            html_content=html if include_html else None,
            links=parsed['links'],
            metadata=meta,
            content_hash=h,
        )
        with SessionLocal() as db:
            db.add(
                FetchLog(
                    url=url,
                    status_code=status_code,
                    fetch_mode=mode,
                    render_js=render_js,
                    duration_ms=int((time.perf_counter() - start) * 1000),
                    success=True,
                )
            )
            db.add(
                ExtractedDocument(
                    source_url=url,
                    title=parsed['title'],
                    text_content=parsed['text'],
                    html_content=html if include_html else None,
                    meta_json=meta,
                    links=parsed['links'],
                    content_hash=h,
                )
            )
            db.commit()
        if preview_html and include_html:
            doc.metadata['sanitized_preview_html'] = preview_html
        return doc
    except SSRFBlocked as exc:
        with SessionLocal() as db:
            db.add(
                FetchLog(
                    url=url,
                    status_code=status_code,
                    fetch_mode=mode,
                    render_js=render_js,
                    duration_ms=int((time.perf_counter() - start) * 1000),
                    success=False,
                    error_message=str(exc),
                )
            )
            db.commit()
        raise
    except Exception as exc:
        with SessionLocal() as db:
            db.add(
                FetchLog(
                    url=url,
                    status_code=status_code,
                    fetch_mode=mode,
                    render_js=render_js,
                    duration_ms=int((time.perf_counter() - start) * 1000),
                    success=False,
                    error_message=str(exc),
                )
            )
            db.commit()
        raise
