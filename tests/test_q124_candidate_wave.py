import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_q124_is_design_only_and_explicitly_separates_options_proxy_from_paper_measure():
    payload = json.loads(
        (ROOT / "research/frontier/q124_candidate_wave_2026_10_02.json").read_text(encoding="utf-8")
    )
    assert payload["status"] == "DESIGN_INVENTORY_ONLY"
    assert len(payload["candidates"]) == 2
    assert all(c["performance_authorized"] is False for c in payload["candidates"])
    options = next(c for c in payload["candidates"] if c["id"] == "Q124:O26")
    assert "must not be represented as the signed options order-imbalance construct" in " ".join(
        payload["notes"] + [options["construction"]]
    )


def test_q124_keeps_security_and_governance_bounds_closed():
    payload = json.loads(
        (ROOT / "research/frontier/q124_candidate_wave_2026_10_02.json").read_text(encoding="utf-8")
    )
    assert payload["policy"]["performance_authorized"] is False
    assert payload["policy"]["holdout_selection_allowed"] is False
    assert payload["policy"]["parameter_search_allowed"] is False
    assert payload["safety"]["paper_only"] is True
    assert payload["safety"]["live_trading_enabled"] is False
