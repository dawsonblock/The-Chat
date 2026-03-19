from __future__ import annotations

import asyncio

from core.runtime.engine import RuntimeEngine
from core.runtime.service import run_service


def test_runtime_engine_unknown_kind_marks_run_failed():
    row = run_service.create_run(
        user_id='baseline-user',
        conversation_id=None,
        kind='bogus_kind',
        input_payload={},
    )
    asyncio.run(RuntimeEngine().run(row.id))
    updated = run_service.get_run(row.id)
    assert updated is not None
    assert updated.status == 'failed'
    assert updated.failure_class == 'user_error'
