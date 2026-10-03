import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_q147_q148_eia_contract_is_pit_only():
    data=json.loads((ROOT/"research/governance/q147_q148_eia_source_clock_contract_2026_10_03.json").read_text(encoding="utf-8"))
    assert data["state"]=="PIT_CONTRACT_DEFINED_PENDING_SERIES_FREEZE"
    assert data["scientific_boundary"]["performance"] is False
    assert data["scientific_boundary"]["candidate_ranking"] is False
    assert data["scientific_boundary"]["live_execution"] is False
    assert data["safety"]=={"PAPER_ONLY":True,"LIVE_TRADING_ENABLED":False,"ORDERS_ENABLED":False,"AUTOMATIC_PROMOTION":False}

def test_q147_q148_contract_rejects_current_api_as_sole_pit_source():
    text=(ROOT/"docs/research_design/Q147_Q148_EIA_SOURCE_CLOCK_CONTRACT_2026-10-03.md").read_text(encoding="utf-8").lower()
    assert "continuously updated" in text
    assert "not accepted as the sole historical pit source" in text
    assert "revision/correction lineage" in text