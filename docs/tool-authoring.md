# Tool authoring

## Define a tool

1. Subclass `ToolDefinition` in `core/tools/definitions/`.
2. Set `name`, `description`, optional `requires_approval`, `risk`, `max_retries`, `retry_delay_seconds`.
3. Implement `async def run(self, ctx: ToolContext, args: dict) -> ToolExecutionResult`.
4. Register the class in `core/tools/definitions/__init__.py` (`BUILTIN_TOOL_CLASSES`).

## Policy

Rows in `tool_policies` (seeded from registry on startup) override defaults. Update at runtime via `PUT /api/tools/meta/policies/{tool_name}`.

## Permissions

Use `core.tools.permissions.checks.tool_requires_approval(name)` for gating logic; dispatcher enforces approval + persistence.

## Artifacts

Return `ToolExecutionResult(artifacts=[{kind, name, mime_type, content, metadata}])`; dispatcher writes files and emits `artifact.created` events.
