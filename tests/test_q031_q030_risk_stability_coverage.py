from __future__ import annotations

import json
from pathlib import Path

from research.asset_universes import get_universe

def test_q031_universe_is_fixed() -> None:
    universe = get_universe("validation_2026_09_27_q030_risk_stability_coverage")
    assert universe.symbols == ("BSV", "FAN", "JNK", "UDN", "VCLT", "VGIT", "SCHR")
    assert universe.interval == "1d"
    assert universe.target_count == 3500


def test_q031_preregistration_is_coverage_only() -> None:
    prereg = json.loads(Path("research/preregistrations/q031_q030_risk_stability_coverage_2026_09_27.json").read_text(encoding="utf-8"))
    assert prereg["status"] == "PREREGISTERED_COVERAGE_ONLY"
    assert prereg["governance"]["coverage_only"] is True
    assert prereg["governance"]["performance_evaluation"] is False
    assert prereg["governance"]["holdout_used_for_selection"] is False
    assert prereg["governance"]["asset_search"] is False
    assert prereg["governance"]["parameter_search"] is False
    assert prereg["safety"] == {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False}
