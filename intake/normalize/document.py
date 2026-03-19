from __future__ import annotations

from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field


class NormalizedDocument(BaseModel):
    source_url: str
    final_url: str | None = None
    title: str | None = None
    text_content: str
    html_content: str | None = None
    links: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    content_hash: str


def content_hash(text: str) -> str:
    return sha256(text.encode('utf-8')).hexdigest()
