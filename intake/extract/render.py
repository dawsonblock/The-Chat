"""Browser-backed acquisition (v0.8 Scrapling pass).

`render_js=True` on `extract_page` is rejected until this module wraps an imported
renderer with explicit resource limits and host SSRF checks.
"""

from __future__ import annotations


async def render_page_html(url: str, *, wait_ms: int = 5000) -> tuple[str, str]:
    raise NotImplementedError(
        'JS rendering is gated for v0.8 Scrapling absorption; use HTTP fetch or pin Scrapling render primitives.'
    )
