from __future__ import annotations

from pathlib import Path

from backend.config import settings


def artifact_dir() -> Path:
    return Path(settings.artifacts_dir) / 'artifacts'


def resolve_artifact_file(artifact_id: str) -> Path | None:
    matches = list(artifact_dir().glob(f'{artifact_id}.*'))
    return matches[0] if matches else None
