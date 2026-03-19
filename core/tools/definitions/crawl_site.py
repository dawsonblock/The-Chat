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

    async def run(self, ctx: ToolContext, args: dict) -> ToolExecutionResult:
        url = (args.get('url') or '').strip()
        if not url:
            return ToolExecutionResult(ok=False, error_code='missing_url', error_message='No URL was provided.')
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
