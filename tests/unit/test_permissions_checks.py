from __future__ import annotations

from core.tools.permissions.checks import tool_max_retries, tool_requires_approval


def test_crawl_site_requires_approval_by_default():
    assert tool_requires_approval('crawl_site') is True


def test_summarize_has_zero_default_retries():
    assert tool_max_retries('summarize_text') == 0
