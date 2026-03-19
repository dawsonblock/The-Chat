from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth.service import get_current_user
from core.tools.policy import effective_tool_policy
from core.tools.registry import registry
from storage.db import SessionLocal
from storage.models import ToolPolicy

router = APIRouter(prefix='/api/tools', tags=['tools'])


class ToolPolicyUpdate(BaseModel):
    requires_approval: bool | None = None
    risk: str | None = None
    max_retries: int | None = None
    retry_delay_seconds: float | None = None


@router.get('')
def list_tools(user=Depends(get_current_user)):
    return registry.list_tools()


@router.get('/meta/policies')
def list_tool_policies(user=Depends(get_current_user)):
    out = []
    for t in registry.list_tools():
        name = t['name']
        tool = registry.get(name)
        eff = effective_tool_policy(name, tool)
        out.append({'name': name, **eff})
    return out


@router.put('/meta/policies/{tool_name}')
def update_tool_policy(tool_name: str, body: ToolPolicyUpdate, user=Depends(get_current_user)):
    registry.get(tool_name)
    with SessionLocal() as db:
        row = db.query(ToolPolicy).filter(ToolPolicy.tool_name == tool_name).first()
        if not row:
            row = ToolPolicy(tool_name=tool_name)
            db.add(row)
        if body.requires_approval is not None:
            row.requires_approval = body.requires_approval
        if body.risk is not None:
            row.risk = body.risk
        if body.max_retries is not None:
            row.max_retries = body.max_retries
        if body.retry_delay_seconds is not None:
            row.retry_delay_seconds = body.retry_delay_seconds
        db.commit()
        db.refresh(row)
    tool = registry.get(tool_name)
    return {'name': tool_name, **effective_tool_policy(tool_name, tool)}


@router.get('/{tool_name}')
def get_tool(tool_name: str, user=Depends(get_current_user)):
    for tool in registry.list_tools():
        if tool['name'] == tool_name:
            return tool
    raise HTTPException(status_code=404, detail='Tool not found')
