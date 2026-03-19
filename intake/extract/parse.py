from __future__ import annotations

import bleach
from bs4 import BeautifulSoup

from intake.normalize.links import normalize_links


ALLOWED_TAGS = frozenset(
    {'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'code', 'pre', 'blockquote', 'h1', 'h2', 'h3', 'span', 'div'}
)
ALLOWED_ATTRS = {'a': ['href', 'title', 'rel']}


def parse_html(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    links = [a.get('href') for a in soup.find_all('a') if a.get('href')]
    text = ' '.join(soup.stripped_strings)
    return {
        'title': title,
        'text': text,
        'links': normalize_links(base_url, links),
    }


def sanitize_html_for_preview(html: str, *, max_length: int = 8000) -> str:
    cleaned = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    if len(cleaned) > max_length:
        return cleaned[:max_length] + '\n…'
    return cleaned
