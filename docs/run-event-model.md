# Run and event model

## Run (`runs` table)

- **status:** `queued` → `running` | `waiting_approval` → terminal `succeeded` | `failed` | `cancelled`
- **Worker** claims `queued` rows (excluding `cancel_requested`).
- **failure_class** on terminal failure (e.g. `infra`, `user_error`, `timeout`, `cancelled`).
- **cancel_requested:** cooperative cancel checked during chat/workflow execution.

## Events (`run_events`)

- Monotonic **seq_no** per `run_id`.
- **event_type** duplicates `payload.type` for querying.
- **SSE:** clients pass `last_event_id` (seq) to replay from persistence, then subscribe to live bus.

## Tool calls / results

- **ToolDispatcher** records `ToolCall` + `ToolResult`; failures carry **failure_class** / **retryable**.
- **Idempotency:** same run + tool + args hash reuses a prior **successful** result.
