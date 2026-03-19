from __future__ import annotations

from fastapi import HTTPException

from core.runtime.service import run_service
from storage.models import Run


def require_run_for_user(run_id: str, user_id: str) -> Run:
    """Return the run if it exists and belongs to ``user_id``; else 404 (no existence leak)."""
    run = run_service.get_run(run_id)
    if run is None or run.user_id != user_id:
        raise HTTPException(status_code=404, detail='Run not found')
    return run
