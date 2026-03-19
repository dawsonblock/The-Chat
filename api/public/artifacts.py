from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from core.auth.service import get_current_user
from storage.db import SessionLocal
from storage.models import Artifact, Run

router = APIRouter(prefix='/api/artifacts', tags=['artifacts'])


@router.get('')
def list_artifacts(run_id: str | None = Query(default=None), user=Depends(get_current_user)):
    with SessionLocal() as db:
        query = db.query(Artifact, Run).join(Run, Run.id == Artifact.run_id).filter(Run.user_id == user.user_id)
        if run_id:
            query = query.filter(Artifact.run_id == run_id)
        rows = query.order_by(Artifact.created_at.desc()).limit(200).all()
        return [
            {
                'id': artifact.id,
                'run_id': artifact.run_id,
                'tool_call_id': artifact.tool_call_id,
                'kind': artifact.kind,
                'name': artifact.name,
                'mime_type': artifact.mime_type,
                'uri': artifact.uri,
                'preview': artifact.preview,
                'metadata': artifact.meta_json,
                'created_at': artifact.created_at.isoformat(),
            }
            for artifact, _run in rows
        ]


@router.get('/{artifact_id}')
def get_artifact(artifact_id: str, user=Depends(get_current_user)):
    with SessionLocal() as db:
        row = db.query(Artifact, Run).join(Run, Run.id == Artifact.run_id).filter(Artifact.id == artifact_id, Run.user_id == user.user_id).first()
        if not row:
            raise HTTPException(status_code=404, detail='Artifact not found')
        artifact, _run = row
        return {
            'id': artifact.id,
            'run_id': artifact.run_id,
            'tool_call_id': artifact.tool_call_id,
            'kind': artifact.kind,
            'name': artifact.name,
            'mime_type': artifact.mime_type,
            'uri': artifact.uri,
            'preview': artifact.preview,
            'metadata': artifact.meta_json,
            'created_at': artifact.created_at.isoformat(),
        }
