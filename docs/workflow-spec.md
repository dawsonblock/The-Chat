# WorkflowSpec

Workflows are JSON stored on `WorkflowVersion.spec` and validated by `core/workflows/spec.validate_workflow_spec`.

## Shape (minimal)

```json
{
  "name": "My workflow",
  "nodes": [
    { "id": "n1", "kind": "tool", "type": "extract_page", "config": { "url": "{{input.url}}" } },
    { "id": "out", "kind": "output", "config": { "text": "{{last.summary}}" } }
  ]
}
```

## Node kinds

- **tool** — `type` must be a registered tool name; `config` is tool args with `{{input.x}}` / `{{last.x}}` placeholders.
- **output** — final text template.
- **condition** / **loop** — validated with warnings until full execution lands in v0.9+.

## Registration

`POST /api/workflows/register` runs validation + `compile_workflow_spec` (shallow normalize). Execution is **only** via queued `kind=workflow` runs and `execute_workflow_run`.
