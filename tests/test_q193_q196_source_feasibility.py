from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_inventory_is_design_only_and_non_authorizing():
    d=json.loads((ROOT/'research/frontier/q193_q196_candidate_wave_2026_10_04.json').read_text(encoding='utf-8'))
    assert d['status']=='DESIGN_INVENTORY_ONLY'
    assert {x['id'] for x in d['candidates']}=={'Q193','Q194','Q195','Q196'}
    assert d['policy']['performance_authorized'] is False
    assert d['policy']['family_ranking_allowed'] is False
    assert d['safety']['paper_only'] is True

def test_q193_is_dependency_gated():
    d=json.loads((ROOT/'research/frontier/q193_q196_candidate_wave_2026_10_04.json').read_text(encoding='utf-8'))
    q=next(x for x in d['candidates'] if x['id']=='Q193')
    assert q['priority']=='C_GATED'
    assert q['robustness_contract']['no_composition_before_component_pit'] is True

def test_source_gate_has_no_performance_inputs():
    s=(ROOT/'automation/q193_q196_source_feasibility.py').read_text(encoding='utf-8')
    for marker in ('DISCOVERY_SOURCE_FEASIBILITY_COMPLETED','performance','holdout_selection','parameter_search','DEPENDENCY_PIT_GATED','live_execution'): assert marker in s

def test_workflow_is_hosted_and_bounded():
    s=(ROOT/'.github/workflows/q193-q196-source-feasibility.yml').read_text(encoding='utf-8')
    assert 'runs-on: ubuntu-24.04' in s
    assert 'automatic_promotion' in s and 'holdout_selection' in s
    assert 'DEPENDENCY_PIT_GATED' in s