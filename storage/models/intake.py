from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text

from storage.db import Base


class FetchLog(Base):
    __tablename__ = 'fetch_logs'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    url = Column(String, nullable=False, index=True)
    status_code = Column(Integer, nullable=True)
    fetch_mode = Column(String, nullable=False)
    render_js = Column(Boolean, nullable=False, default=False)
    duration_ms = Column(Integer, nullable=False, default=0)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ExtractedDocument(Base):
    __tablename__ = 'extracted_documents'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    source_url = Column(String, nullable=False, index=True)
    title = Column(String, nullable=True)
    text_content = Column(Text, nullable=False)
    html_content = Column(Text, nullable=True)
    meta_json = Column('metadata', JSON, nullable=False, default=dict)
    links = Column(JSON, nullable=False, default=list)
    content_hash = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CrawlJob(Base):
    __tablename__ = 'crawl_jobs'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    start_url = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default='queued')
    max_depth = Column(Integer, nullable=False, default=1)
    max_pages = Column(Integer, nullable=False, default=10)
    pages_fetched = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=True)
    result_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)


class CrawlPage(Base):
    __tablename__ = 'crawl_pages'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    crawl_job_id = Column(String, ForeignKey('crawl_jobs.id'), nullable=False, index=True)
    url = Column(String, nullable=False, index=True)
    depth = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default='fetched')
    title = Column(String, nullable=True)
    link_count = Column(Integer, nullable=False, default=0)
    text_preview = Column(Text, nullable=True)
    document_id = Column(String, ForeignKey('extracted_documents.id'), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
