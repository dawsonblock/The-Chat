from __future__ import annotations

import asyncio
import hashlib
import json
import time
from datetime import datetime
from uuid import uuid4

from core.approvals.service import approval_service
from core.events.emitter import emit
from core.events.schema import build_event
from core.files.service import file_service
from core.runtime.service import run_service
from core.tools.base import ToolContext, ToolExecutionResult
from core.tools.failure_classify import classify_tool_failure
from core.tools.permissions.checks import tool_requires_approval
from core.tools.policy import effective_tool_policy
from core.tools.registry import registry
from storage.db import SessionLocal
from storage.models import ApprovalRequest, ToolCall, ToolResult


class ToolDispatcher:
    async def run_tool(self, *, run_id: str, user_id: str, conversation_id: str | None, name: str, args: dict) -> ToolExecutionResult:
        tool = registry.get(name)
        policy = effective_tool_policy(name, tool)
        idempotency_key = hashlib.sha256(json.dumps({'tool': name, 'args': args}, sort_keys=True, default=str).encode()).hexdigest()[:48]

        with SessionLocal() as db:
            existing = (
                db.query(ToolCall, ToolResult)
                .join(ToolResult, ToolResult.tool_call_id == ToolCall.id)
                .filter(
                    ToolCall.run_id == run_id,
                    ToolCall.tool_name == name,
                    ToolCall.idempotency_key == idempotency_key,
                    ToolResult.ok == True,  # noqa: E712
                )
                .first()
            )
            if existing:
                call, res = existing
                return ToolExecutionResult(ok=True, output=res.output or {}, artifacts=[])

        tool_call_id = str(uuid4())
        with SessionLocal() as db:
            db.add(
                ToolCall(
                    id=tool_call_id,
                    run_id=run_id,
                    tool_name=name,
                    args=args,
                    status='running',
                    started_at=datetime.utcnow(),
                    idempotency_key=idempotency_key,
                )
            )
            db.commit()
        await emit(run_id, build_event('tool.started', runId=run_id, tool={'id': tool_call_id, 'toolName': name, 'args': args, 'status': 'running'}))

        verr = tool.validate_args(args)
        if verr:
            fc, retryable = classify_tool_failure('validation_error')
            result = ToolExecutionResult(
                ok=False,
                error_code='validation_error',
                error_message=verr,
                failure_class=fc,
                retryable=retryable,
            )
            with SessionLocal() as db:
                row = db.query(ToolCall).filter(ToolCall.id == tool_call_id).first()
                row.status = 'failed'
                row.finished_at = datetime.utcnow()
                db.merge(
                    ToolResult(
                        tool_call_id=tool_call_id,
                        ok=False,
                        error_code=result.error_code,
                        error_message=result.error_message,
                        failure_class=fc,
                        retryable=retryable,
                    )
                )
                db.commit()
            await emit(
                run_id,
                build_event(
                    'tool.finished',
                    runId=run_id,
                    result={'toolCallId': tool_call_id, 'ok': False, 'error': {'code': result.error_code, 'message': result.error_message}, 'artifacts': []},
                ),
            )
            return result

        if tool_requires_approval(name):
            run_service.set_status(run_id, 'waiting_approval')
            await run_service.emit_status(run_id, 'waiting_approval')
            with SessionLocal() as db:
                approval = ApprovalRequest(
                    run_id=run_id,
                    tool_call_id=tool_call_id,
                    title=f'Approve {name}',
                    reason=f'The tool {name} is gated by policy.',
                    risk=policy['risk'],
                    args_preview=args,
                )
                db.add(approval)
                db.commit()
                db.refresh(approval)
            await emit(
                run_id,
                build_event(
                    'approval.requested',
                    runId=run_id,
                    approval={
                        'id': approval.id,
                        'runId': run_id,
                        'toolCallId': tool_call_id,
                        'title': approval.title,
                        'reason': approval.reason,
                        'risk': approval.risk,
                        'argsPreview': approval.args_preview,
                    },
                ),
            )
            decision = await approval_service.wait_for_decision(approval.id)
            run_service.set_status(run_id, 'running')
            await run_service.emit_status(run_id, 'running')
            if decision != 'approve':
                fc, retryable = classify_tool_failure('approval_denied')
                result = ToolExecutionResult(ok=False, error_code='approval_denied', error_message='Approval denied for guarded tool.', failure_class=fc, retryable=retryable)
                with SessionLocal() as db:
                    row = db.query(ToolCall).filter(ToolCall.id == tool_call_id).first()
                    row.status = 'failed'
                    row.finished_at = datetime.utcnow()
                    db.merge(
                        ToolResult(
                            tool_call_id=tool_call_id,
                            ok=False,
                            error_code=result.error_code,
                            error_message=result.error_message,
                            failure_class=fc,
                            retryable=retryable,
                        )
                    )
                    db.commit()
                await emit(
                    run_id,
                    build_event('tool.finished', runId=run_id, result={'toolCallId': tool_call_id, 'ok': False, 'error': {'code': result.error_code, 'message': result.error_message}, 'artifacts': []}),
                )
                return result

        max_retries = int(policy['max_retries'] or 0)
        delay = float(policy['retry_delay_seconds'] or 0.5)
        wall0 = time.monotonic()
        last_result: ToolExecutionResult | None = None
        for attempt in range(max_retries + 1):
            with SessionLocal() as db:
                row = db.query(ToolCall).filter(ToolCall.id == tool_call_id).first()
                if row:
                    row.attempt_count = attempt + 1
                    db.commit()
            ctx = ToolContext(run_id=run_id, user_id=user_id, conversation_id=conversation_id)
            timeout_s = float(getattr(tool, 'timeout_seconds', 180) or 180)
            try:
                last_result = await asyncio.wait_for(tool.run(ctx, args), timeout=timeout_s)
            except asyncio.TimeoutError:
                fc, retryable = classify_tool_failure('timeout')
                last_result = ToolExecutionResult(
                    ok=False,
                    error_code='timeout',
                    error_message=f'Tool exceeded {timeout_s:.0f}s timeout.',
                    failure_class=fc,
                    retryable=retryable,
                )
            except Exception as exc:
                fc, retryable = classify_tool_failure(None, exc)
                last_result = ToolExecutionResult(ok=False, error_code='tool_exception', error_message=str(exc), failure_class=fc, retryable=retryable)
            if last_result.ok:
                break
            if attempt < max_retries and last_result.retryable:
                await asyncio.sleep(delay * (2**attempt))
                continue
            break

        assert last_result is not None
        result = last_result
        if not result.failure_class:
            fc, retryable = classify_tool_failure(result.error_code)
            result.failure_class = fc
            result.retryable = retryable if result.retryable is None else result.retryable

        artifact_refs = []
        if result.ok:
            for artifact in result.artifacts:
                saved = file_service.create_artifact(
                    run_id=run_id,
                    tool_call_id=tool_call_id,
                    kind=artifact['kind'],
                    name=artifact['name'],
                    mime_type=artifact['mime_type'],
                    content=artifact['content'],
                    metadata=artifact.get('metadata', {}),
                )
                artifact_refs.append({k: saved[k] for k in ['id', 'kind', 'name', 'mime_type', 'uri', 'preview', 'metadata']})
                await emit(run_id, build_event('artifact.created', runId=run_id, artifact={k: saved[k] for k in ['id', 'kind', 'name', 'mime_type', 'uri', 'preview', 'metadata']}))

        with SessionLocal() as db:
            row = db.query(ToolCall).filter(ToolCall.id == tool_call_id).first()
            row.status = 'succeeded' if result.ok else 'failed'
            row.finished_at = datetime.utcnow()
            db.merge(
                ToolResult(
                    tool_call_id=tool_call_id,
                    ok=result.ok,
                    output=result.output if result.ok else None,
                    error_code=result.error_code,
                    error_message=result.error_message,
                    failure_class=result.failure_class,
                    retryable=result.retryable,
                )
            )
            db.commit()

        payload = {
            'toolCallId': tool_call_id,
            'ok': result.ok,
            'output': result.output if result.ok else None,
            'error': None if result.ok else {'code': result.error_code, 'message': result.error_message},
            'artifacts': artifact_refs,
            'durationMs': int((time.monotonic() - wall0) * 1000),
        }
        await emit(run_id, build_event('tool.finished', runId=run_id, result=payload))
        result.artifacts = artifact_refs
        return result


dispatcher = ToolDispatcher()
