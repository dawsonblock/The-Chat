from __future__ import annotations

import logging

from core.events.bus import event_bus
from core.events.schema import build_event
from core.runtime.execution.chat_run import execute_chat_run
from core.runtime.execution.workflow_run import execute_workflow_run
from core.runtime.run_manager import get_run_for_execution
from core.runtime.service import run_service

log = logging.getLogger(__name__)


class RuntimeEngine:
    """Authoritative execution entry: worker and future queue workers call only this."""

    async def run(self, run_id: str) -> None:
        run = get_run_for_execution(run_id)
        if run is None:
            log.warning('runtime_engine_missing_run run_id=%s', run_id)
            return

        if run.kind == 'chat':
            await execute_chat_run(
                run.id,
                run.input_payload,
                user_id=run.user_id,
                conversation_id=run.conversation_id,
            )
            return

        if run.kind == 'workflow':
            payload = run.input_payload
            await execute_workflow_run(
                run.id,
                payload.get('workflow_version_id', ''),
                payload.get('inputs', {}),
                user_id=run.user_id,
            )
            return

        run_service.fail_run(run.id, f'Unknown run kind {run.kind}', failure_class='user_error')
        await run_service.emit_status(run.id, 'failed')
        await event_bus.publish(
            run.id,
            build_event('run.failed', runId=run.id, error={'code': 'unknown_kind', 'message': run.kind}),
        )
