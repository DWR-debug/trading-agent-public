from pathlib import Path
import json

ROOT=Path(__file__).parents[1]

def test_q218_replication_contract_is_frozen_and_disjoint():
    p=ROOT/"research/governance/q218_independent_replication_contract_2026_10_08.json"
    d=json.loads(p.read_text(encoding="utf-8"))
    assert d["status"]=="FROZEN_REPLICATION_CONTRACT"
    assert d["fresh_symbol_disjoint"] is True
    assert set(d["issuers"])=={"GOOGL","META","ORCL","PFE"}
    assert d["parent_trial_id"]=="T-2026-10-08-Q218-PERFORMANCE-01"
    assert d["independence_boundary"]["performance_output_reuse_for_rule_changes"] is False
    assert d["independence_boundary"]["post_pass_optimization"] is False

def test_q218_replication_implementation_is_separate():
    p=(ROOT/"automation/q218_independent_replication.py").read_text(encoding="utf-8")
    assert "q218_sec_multichannel_source_gate" not in p
    assert "q218_sec_event_pair_lineage_gate" not in p
    assert "q218_deterministic_performance_executor" not in p
    assert "GOOGL" in p and "META" in p and "ORCL" in p and "PFE" in p
