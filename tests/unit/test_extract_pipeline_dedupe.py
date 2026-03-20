from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from storage.migrate import ensure_schema


@pytest.fixture(autouse=True)
def _schema():
    ensure_schema()


def test_deduplicated_extract_includes_sanitized_preview_html():
    """Dedupe path must set metadata.sanitized_preview_html like the fresh extract path."""
    html = '<html><body><p>Unique dedupe marker xyz789</p></body></html>'

    async def run_both():
        with patch('intake.extract.pipeline.http_get_html', new_callable=AsyncMock) as m:
            m.return_value = (html, 'https://a.example/p', 200)
            from intake.extract.pipeline import extract_page

            doc1 = await extract_page('https://a.example/p', include_html=True)
            assert 'sanitized_preview_html' in doc1.metadata

            doc2 = await extract_page('https://b.example/q', include_html=True)
            assert doc2.metadata.get('deduplicated') is True
            assert 'sanitized_preview_html' in doc2.metadata

    asyncio.run(run_both())
