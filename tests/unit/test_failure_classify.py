from __future__ import annotations

from core.tools.failure_classify import classify_tool_failure


def test_classify_approval_denied():
    fc, retry = classify_tool_failure('approval_denied')
    assert fc == 'user_error'
    assert retry is False


def test_classify_ssrf():
    fc, retry = classify_tool_failure('ssrf_blocked')
    assert fc == 'user_error'
    assert retry is False
