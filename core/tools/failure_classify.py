from __future__ import annotations


def classify_tool_failure(error_code: str | None, exc: BaseException | None = None) -> tuple[str, bool]:
    code = (error_code or '').lower()
    if code in {'approval_denied', 'missing_url', 'no_text'}:
        return 'user_error', False
    if code in {'timeout', 'connection'}:
        return 'retryable', True
    if code in {'ssrf_blocked', 'ssrf'}:
        return 'user_error', False
    if exc is not None:
        ename = type(exc).__name__
        if ename in {'TimeoutError', 'ConnectError', 'ReadTimeout', 'ConnectTimeout', 'NetworkError'}:
            return 'retryable', True
        if 'HTTPStatusError' in ename or 'HTTPError' in ename:
            return 'infra', False
    return 'infra', False
