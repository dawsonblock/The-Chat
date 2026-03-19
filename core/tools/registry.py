from __future__ import annotations

from core.tools.base import ToolDefinition
from core.tools.definitions import BUILTIN_TOOL_CLASSES


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        for tool_cls in BUILTIN_TOOL_CLASSES:
            tool = tool_cls()
            self._tools[tool.name] = tool

    def list_tools(self) -> list[dict]:
        return [
            {
                'name': tool.name,
                'description': tool.description,
                'requires_approval': tool.requires_approval,
                'risk': getattr(tool, 'risk', 'low'),
            }
            for tool in self._tools.values()
        ]

    def get(self, name: str) -> ToolDefinition:
        return self._tools[name]


registry = ToolRegistry()
