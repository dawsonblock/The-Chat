from __future__ import annotations

from sqlalchemy import Boolean, Column, Float, Integer, String

from storage.db import Base


class ToolPolicy(Base):
    __tablename__ = 'tool_policies'

    tool_name = Column(String, primary_key=True)
    requires_approval = Column(Boolean, nullable=False, default=False)
    risk = Column(String, nullable=False, default='low')
    max_retries = Column(Integer, nullable=False, default=0)
    retry_delay_seconds = Column(Float, nullable=False, default=0.5)
