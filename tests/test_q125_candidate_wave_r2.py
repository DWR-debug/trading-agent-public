import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_q125_r2_is_release_clock_and_round_lot_aware():
    payload = json.loads(
        (ROOT / "research" / "frontier" / "q125_candidate_wave_2026_10_02_r2.json").read_text(encoding="utf-8")
    )
    candidate = payload["candidates"][0]
    assert payload["status"] == "DESIGN_INVENTORY_ONLY"
    assert candidate["id"] == "Q125:M1"
    assert candidate["performance_authorized"] is False
    assert "publication-clock" in candidate["next_gate"]
    assert any("November 3, 2025" in note for note in payload["notes"])
    assert "release_clock" in candidate["construction"]


