from __future__ import annotations
import json
from pathlib import Path
from automation.candidate_robustness_gate import REQUIRED_FIELDS, DEFAULT_INVENTORIES
ROOT = Path(__file__).resolve().parents[1]

def test_all_default_candidate_inventories_match_gate_schema():
    assert len(DEFAULT_INVENTORIES) == 10
    candidates=[]
    for rel in DEFAULT_INVENTORIES:
        data=json.loads((ROOT/rel).read_text(encoding="utf-8"))
        assert data["status"]=="DESIGN_INVENTORY_ONLY"
        for c in data["candidates"]:
            missing=sorted(set(REQUIRED_FIELDS)-set(c))
            assert not missing,(c["id"],missing)
            assert "core_hypothesis" not in c,c["id"]
            candidates.append(c)
    assert len(candidates)==73
    assert len({c["id"] for c in candidates})==73

def test_frontier_candidate_contract_contains_no_authorizing_fields():
    forbidden={"performance","return","returns","pnl","drawdown","winner","selected","promotion","parameter_search","threshold_search","horizon_search","asset_search","candidate_selection","family_ranking"}
    for rel in DEFAULT_INVENTORIES:
        data=json.loads((ROOT/rel).read_text(encoding="utf-8"))
        for c in data["candidates"]:
            assert not forbidden.intersection(c),c["id"]
            assert c["sources"] and c["next_gate"] and c["hypothesis"] and c["construction"]
