from __future__ import annotations

from typing import Any


def validate_workflow_spec(spec: dict[str, Any], tool_names: set[str]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(spec, dict):
        errors.append('Workflow spec must be an object.')
        return {'ok': False, 'errors': errors, 'warnings': warnings}
    nodes = spec.get('nodes') or []
    if not isinstance(nodes, list) or not nodes:
        errors.append('Workflow must contain at least one node.')
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f'Node {i} must be an object.')
            continue
        kind = node.get('kind')
        if kind == 'tool' and node.get('type') not in tool_names:
            errors.append(f"Unknown tool: {node.get('type')}")
        elif kind == 'condition':
            if 'expression' not in node and 'config' not in node:
                warnings.append(f'Node {i} condition has no expression/config (execution stub until v0.9+).')
        elif kind == 'loop':
            if not node.get('config', {}).get('max_iterations'):
                warnings.append(f'Node {i} loop should set config.max_iterations for safety.')
        elif kind == 'output':
            pass
        elif kind not in {'tool', 'output', 'condition', 'loop'}:
            warnings.append(f'Unknown node kind {kind!r} at index {i} (may be ignored by executor).')
    return {'ok': not errors, 'errors': errors, 'warnings': warnings}
