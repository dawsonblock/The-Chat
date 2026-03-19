# Intake security

## SSRF

- `intake/extract/fetch.py` allows only `http`/`https`, resolves DNS, and blocks private/loopback/link-local targets unless `INTAKE_ALLOW_PRIVATE_HOSTS=true`.
- **Redirects:** final URL is re-validated after fetch.

## Domain policy

- `INTAKE_DENY_DOMAINS` — comma-separated hostnames (default blocks common local names).
- `INTAKE_ALLOW_DOMAINS` — if non-empty, only those hosts (suffix match) are allowed.

## Sanitization

- **bleach** strips unsafe HTML for previews (`intake/extract/parse.py`, `core/files/service.preview_content`).
- Raw HTML may still be stored for extraction artifacts; UI should prefer `preview_only` API where possible.

## Internal API

`/internal/intake/*` requires `X-Service-Token` matching `SERVICE_TOKEN` (see `backend.config.settings`).
