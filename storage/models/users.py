from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from storage.db import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Session(Base):
    __tablename__ = 'sessions'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String, nullable=False, default='New conversation')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ConversationMessage(Base):
    __tablename__ = 'conversation_messages'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    conversation_id = Column(String, ForeignKey('conversations.id'), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    run_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class UploadedFile(Base):
    __tablename__ = 'uploaded_files'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    original_name = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    size_bytes = Column(String, nullable=False)
    sha256 = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
