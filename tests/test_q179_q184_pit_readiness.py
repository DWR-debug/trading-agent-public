from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_q179_q184_pit_r1_is_non_authorizing():
    text=(ROOT/"automation/q179_q184_pit_readiness.py").read_text(encoding="utf-8")
    assert "PIT_READINESS_R1_COMPLETED_NO_PERFORMANCE" in text
    for key in ("performance","holdout_selection","parameter_search","threshold_search","horizon_search","candidate_ranking","promotion","live_execution"):
        assert key in text
    assert "RUNNER_ACCESS_BLOCKED" in text

def test_q179_q184_pit_r1_inventory_contracts_present():
    text=(ROOT/"automation/q179_q184_pit_readiness.py").read_text(encoding="utf-8")
    for cid in ("Q179","Q180","Q181","Q182","Q183","Q184"):
        assert f'"{cid}"' in text
    data=json.loads((ROOT/"research/frontier/q179_q184_candidate_wave_2026_10_04.json").read_text(encoding="utf-8"))
    assert len(data["candidates"])==6
    for c in data["candidates"]:
        assert all(c.get(k) for k in ("id","name","hypothesis","construction","sources","next_gate"))

def test_q179_q184_pit_workflow_is_hosted_and_bounded():
    text=(ROOT/".github/workflows/q179-q184-pit-readiness.yml").read_text(encoding="utf-8")
    assert "runs-on: ubuntu-24.04" in text
    assert "PIT_READINESS_R1_COMPLETED_NO_PERFORMANCE" in text
    assert "AUTOMATIC_PROMOTION" in text
