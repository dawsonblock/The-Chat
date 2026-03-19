# Schema collapse plan (`tool_calls` / `tool_results` → `run_events`)

## Canonical read order (today)

When building a run timeline for the UI, treat sources in this order:

1. **`run_events`** — primary SSE / audit stream (`seq_no` order). Tool lifecycle is already duplicated here when code uses [`emit()`](../core/events/emitter.py).
2. **`tool_calls` + `tool_results`** — structured rows for idempotency, retries, and DB joins to `approval_requests` / `artifacts`.
3. **Bundle API** — [`GET /api/runs/{id}/bundle`](../api/public/runs.py) returns all three for hydration.

## Migration strategy (incremental)

1. **Stop writing redundant projections** — prefer `emit()` for every user-visible tool/approval/artifact signal (dispatcher done).
2. **Backfill (optional, manual)** — For historical rows where `tool_calls` exist but no matching `tool.started` / `tool.finished` events exist, insert synthetic `RunEvent` rows. This requires JSON payload shape parity with [`build_event`](../core/events/schema.py); run only after backup.
3. **Deprecate tables** — After reads move to events-only and a release window passes, drop `tool_calls` / `tool_results` or keep them as implementation indexes only (not exposed to API).

## SQLite sketch (do not run blindly)

```sql
-- Example: detect tool_calls without a persisted tool.started (pseudo; adjust JSON ops for SQLite)
SELECT tc.id, tc.run_id FROM tool_calls tc
WHERE NOT EXISTS (
  SELECT 1 FROM run_events re
  WHERE re.run_id = tc.run_id AND re.event_type = 'tool.started'
  AND json_extract(re.payload, '$.tool.id') = tc.id
);
```

Run idempotent backfill (after backup):

```bash
BACKFILL_RUN_EVENTS=1 ./scripts/migrate.sh
# or: python -c "from storage.migrate import backfill_run_events_from_tool_calls; print(backfill_run_events_from_tool_calls())"
```

Implementation: [`backfill_run_events_from_tool_calls`](../storage/migrate.py).

## Postgres

Prefer `JSONB` + `GIN` indexes on `run_events.payload` before dropping relational tool tables.
