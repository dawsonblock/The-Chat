# Plan: matrix path alignment + permissions + docs + contract test

## Goals

1. Add **canonical paths** from the v0.7–v1.0 matrix without duplicating logic (`core/events/persist/store`, `intake/extract/extract_page`, split `api/internal/intake/*`).
2. Add **`core/tools/permissions/checks.py`** for policy helpers (single gate with dispatcher).
3. Add **operator / spec / security** docs and **`requirements.lock`** for reproducible installs.
4. Add **contract test** for critical OpenAPI paths.

## Done when

- Imports resolve; `pytest` passes; `api.internal.intake` is a package (no `intake.py` file shadowing).
