from __future__ import annotations

import json

from core.tools.base import ToolContext, ToolDefinition, ToolExecutionResult
from intake.crawl import crawl_site


class CrawlSiteTool(ToolDefinition):
    name = 'crawl_site'
    description = 'Shallow crawl a site starting from one URL.'
    requires_approval = True
    risk = 'medium'
    max_retries = 1
    timeout_seconds = 300.0

    def validate_args(self, args: dict) -> str | None:
        url = (args.get('url') or '').strip()
        return None if url else 'No URL was provided.'

    async def run(self, ctx: ToolContext, args: dict) -> ToolExecutionResult:
        url = (args.get('url') or '').strip()
        result = await crawl_site(url, max_depth=int(args.get('max_depth', 1)), max_pages=int(args.get('max_pages', 5)))
        artifacts = [
            {
                'kind': 'json',
                'name': f'Crawl manifest for {url}',
                'mime_type': 'application/json',
                'content': json.dumps(result, indent=2),
                'metadata': {'start_url': url, 'job_id': result['job_id']},
            }
        ]
        return ToolExecutionResult(ok=True, output=result, artifacts=artifacts)
