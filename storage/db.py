from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import settings

Base = declarative_base()


def _connect_args(url: str) -> dict:
    if url.startswith('sqlite'):
        db_path = url.replace('sqlite:///', '')
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return {'check_same_thread': False}
    return {}


engine = create_engine(settings.database_url, future=True, connect_args=_connect_args(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
