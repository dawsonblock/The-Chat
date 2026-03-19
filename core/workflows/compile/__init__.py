"""Workflow compile/validate expansion (v0.9+).

`compile_workflow_spec` is a hook for graph normalization before persistence.
Execution remains in `core.runtime.execution.workflow_run`.
"""

from __future__ import annotations

from typing import Any


def compile_workflow_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow-normalized spec (ordering, ids). Full DAG compile lands in v0.9+."""
    nodes = list(spec.get('nodes') or [])
    return {**spec, 'nodes': nodes}
