from __future__ import annotations

from datetime import datetime

from core.runtime.run_queue_signal import notify_run_queued
from core.runtime.service import run_service
from storage.db import SessionLocal
from storage.models import Run, Workflow, WorkflowRun, WorkflowVersion


class WorkflowService:
    def register(self, user_id: str, spec: dict) -> dict:
        with SessionLocal() as db:
            workflow = Workflow(user_id=user_id, name=spec.get('name', 'Workflow'), updated_at=datetime.utcnow())
            db.add(workflow)
            db.commit()
            db.refresh(workflow)
            version = WorkflowVersion(workflow_id=workflow.id, version='1.0.0', spec=spec)
            db.add(version)
            db.commit()
            db.refresh(version)
            return {'workflow_id': workflow.id, 'workflow_version_id': version.id, 'version': version.version}

    def list(self, user_id: str) -> list[dict]:
        with SessionLocal() as db:
            rows = db.query(Workflow, WorkflowVersion).join(WorkflowVersion, Workflow.id == WorkflowVersion.workflow_id).filter(Workflow.user_id == user_id).order_by(Workflow.updated_at.desc()).all()
            return [{'workflow_id': w.id, 'name': w.name, 'version_id': v.id, 'version': v.version, 'spec': v.spec} for w, v in rows]

    def create_run(self, *, user_id: str, workflow_version_id: str, inputs: dict) -> Run:
        with SessionLocal() as db:
            run = Run(user_id=user_id, kind='workflow', status='queued', input_payload={'workflow_version_id': workflow_version_id, 'inputs': inputs})
            db.add(run)
            db.commit()
            db.refresh(run)
            db.add(WorkflowRun(workflow_version_id=workflow_version_id, run_id=run.id, inputs=inputs))
            db.commit()
            notify_run_queued(run.id)
            return run


workflow_service = WorkflowService()
