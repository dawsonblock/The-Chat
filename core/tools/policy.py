from __future__ import annotations

from typing import Any

from sqlalchemy.exc import OperationalError

from core.tools.base import ToolDefinition
from storage.db import SessionLocal
from storage.models import ToolPolicy


def effective_tool_policy(name: str, tool: ToolDefinition) -> dict[str, Any]:
    row = None
    try:
        with SessionLocal() as db:
            row = db.query(ToolPolicy).filter(ToolPolicy.tool_name == name).first()
    except OperationalError:
        pass
    return {
        'requires_approval': row.requires_approval if row else tool.requires_approval,
        'risk': row.risk if row else getattr(tool, 'risk', 'low'),
        'max_retries': row.max_retries if row is not None else getattr(tool, 'max_retries', 0),
        'retry_delay_seconds': row.retry_delay_seconds if row is not None else getattr(tool, 'retry_delay_seconds', 0.5),
    }


def seed_tool_policies_from_registry() -> None:
    from core.tools.registry import registry

    with SessionLocal() as db:
        for name, tool in registry._tools.items():
            if db.query(ToolPolicy).filter(ToolPolicy.tool_name == name).first():
                continue
            db.add(
                ToolPolicy(
                    tool_name=name,
                    requires_approval=tool.requires_approval,
                    risk=getattr(tool, 'risk', 'low'),
                    max_retries=getattr(tool, 'max_retries', 0),
                    retry_delay_seconds=getattr(tool, 'retry_delay_seconds', 0.5),
                )
            )
        db.commit()
