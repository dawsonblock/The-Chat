from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text

from storage.db import Base


class Run(Base):
    __tablename__ = 'runs'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False, index=True)
    conversation_id = Column(String, ForeignKey('conversations.id'), nullable=True, index=True)
    kind = Column(String, nullable=False, default='chat')
    status = Column(String, nullable=False, default='queued', index=True)
    input_payload = Column(JSON, nullable=False, default=dict)
    output_text = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    failure_class = Column(String, nullable=True)
    cancel_requested = Column(Boolean, nullable=False, default=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RunEvent(Base):
    __tablename__ = 'run_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('runs.id'), nullable=False, index=True)
    seq_no = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ToolCall(Base):
    __tablename__ = 'tool_calls'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    run_id = Column(String, ForeignKey('runs.id'), nullable=False, index=True)
    tool_name = Column(String, nullable=False)
    args = Column(JSON, nullable=False, default=dict)
    status = Column(String, nullable=False, default='pending')
    idempotency_key = Column(String, nullable=True, index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ToolResult(Base):
    __tablename__ = 'tool_results'

    tool_call_id = Column(String, ForeignKey('tool_calls.id'), primary_key=True)
    ok = Column(Boolean, nullable=False)
    output = Column(JSON, nullable=True)
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    failure_class = Column(String, nullable=True)
    retryable = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ApprovalRequest(Base):
    __tablename__ = 'approval_requests'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    run_id = Column(String, ForeignKey('runs.id'), nullable=False, index=True)
    tool_call_id = Column(String, ForeignKey('tool_calls.id'), nullable=False, index=True)
    title = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    risk = Column(String, nullable=False, default='medium')
    args_preview = Column(JSON, nullable=False, default=dict)
    status = Column(String, nullable=False, default='pending')
    decision = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    decided_at = Column(DateTime, nullable=True)


class Artifact(Base):
    __tablename__ = 'artifacts'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    run_id = Column(String, ForeignKey('runs.id'), nullable=False, index=True)
    tool_call_id = Column(String, ForeignKey('tool_calls.id'), nullable=True, index=True)
    kind = Column(String, nullable=False)
    name = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    uri = Column(String, nullable=False)
    preview = Column(Text, nullable=True)
    meta_json = Column('metadata', JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
