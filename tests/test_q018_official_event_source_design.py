import json
from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_q018_design_has_three_unranked_official_source_candidates():
    payload = json.loads((ROOT / "research" / "preregistrations" / "q018_official_event_source_design_round_2026_09_26.json").read_text(encoding="utf-8"))
    assert payload["task_id"] == "Q-018-ORTHOGONAL-OFFICIAL-EVENT-SOURCE-DESIGN"
    assert payload["status"] == "DESIGN_ONLY"
    assert [item["id"] for item in payload["candidates"]] == ["A", "B", "C"]
    assert payload["governance"]["candidates_unranked"] is True
    assert payload["governance"]["performance_trial_authorized"] is False

def test_q018_universe_is_fixed_and_symbol_disjoint():
    from research.asset_universes import get_universe, list_universes
    universe = get_universe("q018_official_event_source_validation")
    assert universe.symbols == ("UNH", "UPS", "FDX", "DIS", "ADP", "BKNG", "ORLY", "AZO", "TJX", "RSG", "WM", "EOG")
    used_elsewhere = {symbol for item in list_universes() if item.name != universe.name for symbol in item.symbols}
    assert not (set(universe.symbols) & used_elsewhere)
    assert universe.target_count == 3520

def test_q018_safety_is_unchanged():
    payload = json.loads((ROOT / "research" / "preregistrations" / "q018_official_event_source_design_round_2026_09_26.json").read_text(encoding="utf-8"))
    assert payload["safety"] == {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False}
