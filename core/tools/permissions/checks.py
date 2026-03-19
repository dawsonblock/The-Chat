from __future__ import annotations

from core.tools.policy import effective_tool_policy
from core.tools.registry import registry


def tool_requires_approval(tool_name: str) -> bool:
    """Whether policy + registry require human approval before execution."""
    tool = registry.get(tool_name)
    return bool(effective_tool_policy(tool_name, tool)['requires_approval'])


def tool_max_retries(tool_name: str) -> int:
    tool = registry.get(tool_name)
    return int(effective_tool_policy(tool_name, tool)['max_retries'] or 0)
