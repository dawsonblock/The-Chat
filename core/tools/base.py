from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolExecutionResult:
    ok: bool
    output: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    failure_class: str | None = None
    retryable: bool | None = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)


class ToolContext:
    def __init__(self, run_id: str, user_id: str, conversation_id: str | None = None):
        self.run_id = run_id
        self.user_id = user_id
        self.conversation_id = conversation_id


class ToolDefinition:
    name = 'tool'
    description = ''
    requires_approval = False
    risk = 'low'
    max_retries = 0
    retry_delay_seconds = 0.5

    async def run(self, ctx: ToolContext, args: dict[str, Any]) -> ToolExecutionResult:
        raise NotImplementedError
