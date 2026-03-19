# Operator One — single runtime hardening roadmap

This maps the **non-negotiable target** (one loop: input → run → runtime → events → persist → stream → UI → approval → completion) to **this repository** and tracks phases 0–16 from the product spec.

**Baseline inventory:** [`docs/baseline.md`](baseline.md)  
**Branch for work:** `operator-one-hardening`

---

## Honest current state (vs spec)

| Spec expectation | This repo today |
|------------------|-----------------|
| Single `RuntimeEngine.run(run_id)` | Worker calls `execute_chat_run` / `execute_workflow_run`; no `engine.py` |
| `emit()` → persist + stream only | `build_event`, `event_bus`, `event_store`, SSE formatter — multiple touchpoints |
| POST `/api/runs` only entry | `POST /api/runs/chat`, workflow-specific POST, **`/v1/chat/completions`** |
| No tool execution from API routes | Internal intake routes exist; OpenAI compat calls `provider` directly |
| Redis + RQ worker | **In-process** asyncio worker + SQLite/Postgres via SQLAlchemy |
| Events only in `run_events` | **`tool_calls`**, **`tool_results`**, **`approval_requests`** plus `run_events` |
| Postgres JSONB | SQLite default; JSON columns portable to Postgres |

---

## Phase checklist

- [x] **Phase 0 — Freeze baseline** — `docs/baseline.md`, branch `operator-one-hardening`
- [x] **Phase 1 (initial)** — `core/runtime/engine.py` (`RuntimeEngine.run`), `run_manager.py`, `event_emitter.py` stub; **worker** calls only `RuntimeEngine().run(run.id)`. Chat/workflow bodies unchanged. **Still to do:** ban `execute_*` imports from `api/`, fold `/v1` into runs, rename/merge `executor` re-exports.
- [ ] **Phase 2 — Unify run model** — Migrate schema toward spec (or document intentional deltas); collapse duplicate tables into events where safe
- [ ] **Phase 3 — Event system** — One `RunEvent` contract + `emit()` = persist + SSE; retire parallel formats
- [ ] **Phase 4 — Tool boundary** — `execute()` contract, validation, timeout/retry wrappers; no direct Scrapling/fs/http outside tools
- [ ] **Phase 5 — Workflows** — `WorkflowSpec` → compile plan → **same** engine path as chat
- [ ] **Phase 6 — Intake** — Only via tools; remove or gate `/internal/intake` for non-admin
- [ ] **Phase 7 — API consolidation** — Align to `POST /api/runs`, `GET /api/runs/:id/events`, etc.; decide fate of `/v1` (proxy vs separate product)
- [ ] **Phase 8 — Frontend** — Chat renders **only** from run events; remove message-only state where redundant
- [ ] **Phase 9 — Widgets** — Central `renderEvent(event)` router; align payloads to Phase 3 types
- [ ] **Phase 10 — Artifacts** — Single flow: tool → disk → `ArtifactCreated` event → UI
- [ ] **Phase 11 — Queue** — Optional Redis/RQ worker process; API enqueue-only
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
