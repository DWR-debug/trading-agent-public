import json
from pathlib import Path


def test_q017_design_contains_three_unranked_orthogonal_candidates():
    path = Path(__file__).parents[1] / "research" / "preregistrations" / "q017_orthogonal_hypothesis_design_round_2026_09_25.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["status"] == "DESIGN_ONLY"
    candidates = payload["candidates"]
    assert len(candidates) >= 3
    assert [item["id"] for item in candidates] == ["A", "B", "C"]
    assert len({item["family"] for item in candidates}) == len(candidates)
    assert payload["governance"]["no_holdout_selection"] is True
    assert payload["governance"]["no_parameter_search"] is True
    assert payload["governance"]["fresh_symbol_disjoint_validation"] is True
    assert payload["governance"]["performance_trial_authorized"] is False
    assert payload["governance"]["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def test_q017_is_design_only_and_not_promoted():
    path = Path(__file__).parents[1] / "research" / "preregistrations" / "q017_orthogonal_hypothesis_design_round_2026_09_25.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == "DESIGN_ONLY"
    assert payload["governance"]["performance_trial_authorized"] is False
    assert payload["interpretation"].startswith("Candidates are not ranked")

