import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_q125_sec_midas_is_design_only_and_lag_aware():
    payload = json.loads(
        (ROOT / "research/frontier/q125_candidate_wave_2026_10_02.json").read_text(encoding="utf-8")
    )
    candidate = payload["candidates"][0]
    assert payload["status"] == "DESIGN_INVENTORY_ONLY"
    assert candidate["id"] == "Q125:M1"
    assert candidate["performance_authorized"] is False
    assert "historical publication-lag" in candidate["next_gate"]
    assert any("3-4 week lag" in note for note in payload["notes"])
