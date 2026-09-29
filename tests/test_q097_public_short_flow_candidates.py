from __future__ import annotations

import json
from pathlib import Path


def test_q097_registry_is_design_only_and_unranked() -> None:
    p = json.loads(Path('research/frontier/q097_public_short_flow_candidates.json').read_text(encoding='utf-8'))
    assert p['status'] == 'DESIGN_ONLY_UNRANKED'
    assert p['performance_authorized'] is False
    assert len(p['candidates']) == 4
    assert {row['id'] for row in p['candidates']} == {'Q097:I15', 'Q097:I16', 'Q097:I17', 'Q097:I18'}


def test_q097_safety_and_governance_are_fail_closed() -> None:
    p = json.loads(Path('research/frontier/q097_public_short_flow_candidates.json').read_text(encoding='utf-8'))
    g = p['governance']
    assert all(g.values())
    assert p['safety'] == {
        'paper_only': True,
        'live_trading_enabled': False,
        'orders_enabled': False,
        'automatic_promotion': False,
    }
