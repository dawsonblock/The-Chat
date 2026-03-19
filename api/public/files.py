from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from core.auth.service import get_current_user
from core.files.artifacts import resolve_artifact_file
from core.files.service import PREVIEW_HTML_MAX, PREVIEW_TEXT_MAX, file_service, preview_content
from storage.db import SessionLocal
from storage.models import Artifact, Run, UploadedFile

router = APIRouter(prefix='/api/files', tags=['files'])


@router.post('/upload')
async def upload_file(file: UploadFile = File(...), user=Depends(get_current_user)):
    content = await file.read()
    row = file_service.save_upload(user_id=user.user_id, filename=file.filename, content=content, mime_type=file.content_type)
    return {'id': row.id, 'original_name': row.original_name, 'mime_type': row.mime_type, 'size_bytes': row.size_bytes}


@router.get('/uploaded/{file_id}')
def get_uploaded_file(file_id: str, user=Depends(get_current_user)):
    with SessionLocal() as db:
        row = db.query(UploadedFile).filter(UploadedFile.id == file_id, UploadedFile.user_id == user.user_id).first()
        if not row:
            raise HTTPException(status_code=404, detail='File not found')
        return {'id': row.id, 'original_name': row.original_name, 'mime_type': row.mime_type, 'size_bytes': row.size_bytes, 'storage_path': row.storage_path}


@router.get('/{artifact_id}')
def get_artifact_meta(artifact_id: str, user=Depends(get_current_user)):
    with SessionLocal() as db:
        row = db.query(Artifact, Run).join(Run, Run.id == Artifact.run_id).filter(Artifact.id == artifact_id, Run.user_id == user.user_id).first()
        if not row:
            raise HTTPException(status_code=404, detail='Artifact not found')
        artifact, _run = row
        return {
            'id': artifact.id,
            'run_id': artifact.run_id,
            'kind': artifact.kind,
            'name': artifact.name,
            'mime_type': artifact.mime_type,
            'uri': artifact.uri,
            'preview': artifact.preview,
            'metadata': artifact.meta_json,
        }


@router.get('/{artifact_id}/content')
def get_artifact_content(
    artifact_id: str,
    preview_only: bool = Query(default=False),
    user=Depends(get_current_user),
):
    with SessionLocal() as db:
        row = db.query(Artifact, Run).join(Run, Run.id == Artifact.run_id).filter(Artifact.id == artifact_id, Run.user_id == user.user_id).first()
        if not row:
            raise HTTPException(status_code=404, detail='Artifact not found')
        artifact, _run = row
    path = resolve_artifact_file(artifact_id)
    if not path or not path.is_file():
        raise HTTPException(status_code=404, detail='Artifact content missing')
    if preview_only:
        text = path.read_text(encoding='utf-8', errors='ignore')
        snippet = preview_content(artifact.mime_type or '', text)
        m = (artifact.mime_type or '').lower()
        limit = PREVIEW_HTML_MAX if 'html' in m else PREVIEW_TEXT_MAX
        return {
            'artifact_id': artifact_id,
            'mime_type': artifact.mime_type,
            'snippet': snippet,
            'full_length': len(text),
            'truncated': len(text) > limit,
        }
    media = artifact.mime_type or 'application/octet-stream'
    return FileResponse(path, media_type=media, filename=artifact.name or path.name)
