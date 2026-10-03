import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_q144_page_map_is_fixed_to_q107_universe():
    data=json.loads((ROOT/"research/governance/q144_q107_wikipedia_page_map_2026_10_03.json").read_text(encoding="utf-8"))
    assert data["universe_fingerprint"]=="18571a7871f72b8018905c10c289724bb5cf976ab7fa4f9f424599ddc727fbd2"
    assert [x["symbol"] for x in data["symbols"]]==["SPGI","NDAQ","AMP","RJF","WMB","VLO","DVN","EMN"]
    assert data["freeze_policy"]["page_title_is_frozen"] is True

def test_q137_q144_micro_pit_is_non_performance():
    text=(ROOT/"automation/q137_q144_micro_pit.py").read_text(encoding="utf-8")
    for marker in ('"performance":False','"holdout_selection":False','"candidate_ranking":False','"parameter_search":False','"live_execution":False'):
        assert marker in text

def test_q137_q144_micro_pit_has_no_search_or_return_metrics():
    text=(ROOT/"automation/q137_q144_micro_pit.py").read_text(encoding="utf-8").lower()
    for marker in ("sharpe","profit factor","grid search","threshold sweep","holdout ranking"):
        assert marker not in text

def test_q144_uses_fixed_wikimedia_endpoint_contract():
    text=(ROOT/"automation/q137_q144_micro_pit.py").read_text(encoding="utf-8")
    assert "all-access/all-agents" in text
    assert "2025082500/2025092500" in text