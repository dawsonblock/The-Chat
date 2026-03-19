from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String

from storage.db import Base


class Workflow(Base):
    __tablename__ = 'workflows'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WorkflowVersion(Base):
    __tablename__ = 'workflow_versions'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    workflow_id = Column(String, ForeignKey('workflows.id'), nullable=False, index=True)
    version = Column(String, nullable=False, default='1.0.0')
    spec = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WorkflowRun(Base):
    __tablename__ = 'workflow_runs'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    workflow_version_id = Column(String, ForeignKey('workflow_versions.id'), nullable=False, index=True)
    run_id = Column(String, ForeignKey('runs.id'), nullable=False, unique=True, index=True)
    inputs = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
