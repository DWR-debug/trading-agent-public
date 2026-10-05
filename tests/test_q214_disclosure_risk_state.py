import json
from pathlib import Path


def test_q214_is_risk_only_and_non_authorizing():
    d=json.loads(Path('research/frontier/q214_disclosure_risk_state_2026_10_05.json').read_text(encoding='utf-8'))
    c=d['candidates'][0]
    assert c['id']=='Q214'
    assert c['risk_state_only'] is True
    assert c['performance_authorization_allowed'] is False
    assert c['scientific_boundary']=='discovery_contract_only'
    assert 'Q088' in c['non_overlap']
