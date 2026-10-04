from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_q179_q184_inventory_is_design_only_and_schema_complete():
    data=json.loads((ROOT/"research/frontier/q179_q184_candidate_wave_2026_10_04.json").read_text(encoding="utf-8"))
    assert data["status"]=="DESIGN_INVENTORY_ONLY"
    assert len(data["candidates"])==6
    for c in data["candidates"]:
        assert all(c.get(k) for k in ("id","name","hypothesis","construction","sources","next_gate"))
        assert "performance" not in c and "promotion" not in c
    assert data["policy"]["performance_authorized"] is False
    assert data["safety"]["automatic_promotion"] is False

def test_q179_q184_source_feasibility_is_non_authorizing():
    text=(ROOT/"automation/q179_q184_source_feasibility.py").read_text(encoding="utf-8")
    for marker in ("DISCOVERY_SOURCE_FEASIBILITY_COMPLETED","future_row_prefix_invariant","performance","holdout_selection","parameter_search","candidate_results","live_execution","automatic_promotion"):
        assert marker in text

def test_q179_q184_workflow_is_hosted_and_separate_from_formal_performance():
    text=(ROOT/".github/workflows/q179-q184-source-feasibility.yml").read_text(encoding="utf-8")
    assert "runs-on: ubuntu-24.04" in text
    assert 'cron: "23 */1 * * *"' in text
    assert "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED" in text
    assert "automatic_promotion" in text
