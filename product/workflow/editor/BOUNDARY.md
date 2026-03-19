# Flowgram editor boundary (v0.8 Pass 5)

Mount Flowgram-derived graph UI here. Serialization must compile to the JSON shape validated by `validate_workflow_spec` in `core/workflows/spec.py`.

Forbidden:

- A second workflow runner or persistence layer
- Flowgram auth/session/globals

Allowed:

- Canvas, inspector, layout, export to `WorkflowSpec`
- Visual overlays driven by `run_events` from the host API
