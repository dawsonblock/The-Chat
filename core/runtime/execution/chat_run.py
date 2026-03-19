from __future__ import annotations

import re
from pathlib import Path

from core.events.bus import event_bus
from core.events.schema import build_event
from core.runtime.cancellation.service import cancellation_service
from core.runtime.provider import provider
from core.runtime.service import run_service
from core.tools.dispatcher import dispatcher
from storage.db import SessionLocal
from storage.models import UploadedFile

URL_RE = re.compile(r'https?://\S+')


def cancel_run(run_id: str) -> None:
    run_service.request_cancel(run_id)


def is_cancelled(run_id: str) -> bool:
    return cancellation_service.is_cancelled(run_id)


def _load_attachment_text(user_id: str, attachment_ids: list[str]) -> str:
    if not attachment_ids:
        return ''
    collected: list[str] = []
    with SessionLocal() as db:
        rows = db.query(UploadedFile).filter(UploadedFile.user_id == user_id, UploadedFile.id.in_(attachment_ids)).all()
        for row in rows:
            mime = (row.mime_type or '').lower()
            suffix = Path(row.original_name).suffix.lower()
            if mime.startswith('text/') or suffix in {'.txt', '.md', '.csv', '.json', '.html', '.htm'}:
                try:
                    content = Path(row.storage_path).read_text(encoding='utf-8', errors='ignore')
                    if content.strip():
                        collected.append(f"# File: {row.original_name}\n{content[:20000]}")
                except OSError:
                    continue
    return '\n\n'.join(collected)


async def execute_chat_run(run_id: str, payload: dict, *, user_id: str, conversation_id: str | None):
    try:
        await run_service.emit_created_if_needed(run_id)
        await run_service.emit_status(run_id, 'running')

        message = (payload.get('message') or '').strip()
        attachment_ids = payload.get('attachments') or []
        attachment_text = _load_attachment_text(user_id, attachment_ids)
        urls = URL_RE.findall(message)
        final_text = ''

        if urls and 'crawl' in message.lower():
            crawl_result = await dispatcher.run_tool(run_id=run_id, user_id=user_id, conversation_id=conversation_id, name='crawl_site', args={'url': urls[0], 'max_depth': 1, 'max_pages': 5})
            if is_cancelled(run_id):
                run_service.set_status(run_id, 'cancelled', failure_class='cancelled')
                await run_service.emit_status(run_id, 'cancelled')
                await event_bus.publish(run_id, build_event('run.failed', runId=run_id, error={'code': 'cancelled', 'message': 'Run cancelled.'}))
                return
            final_text = crawl_result.output.get('summary', '') if crawl_result.ok else (crawl_result.error_message or 'The crawl did not complete.')
        elif urls:
            extracted = await dispatcher.run_tool(run_id=run_id, user_id=user_id, conversation_id=conversation_id, name='extract_page', args={'url': urls[0], 'render_js': False})
            if is_cancelled(run_id):
                run_service.set_status(run_id, 'cancelled', failure_class='cancelled')
                await run_service.emit_status(run_id, 'cancelled')
                await event_bus.publish(run_id, build_event('run.failed', runId=run_id, error={'code': 'cancelled', 'message': 'Run cancelled.'}))
                return
            if extracted.ok:
                summary = await dispatcher.run_tool(run_id=run_id, user_id=user_id, conversation_id=conversation_id, name='summarize_text', args={'text': extracted.output.get('text_content', '')})
                title = extracted.output.get('title') or extracted.output.get('source_url')
                final_text = f"Summary for {title}: {summary.output.get('summary', '')}" if summary.ok else f"Extracted {title}, but the summary step failed."
            else:
                final_text = extracted.error_message or 'Extraction failed.'
        elif attachment_text:
            source_text = f"User prompt:\n{message}\n\nAttached files:\n{attachment_text}" if message else attachment_text
            summary = await dispatcher.run_tool(run_id=run_id, user_id=user_id, conversation_id=conversation_id, name='summarize_text', args={'text': source_text})
            if is_cancelled(run_id):
                run_service.set_status(run_id, 'cancelled', failure_class='cancelled')
                await run_service.emit_status(run_id, 'cancelled')
                await event_bus.publish(run_id, build_event('run.failed', runId=run_id, error={'code': 'cancelled', 'message': 'Run cancelled.'}))
                return
            final_text = summary.output.get('summary', '') if summary.ok else await provider.generate(source_text)
        else:
            summary = await dispatcher.run_tool(run_id=run_id, user_id=user_id, conversation_id=conversation_id, name='summarize_text', args={'text': message})
            if is_cancelled(run_id):
                run_service.set_status(run_id, 'cancelled', failure_class='cancelled')
                await run_service.emit_status(run_id, 'cancelled')
                await event_bus.publish(run_id, build_event('run.failed', runId=run_id, error={'code': 'cancelled', 'message': 'Run cancelled.'}))
                return
            final_text = summary.output.get('summary', '') if summary.ok else await provider.generate(message)

        if is_cancelled(run_id):
            run_service.set_status(run_id, 'cancelled', failure_class='cancelled')
            await run_service.emit_status(run_id, 'cancelled')
            await event_bus.publish(run_id, build_event('run.failed', runId=run_id, error={'code': 'cancelled', 'message': 'Run cancelled.'}))
            return

        run_service.set_output(run_id, final_text)
        await run_service.emit_text(run_id, final_text)
        run_service.set_status(run_id, 'succeeded')
        await run_service.emit_status(run_id, 'succeeded')
        await event_bus.publish(run_id, build_event('run.completed', runId=run_id))
    except Exception as exc:
        run_service.fail_run(run_id, str(exc), failure_class='infra')
        await run_service.emit_status(run_id, 'failed')
        await event_bus.publish(run_id, build_event('run.failed', runId=run_id, error={'code': 'run_failed', 'message': str(exc)}))
