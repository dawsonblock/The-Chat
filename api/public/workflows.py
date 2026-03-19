from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth.service import get_current_user
from core.workflows.compile import compile_workflow_spec
from core.workflows.service import workflow_service
from core.workflows.spec import validate_workflow_spec
from core.tools.registry import registry
from storage.db import SessionLocal
from storage.models import Workflow, WorkflowVersion

router = APIRouter(prefix='/api/workflows', tags=['workflows'])


class ValidateBody(BaseModel):
    spec: dict


class RegisterBody(BaseModel):
    spec: dict


class RunWorkflowBody(BaseModel):
    inputs: dict = {}


@router.get('')
def list_workflows(user=Depends(get_current_user)):
    return workflow_service.list(user.user_id)


@router.post('/validate')
def validate_workflow(body: ValidateBody, user=Depends(get_current_user)):
    return validate_workflow_spec(body.spec, {t['name'] for t in registry.list_tools()})


@router.post('/register')
def register_workflow(body: RegisterBody, user=Depends(get_current_user)):
    result = validate_workflow_spec(body.spec, {t['name'] for t in registry.list_tools()})
    if not result['ok']:
        raise HTTPException(status_code=400, detail=result)
    spec = compile_workflow_spec(body.spec)
    return workflow_service.register(user.user_id, spec)


@router.post('/{workflow_version_id}/run')
async def run_workflow(workflow_version_id: str, body: RunWorkflowBody, user=Depends(get_current_user)):
    run = workflow_service.create_run(user_id=user.user_id, workflow_version_id=workflow_version_id, inputs=body.inputs)
    return {'run_id': run.id, 'status': run.status}
