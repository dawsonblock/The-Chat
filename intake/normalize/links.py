from __future__ import annotations

from urllib.parse import urljoin


def normalize_links(base_url: str, links: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in links:
        if not item:
            continue
        full = urljoin(base_url, item)
        if full not in seen:
            seen.add(full)
            out.append(full)
    return out
