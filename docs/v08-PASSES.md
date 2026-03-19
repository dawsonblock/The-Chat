# v0.8 absorption passes (execution order)

Upstream code is **not** vendored in this repository until each repo is cloned and pinned (see `docs/import-audit/*.md`). This document is the control checklist for the five passes.

## Pass 1 — Agno → runtime/tools/events

- **Targets:** `core/runtime/providers/`, `core/tools/`, `core/events/`
- **Entry anchor:** [`core/runtime/providers/README.md`](../core/runtime/providers/README.md)
- **Exit:** tool dispatch + provider routing still use one `Run` / `RunEvent` model; add Agno-derived modules beside [`core/runtime/provider.py`](../core/runtime/provider.py).

## Pass 2 — Scrapling → intake

- **Targets:** `intake/extract/`, `intake/crawl/`
- **Entry anchors:** [`intake/extract/render.py`](../intake/extract/render.py) (JS acquisition gate), fetch/parse split.
- **Exit:** `NormalizedDocument` remains the only outward document type.

## Pass 3 — Open WebUI → product shell

- **Targets:** `product/web/src/`
- **Entry anchor:** [`product/web/src/shell/README.md`](../product/web/src/shell/README.md)
- **Exit:** no second auth or file truth; still talk to `/api/*` only.

## Pass 4 — Tool UI → widgets

- **Targets:** `product/widgets/`, chat/run components
- **Exit:** widgets remain stateless; props from bundle/SSE shapes.

## Pass 5 — Flowgram → workflow editor

- **Targets:** `product/workflow/editor/`
- **Entry anchor:** [`product/workflow/editor/BOUNDARY.md`](../product/workflow/editor/BOUNDARY.md)
- **Exit:** export compiles to [`core/workflows/spec.py`](../core/workflows/spec.py); execution stays in worker + `execute_workflow_run`.

After each pass: run `pytest` + `scripts/smoke.sh` + UI smoke for the touched surface.
