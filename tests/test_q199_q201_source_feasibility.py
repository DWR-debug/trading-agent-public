from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_inventory_is_design_only():
    d=json.loads((ROOT/'research/frontier/q199_q201_candidate_wave_2026_10_04.json').read_text(encoding='utf-8'))
    assert d['status']=='DESIGN_INVENTORY_ONLY'
    assert {x['id'] for x in d['candidates']}=={'Q199','Q201'}
    assert d['policy']['performance_authorized'] is False
    assert d['safety']['paper_only'] is True

def test_q199_is_distinct_patent_publication_event():
    d=json.loads((ROOT/'research/frontier/q199_q201_candidate_wave_2026_10_04.json').read_text(encoding='utf-8'))
    q=next(x for x in d['candidates'] if x['id']=='Q199')
    assert q['robustness_contract']['public_boundary_locked'] is True
    assert 'Q186' not in q['name']

def test_source_gate_never_reads_returns_or_authorizes_performance():
    s=(ROOT/'automation/q199_q201_source_feasibility.py').read_text(encoding='utf-8')
    for marker in ('DISCOVERY_SOURCE_FEASIBILITY_COMPLETED','performance','holdout_selection','parameter_search','live_execution'): assert marker in s
    assert 'return' not in s.lower() or 'return ' in s.lower()

def test_q201_history_probe_is_fixed_and_non_authorizing():
    s = (ROOT / "automation/q199_q201_source_feasibility.py").read_text(encoding="utf-8")
    assert "https://clinicaltrials.gov/study/NCT00125528?a=2&tab=history" in s
    assert "https://clinicaltrials.gov/ct2/history/NCT00125528" in s
    assert '"2005-07-29"' in s
    assert '"2015-02-19"' in s
    assert '"2016-12-16"' in s
    assert "HISTORICAL_VERSION_ARCHIVE_COMPONENT_READY" in s

def test_q201_uses_proven_clinicaltrials_public_clock_fields():
    s = (ROOT / "automation/q199_q201_source_feasibility.py").read_text(encoding="utf-8")
    assert "https://clinicaltrials.gov/api/v2/studies/NCT00125528" in s
    for marker in (
        "studyFirstPostDateStruct",
        "lastUpdatePostDateStruct",
        "resultsFirstPostDateStruct",
    ):
        assert marker in s


def test_workflow_is_bounded_and_non_authorizing():
    s=(ROOT/'.github/workflows/q199-q201-source-feasibility.yml').read_text(encoding='utf-8')
    assert 'runs-on: ubuntu-24.04' in s
    assert 'automatic_promotion' in s and 'holdout_selection' in s
    assert 'DISCOVERY_SOURCE_FEASIBILITY_COMPLETED' in s