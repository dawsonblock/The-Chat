from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

import bleach

from backend.config import settings
from storage.db import SessionLocal
from storage.models import Artifact, UploadedFile

PREVIEW_TEXT_MAX = 2000
PREVIEW_HTML_MAX = 8000

_HTML_TAGS = frozenset({'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'code', 'pre', 'blockquote', 'h1', 'h2', 'h3'})
_HTML_ATTRS = {'a': ['href', 'title', 'rel']}


def preview_content(mime_type: str, content: str) -> str:
    m = (mime_type or '').lower()
    if 'html' in m:
        cleaned = bleach.clean(content, tags=_HTML_TAGS, attributes=_HTML_ATTRS, strip=True)
        if len(cleaned) > PREVIEW_HTML_MAX:
            return cleaned[:PREVIEW_HTML_MAX] + '\n…'
        return cleaned
    if len(content) > PREVIEW_TEXT_MAX:
        return content[:PREVIEW_TEXT_MAX] + '\n…'
    return content


class FileService:
    def __init__(self) -> None:
        self.base = Path(settings.artifacts_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def save_upload(self, *, user_id: str, filename: str, content: bytes, mime_type: str | None) -> UploadedFile:
        sha = hashlib.sha256(content).hexdigest()
        ext = Path(filename).suffix or ''
        path = self.base / 'uploads'
        path.mkdir(parents=True, exist_ok=True)
        file_id = str(uuid4())
        target = path / f'{file_id}{ext}'
        target.write_bytes(content)
        with SessionLocal() as db:
            row = UploadedFile(
                user_id=user_id,
                original_name=filename,
                storage_path=str(target),
                mime_type=mime_type or 'application/octet-stream',
                size_bytes=str(len(content)),
                sha256=sha,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row

    def create_artifact(self, *, run_id: str, tool_call_id: str | None, kind: str, name: str, mime_type: str, content: str, metadata: dict | None = None) -> dict:
        artifact_id = str(uuid4())
        ext_map = {'text/plain': '.txt', 'text/html': '.html', 'application/json': '.json'}
        ext = ext_map.get(mime_type, '.bin')
        folder = self.base / 'artifacts'
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f'{artifact_id}{ext}'
        target.write_text(content, encoding='utf-8')
        preview = preview_content(mime_type, content)
        uri = f'/api/files/{artifact_id}/content'
        meta = dict(metadata or {})
        meta['storage_path'] = str(target)
        with SessionLocal() as db:
            row = Artifact(
                id=artifact_id,
                run_id=run_id,
                tool_call_id=tool_call_id,
                kind=kind,
                name=name,
                mime_type=mime_type,
                uri=uri,
                preview=preview,
                meta_json=meta,
            )
            db.add(row)
            db.commit()
        return {
            'id': artifact_id,
            'kind': kind,
            'name': name,
            'mime_type': mime_type,
            'uri': uri,
            'preview': preview,
            'metadata': meta,
            'storage_path': str(target),
        }


file_service = FileService()
