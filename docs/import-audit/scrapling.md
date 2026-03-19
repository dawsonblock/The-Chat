# Import audit: Scrapling

## Repo

- **name:** Scrapling
- **commit pinned:** _TBD_
- **local path:** _e.g. `/path/to/Scrapling-main`_

## Purpose (1–2 sentences)

Resilient HTTP acquisition, parsing, optional rendering, and crawl primitives—land behind a single `NormalizedDocument` boundary.

## Target destination in operator-one

- `intake/extract/`
- `intake/crawl/`
- `intake/monitor/`
- `intake/normalize/`

## Directory classification

| Path | Purpose | Action | Destination | Notes |
|------|---------|--------|-------------|-------|
| _(inspect)_ | fetch / session | COPY/ADAPT | `intake/extract/fetch.py`, `session.py` | Replace httpx-only path where stronger |
| _(inspect)_ | parse / extract | ADAPT | `intake/extract/parse.py` | Keep bleach + SSRF policy in host |
| _(inspect)_ | render / browser | ADAPT | `intake/extract/render.py` | Gate `render_js` default false |
| _(inspect)_ | crawl frontier | ADAPT | `intake/crawl/` | Single worker + DB truth |
| CLI / demos | packaging | IGNORE | — | |

## Subsystems

### Fetch/session

- **Destination:** `intake/extract/`
- **Replaces:** v0.7 httpx wrapper where Scrapling is strictly better

### Parse / normalize

- **Destination:** `intake/normalize/`, `intake/extract/parse.py`
- **Replaces:** BeautifulSoup-only paths selectively

### Crawl

- **Destination:** `intake/crawl/`
- **Replaces:** shallow `intake/crawl.py` scheduler as v0.9 hardens workers

## Conflict detection

- [ ] second public intake API
- [ ] second document schema (must stay `NormalizedDocument`)

## Data mapping

| Upstream | operator-one |
|----------|--------------|
| Page / document | `NormalizedDocument` |
| Links | `normalize_links` output |

## Deletions triggered by this import

- Redundant fetch helpers after Scrapling-backed modules land
- Duplicate normalize helpers

## Integration checks

- [ ] `extract_page` tool still returns artifacts + `NormalizedDocument` fields
- [ ] SSRF / allowlist still enforced at host boundary
- [ ] Internal API `/internal/intake/*` unchanged contract
