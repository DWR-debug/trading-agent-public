import json
from pathlib import Path

from config import settings
from research.asset_universes import get_universe


ROOT = Path(__file__).resolve().parents[1]


def _preregistration() -> dict:
    return json.loads(
        (
            ROOT
            / "research"
            / "preregistrations"
            / "q022_h1_directional_inversion_performance_2026_09_26.json"
        ).read_text(encoding="utf-8")
    )


def test_q022_h1_preregistration_is_fixed_and_safe() -> None:
    prereg = _preregistration()
    assert prereg["status"] == "PREREGISTERED_DESIGN_ONLY"
    assert prereg["trial_id"] == "T-2026-09-26-047"
    assert prereg["universe"] == "validation_2026_09_26_treasury_auction_directional_inversion"
    assert prereg["selection"]["parameter_search"] is False
    assert prereg["selection"]["holdout_used_for_selection"] is False
    assert prereg["trading_rule"]["no_other_changes"] is True
    assert prereg["authorization"]["performance_trial_authorized"] is False
    assert prereg["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    assert settings.PAPER_ONLY is True
    assert settings.LIVE_TRADING_ENABLED is False
    assert settings.ORDERS_ENABLED is False
    assert settings.AUTOMATIC_PROMOTION is False


def test_q022_h1_universe_matches_preregistration_and_has_no_duplicate_symbols() -> None:
    prereg = _preregistration()
    universe = get_universe(prereg["universe"])
    assert tuple(universe.symbols) == tuple(prereg["symbols"])
    assert len(universe.symbols) == 12
    assert len(set(universe.symbols)) == 12
    assert universe.target_count == 3520


def test_q022_h1_coverage_authorization_is_not_performance_authorization() -> None:
    auth = json.loads(
        (
            ROOT
            / "research"
            / "authorizations"
            / "q022_h1_directional_inversion_coverage_2026_09_26.json"
        ).read_text(encoding="utf-8")
    )
    assert auth["authorized"] is True
    assert auth["coverage_execution_authorized"] is True
    assert auth["performance_execution_authorized"] is False
    assert auth["execution_scope"] == "COVERAGE_ONLY"
