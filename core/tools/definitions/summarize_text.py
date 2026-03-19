from __future__ import annotations

from core.runtime.provider import provider
from core.tools.base import ToolContext, ToolDefinition, ToolExecutionResult


class SummarizeTextTool(ToolDefinition):
    name = 'summarize_text'
    description = 'Summarize a block of text.'
    timeout_seconds = 240.0

    def validate_args(self, args: dict) -> str | None:
        text = (args.get('text') or '').strip()
        return None if text else 'No text was provided.'

    async def run(self, ctx: ToolContext, args: dict) -> ToolExecutionResult:
        text = (args.get('text') or '').strip()
        summary = await provider.generate(text)
        return ToolExecutionResult(ok=True, output={'summary': summary})
