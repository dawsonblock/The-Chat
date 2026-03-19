from __future__ import annotations

from core.tools.base import ToolContext, ToolDefinition, ToolExecutionResult
from intake.extract import extract_page
from intake.extract.fetch import SSRFBlocked


class ExtractPageTool(ToolDefinition):
    name = 'extract_page'
    description = 'Fetch and normalize a public web page.'
    max_retries = 2
    retry_delay_seconds = 0.75
    timeout_seconds = 120.0

    def validate_args(self, args: dict) -> str | None:
        url = (args.get('url') or '').strip()
        return None if url else 'No URL was provided.'

    async def run(self, ctx: ToolContext, args: dict) -> ToolExecutionResult:
        url = (args.get('url') or '').strip()
        try:
            doc = await extract_page(url, render_js=bool(args.get('render_js', False)), include_html=True)
        except SSRFBlocked as exc:
            return ToolExecutionResult(ok=False, error_code='ssrf_blocked', error_message=str(exc), failure_class='user_error', retryable=False)
        except NotImplementedError as exc:
            return ToolExecutionResult(ok=False, error_code='not_supported', error_message=str(exc), failure_class='user_error', retryable=False)
        artifacts = [
            {
                'kind': 'text',
                'name': f'Extracted text for {doc.title or doc.source_url}',
                'mime_type': 'text/plain',
                'content': doc.text_content,
                'metadata': {'source_url': doc.source_url, 'content_hash': doc.content_hash},
            }
        ]
        if doc.html_content:
            artifacts.append(
                {
                    'kind': 'html',
                    'name': f'Raw HTML for {doc.title or doc.source_url}',
                    'mime_type': 'text/html',
                    'content': doc.html_content,
                    'metadata': {'source_url': doc.source_url},
                }
            )
        return ToolExecutionResult(
            ok=True,
            output={
                'title': doc.title,
                'source_url': doc.source_url,
                'final_url': doc.final_url,
                'text_content': doc.text_content,
                'link_count': len(doc.links),
                'links': doc.links[:25],
                'content_hash': doc.content_hash,
            },
            artifacts=artifacts,
        )
