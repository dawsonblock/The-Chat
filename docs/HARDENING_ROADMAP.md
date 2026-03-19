# Operator One — single runtime hardening roadmap

This maps the **non-negotiable target** (one loop: input → run → runtime → events → persist → stream → UI → approval → completion) to **this repository** and tracks phases 0–16 from the product spec.

**Baseline inventory:** [`docs/baseline.md`](baseline.md)  
**Branch for work:** `operator-one-hardening`

---

## Honest current state (vs spec)

| Spec expectation | This repo today |
|------------------|-----------------|
| Single `RuntimeEngine.run(run_id)` | **Yes:** [`core/runtime/engine.py`](../core/runtime/engine.py); worker calls only `RuntimeEngine().run` ([`worker.py`](../core/runtime/worker.py)). **Contract:** [`tests/contract/test_api_no_direct_execution.py`](../tests/contract/test_api_no_direct_execution.py). |
| `emit()` → persist + stream only | **`core/events/emitter.py`** `emit()` → `event_bus.publish` (which persists). Runtime (`service`, `execution/*`, `engine`, `worker`), dispatcher, and tools use `emit`; HTTP may `subscribe` on `event_bus` only. |
| POST `/api/runs` only entry | **`POST /api/runs`** generic create + **`POST /api/runs/chat`** alias; workflow POST; **`/v1/*`** documented compatibility bypass (Open WebUI). |
| No tool execution from API routes | Internal intake **gated** by `X-Service-Token`; OpenAI compat still calls `provider` (bypass — see baseline). |
| Redis + RQ worker | **In-process** worker optional; **`python -m worker`** for external process when `WORKER_IN_PROCESS=false`. |
| Events only in `run_events` | **`tool_calls`**, **`tool_results`**, **`approval_requests`** plus `run_events` — collapse plan in [`docs/schema-collapse.md`](schema-collapse.md). |
| Postgres JSONB | SQLite default; JSON columns portable to Postgres |

---

## Phase checklist

- [x] **Phase 0 — Freeze baseline** — `docs/baseline.md`, branch `operator-one-hardening`
- [x] **Phase 1 (v0.7)** — Worker → `RuntimeEngine.run` only; **contract** [`test_api_no_direct_execution.py`](../tests/contract/test_api_no_direct_execution.py). **`executor`** exports only `RuntimeEngine`, `cancel_run`, `is_cancelled`. **Optional:** `OPENWEBUI_SYNTHETIC_RUNS` for non-stream `/v1` (see baseline).
- [ ] **Phase 2 — Unify run model** — **Backfill** [`backfill_run_events_from_tool_calls()`](../storage/migrate.py) + docs; full table drop still future
- [x] **Phase 3 (initial)** — `emit()` for runtime + dispatcher; [`test_runtime_uses_emit.py`](../tests/contract/test_runtime_uses_emit.py); typed `RunEvent` union still future
- [x] **Phase 4 (initial)** — `validate_args` + per-tool `timeout_seconds` + `asyncio.wait_for` in dispatcher; intake still only under `intake/` tools
- [x] **Phase 5 (runtime path)** — Workflow runs are `kind: workflow` rows; **`RuntimeEngine.run`** → `execute_workflow_run` (same queue/worker as chat). Flowgram export / spec hardening still open.
- [x] **Phase 6 (initial)** — `/internal/intake/*` requires `X-Service-Token` (`SERVICE_TOKEN`); target remains tools-only for product callers
- [x] **Phase 7 (initial)** — `POST /api/runs` + `/chat` alias; `/v1` documented bypass (Open WebUI); path naming polish later
- [x] **Phase 8 (incremental)** — When a **conversation run** is selected, main transcript uses [`transcriptFromRunEvents`](../product/web/src/lib/runStore.js); conversation list still loads messages API when no run selected
- [x] **Phase 9 (initial)** — [`product/widgets/renderRunEvent.jsx`](../product/widgets/renderRunEvent.jsx) + `RunTimeline`; expand coverage as types stabilize
- [x] **Phase 10 (existing)** — Dispatcher → `file_service.create_artifact` → `artifact.created` + `ArtifactPreview` in timeline
- [x] **Phase 11 (partial)** — Optional **`REDIS_URL`** + `notify_run_queued` / worker `BRPOP` (DB remains truth); **RQ/Celery** not adopted
- [x] **Phase 12 (initial)** — [`docs/AUTH_MATRIX.md`](AUTH_MATRIX.md); central `core/auth` enforcement still future
- [x] **Phase 13 (initial)** — [`core/runtime/control.py`](../core/runtime/control.py) for cancel entry; tool timeouts + retries in dispatcher
- [x] **Phase 14 (initial)** — `durationMs` on `tool.finished` events + **ToolResultCard** display
- [x] **Phase 15 (pass)** — Cancel via `control`; docs/links; deeper dedupe deferred
- [x] **Phase 16 (v0.7)** — Tag `v0.7.0` on release commit (run `git tag -a v0.7.0 -m "v0.7 hardening"` if not present)

---

## Recommended v0.7 slice (first shippable enforcement)

1. Implement **`RuntimeEngine.run(run_id)`** that delegates to existing chat/workflow bodies **without** changing behavior.  
2. Worker calls **only** `RuntimeEngine.run(run_id)`.  
3. Document **`/v1`** as *compatibility layer* or enqueue a **synthetic run** so Open WebUI participates in the same loop.  
4. Add contract tests: **no new** `dispatcher.run_tool` calls from `api/public` except via run execution.

---

## Files to add (target shape from spec)

```
core/runtime/engine.py
core/runtime/run_manager.py   # may merge with existing run_service
core/events/emitter.py        # single emit()
```

Keep renames minimal until Phase 15 to avoid a mega-diff.

---

## Related docs

- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)  
- [`docs/run-event-model.md`](run-event-model.md)  
- [`docs/workflow-spec.md`](workflow-spec.md)  
