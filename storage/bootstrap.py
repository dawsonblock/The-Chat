from pathlib import Path

from backend.config import settings
from storage.db import Base, engine
from storage import models  # noqa: F401
from storage.migrate import ensure_schema


def init_db() -> None:
    Path(settings.artifacts_dir).mkdir(parents=True, exist_ok=True)
    ensure_schema()
    from core.tools.policy import seed_tool_policies_from_registry

    seed_tool_policies_from_registry()
