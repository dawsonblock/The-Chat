from __future__ import annotations

from core.runtime.provider import provider
from core.tools.base import ToolContext, ToolDefinition, ToolExecutionResult


class SummarizeTextTool(ToolDefinition):
    name = 'summarize_text'
    description = 'Summarize a block of text.'

    async def run(self, ctx: ToolContext, args: dict) -> ToolExecutionResult:
        text = (args.get('text') or '').strip()
        if not text:
            return ToolExecutionResult(ok=False, error_code='no_text', error_message='No text was provided.')
        summary = await provider.generate(text)
        return ToolExecutionResult(ok=True, output={'summary': summary})
