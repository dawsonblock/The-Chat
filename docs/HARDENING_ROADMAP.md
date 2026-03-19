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
- [x] **Phase 1 (v0.7)** — Worker → `RuntimeEngine.run` only; **contract** [`test_api_no_direct_execution.py`](../tests/contract/test_api_no_direct_execution.py). **`executor`** exports only `RuntimeEngine`, `cancel_run`, `is_cancelled`. **Still to do:** Option B synthetic `/v1` run if eliminating bypass.
- [ ] **Phase 2 — Unify run model** — Migrate schema toward spec; collapse duplicate tables ([`schema-collapse.md`](schema-collapse.md))
- [x] **Phase 3 (initial)** — `emit()` for runtime + dispatcher; [`test_runtime_uses_emit.py`](../tests/contract/test_runtime_uses_emit.py); typed `RunEvent` union still future
- [ ] **Phase 4 — Tool boundary** — `execute()` contract, validation, timeout/retry wrappers; no direct Scrapling/fs/http outside tools
- [x] **Phase 5 (runtime path)** — Workflow runs are `kind: workflow` rows; **`RuntimeEngine.run`** → `execute_workflow_run` (same queue/worker as chat). Flowgram export / spec hardening still open.
- [x] **Phase 6 (initial)** — `/internal/intake/*` requires `X-Service-Token` (`SERVICE_TOKEN`); target remains tools-only for product callers
- [x] **Phase 7 (initial)** — `POST /api/runs` + `/chat` alias; `/v1` documented bypass (Open WebUI); path naming polish later
- [ ] **Phase 8 — Frontend** — Chat still hydrates `ConversationMessage` for history; live run uses events + `RunTimeline` — full event-only transcript is v0.8+
- [x] **Phase 9 (initial)** — [`product/widgets/renderRunEvent.jsx`](../product/widgets/renderRunEvent.jsx) + `RunTimeline`; expand coverage as types stabilize
- [ ] **Phase 10 — Artifacts** — Single flow: tool → disk → `ArtifactCreated` event → UI
- [x] **Phase 11 (partial)** — DB-queued runs + optional `python -m worker` when `WORKER_IN_PROCESS=false`; **Redis/RQ** still future
- [ ] **Phase 12 — Auth** — Uniform `user_id` on runs; tool/file/approval permission matrix
- [ ] **Phase 13 — Failure & control** — Cancel/retry policies owned by runtime layer
- [ ] **Phase 14 — Observability** — Run timeline, latency metrics per tool
- [ ] **Phase 15 — Cleanup** — Delete dead code paths, duplicate registries, stray backends
- [ ] **Phase 16 — Version tags** — Tag `v0.7`, `v0.8`, … when phases complete

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
