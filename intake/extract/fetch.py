from __future__ import annotations

import asyncio
import socket
from ipaddress import ip_address
from urllib.parse import urlparse

import httpx

from backend.config import settings


class SSRFBlocked(Exception):
    def __init__(self, message: str = 'Target host is not allowed (SSRF protection).'):
        super().__init__(message)


def _domain_policy_allows(host: str) -> None:
    host_l = host.lower().strip('.')
    deny = [d.strip().lower() for d in settings.intake_deny_domains.split(',') if d.strip()]
    for d in deny:
        if host_l == d or host_l.endswith('.' + d):
            raise SSRFBlocked(f'Host {host!r} matches deny policy.')
    allow = [a.strip().lower() for a in settings.intake_allow_domains.split(',') if a.strip()]
    if allow:
        if not any(host_l == a or host_l.endswith('.' + a) for a in allow):
            raise SSRFBlocked('Host is not on the allow list.')


async def _assert_resolved_ips_safe(hostname: str) -> None:
    if settings.intake_allow_private_hosts:
        return

    def resolve() -> list[str]:
        ips: list[str] = []
        for fam, _, _, _, sockaddr in socket.getaddrinfo(hostname, None):
            if fam in (socket.AF_INET, socket.AF_INET6):
                ips.append(sockaddr[0])
        return ips

    try:
        raw_ips = await asyncio.to_thread(resolve)
    except socket.gaierror as exc:
        raise SSRFBlocked(f'DNS resolution failed: {exc}') from exc

    for raw in raw_ips:
        addr = ip_address(raw)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            raise SSRFBlocked('Resolved to a private or loopback address.')
        if str(addr) == '169.254.169.254':
            raise SSRFBlocked('Metadata endpoints are blocked.')


def assert_safe_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        raise SSRFBlocked('Only http and https URLs are allowed.')
    host = parsed.hostname
    if not host:
        raise SSRFBlocked('URL is missing a host.')
    _domain_policy_allows(host)


async def validate_fetch_targets(url: str, final_url: str) -> None:
    for candidate in {url, final_url}:
        assert_safe_http_url(candidate)
        parsed = urlparse(candidate)
        assert parsed.hostname
        await _assert_resolved_ips_safe(parsed.hostname)


async def http_get_html(url: str) -> tuple[str, str, int]:
    assert_safe_http_url(url)
    parsed = urlparse(url)
    assert parsed.hostname
    await _assert_resolved_ips_safe(parsed.hostname)
    timeout = httpx.Timeout(settings.intake_read_timeout, connect=settings.intake_connect_timeout)
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=timeout,
        max_redirects=settings.intake_max_redirects,
        headers={'User-Agent': 'OperatorOne/0.7'},
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        final_url = str(response.url)
        await validate_fetch_targets(url, final_url)
        return response.text, final_url, response.status_code
