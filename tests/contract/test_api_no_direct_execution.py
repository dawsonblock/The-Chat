from __future__ import annotations

import ast
from pathlib import Path


def _under(prefix: str, module: str) -> bool:
    return module == prefix or module.startswith(prefix + '.')


def _api_py_files() -> list[Path]:
    root = Path(__file__).resolve().parents[2] / 'api'
    return sorted(p for p in root.rglob('*.py') if p.is_file())


def _violations_in_tree(tree: ast.AST, path: Path) -> list[str]:
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if _under('core.runtime.execution', name):
                    bad.append(f'{path}: import {name}')
                if _under('core.tools.dispatcher', name):
                    bad.append(f'{path}: import {name}')
                if _under('core.runtime.engine', name):
                    bad.append(f'{path}: import {name}')
        elif isinstance(node, ast.ImportFrom):
            mod = node.module
            if mod is None:
                continue
            names = {a.name for a in node.names}
            if _under('core.runtime.execution', mod):
                bad.append(f'{path}: from {mod} import {sorted(names)}')
            if _under('core.tools.dispatcher', mod):
                bad.append(f'{path}: from {mod} import {sorted(names)}')
            if _under('core.runtime.engine', mod):
                bad.append(f'{path}: from {mod} import {sorted(names)}')
            if _under('core.runtime.executor', mod):
                forbidden = names & {'execute_chat_run', 'execute_workflow_run', 'RuntimeEngine'}
                if forbidden:
                    bad.append(f'{path}: from {mod} import {sorted(forbidden)}')
    return bad


def test_api_has_no_direct_runtime_execution_imports():
    """HTTP layer must not start runs inline; use run_service + worker → RuntimeEngine."""
    all_v: list[str] = []
    for path in _api_py_files():
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        all_v.extend(_violations_in_tree(tree, path))
    assert not all_v, 'Forbidden imports under api/:\n' + '\n'.join(all_v)
