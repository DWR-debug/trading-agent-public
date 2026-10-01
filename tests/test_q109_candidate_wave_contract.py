from __future__ import annotations
import json
from pathlib import Path
from automation.q109_candidate_wave_contract import validate

def test_q109_design_contract():
    root = Path(__file__).parents[1]
    data = json.loads((root/"research/frontier/q109_candidate_wave_2026_10_01.json").read_text(encoding="utf-8"))
    result = validate(data)
    assert result["status"] == "DESIGN_CONTRACT_VALIDATED"
    assert result["candidate_count"] == 6
    assert result["governance"]["performance_authorized"] is False
    assert result["safety"]["paper_only"] is True
