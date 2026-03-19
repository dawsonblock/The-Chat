from __future__ import annotations

"""Single read path for loading a run row before execution (see `RuntimeEngine`)."""

from storage.models import Run

from core.runtime.service import run_service


def get_run_for_execution(run_id: str) -> Run | None:
    return run_service.get_run(run_id)
