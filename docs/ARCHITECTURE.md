# Operator One architecture (code-truth summary)

## Single authorities

| Concern | Authority |
|---------|-----------|
| Runs | `storage.models.runtime.Run`, claimed by `core.runtime.worker` |
| Events | `RunEvent` + `core.events.store` / `core.events.bus` |
| Tool execution | `core.tools.dispatcher.ToolDispatcher` |
| Workflow shape | `core/workflows/spec.py` (`WorkflowSpec` JSON) |
| Workflow execution | `core.runtime.execution.workflow_run.execute_workflow_run` |
| Artifacts | `core.files.service` + `Artifact` rows; served under `/api/files/*` |
| Tool policy | `storage.models.tool_policy.ToolPolicy` + `core.tools.policy.effective_tool_policy` |
| Intake document | `intake.normalize.NormalizedDocument` |

## Request flow (chat)

1. `POST /api/runs/chat` creates a `queued` run.
2. `runtime_worker_loop` claims the run and calls `execute_chat_run`.
3. Tools run through the dispatcher (retries, idempotency on success, approvals).
4. SSE clients reconnect with `last_event_id` for replay from `RunEvent.seq_no`.

## v0.8+ absorption

See `docs/import-audit/*.md` and `docs/v08-PASSES.md`. Imported upstream code must not introduce a second run, event, workflow, artifact, or auth model.

## Operations

- Bootstrap DB: `scripts/migrate.sh` or app startup `init_db()`.
- Logs: set `JSON_LOGS=true` for JSON lines on stdout (`core.observability`).

## More docs

- [Run / event model](run-event-model.md)
- [WorkflowSpec](workflow-spec.md)
- [Tool authoring](tool-authoring.md)
- [Intake security](intake-security.md)
- [Operator guide](operator.md)
- [Import map](IMPORT_MAP.md)
