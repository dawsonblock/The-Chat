from __future__ import annotations

import re

from core.events.emitter import emit
from core.events.schema import build_event
from core.runtime.cancellation.service import cancellation_service
from core.runtime.service import run_service
from core.tools.dispatcher import dispatcher
from storage.db import SessionLocal
from storage.models import WorkflowVersion

_PLACEHOLDER_RE = re.compile(r'^{{\s*(input|last)\.([\w_]+)\s*}}$')


def _resolve(value, inputs: dict, last: dict):
    if isinstance(value, str):
        m = _PLACEHOLDER_RE.match(value)
        if m:
            scope, key = m.groups()
            return inputs.get(key) if scope == 'input' else last.get(key)
    if isinstance(value, dict):
        return {k: _resolve(v, inputs, last) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(v, inputs, last) for v in value]
    return value


async def execute_workflow_run(run_id: str, workflow_version_id: str, inputs: dict, *, user_id: str):
    try:
        await run_service.emit_created_if_needed(run_id)
        await run_service.emit_status(run_id, 'running')
        with SessionLocal() as db:
            version = db.query(WorkflowVersion).filter(WorkflowVersion.id == workflow_version_id).first()
            spec = version.spec
        last_output = {}
        final_text = ''
        for node in spec.get('nodes', []):
            if cancellation_service.is_cancelled(run_id):
                run_service.set_status(run_id, 'cancelled', failure_class='cancelled')
                await run_service.emit_status(run_id, 'cancelled')
                await emit(run_id, build_event('run.failed', runId=run_id, error={'code': 'cancelled', 'message': 'Run cancelled.'}))
                return
            if node.get('kind') == 'tool':
                args = _resolve(node.get('config', {}), inputs, last_output)
                result = await dispatcher.run_tool(run_id=run_id, user_id=user_id, conversation_id=None, name=node.get('type'), args=args)
                if not result.ok:
                    raise RuntimeError(result.error_message or f"Node {node.get('id')} failed")
                last_output = result.output
                if 'summary' in last_output:
                    final_text = last_output['summary']
            elif node.get('kind') == 'output':
                template = node.get('config', {}).get('text', '')
                final_text = str(_resolve(template, inputs, last_output) or final_text)
        final_text = final_text or 'Workflow completed.'
        run_service.set_output(run_id, final_text)
        await run_service.emit_text(run_id, final_text)
        run_service.set_status(run_id, 'succeeded')
        await run_service.emit_status(run_id, 'succeeded')
        await emit(run_id, build_event('run.completed', runId=run_id))
    except Exception as exc:
        run_service.fail_run(run_id, str(exc), failure_class='infra')
        await run_service.emit_status(run_id, 'failed')
        await emit(run_id, build_event('run.failed', runId=run_id, error={'code': 'workflow_failed', 'message': str(exc)}))
