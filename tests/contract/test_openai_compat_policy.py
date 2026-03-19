from __future__ import annotations

from pathlib import Path


def test_baseline_documents_openai_v1_bypass_policy():
    root = Path(__file__).resolve().parents[2]
    text = (root / 'docs' / 'baseline.md').read_text(encoding='utf-8')
    assert 'Option A' in text or 'compatibility bypass' in text or 'OPENWEBUI_SYNTHETIC_RUNS' in text
    assert '/v1/chat/completions' in text
