import json
from pathlib import Path

from config import settings
from research.asset_universes import get_universe

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research" / "preregistrations" / "q022_h2_treasury_release_timing_2026_09_27.json"


def _prereg() -> dict:
    return json.loads(PREREG.read_text(encoding="utf-8"))


def test_q022_h2_preregistration_is_fixed_and_safe() -> None:
    prereg = _prereg()
    assert prereg["status"] == "PREREGISTERED_DESIGN_ONLY"
    assert prereg["trial_id"] == "T-2026-09-27-048"
    assert prereg["research_family"] == "official_event_alpha_release_timing"
    assert prereg["data_contract"]["requested_raw_candles_per_symbol"] == 3520
    assert prereg["data_contract"]["target_common_calendar"] == 3500
    assert prereg["trading_rule"]["intervention"] == (
        "Only change versus Q020/Q022-H1 is the event-date mapping "
        "from record_date to auction_date; signal sign and all other "
        "trading rules remain unchanged."
    )
    assert prereg["authorization"]["performance_trial_authorized"] is False
    assert prereg["selection"]["performance_selection"] is False
    assert prereg["selection"]["holdout_used_for_selection"] is False
    assert prereg["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    assert settings.PAPER_ONLY is True
    assert settings.LIVE_TRADING_ENABLED is False
    assert settings.ORDERS_ENABLED is False


def test_q022_h2_universe_matches_preregistration() -> None:
    prereg = _prereg()
    universe = get_universe(prereg["universe"])
    assert tuple(universe.symbols) == tuple(prereg["symbols"])
    assert tuple(prereg["symbols"]) == ("BSV", "FAN", "JNK", "UDN", "VCLT", "VGIT")
    assert len(set(universe.symbols)) == 6
    assert universe.target_count >= prereg["data_contract"]["requested_raw_candles_per_symbol"]


def test_q022_h2_timing_provenance_is_q025_date_validated() -> None:
    prereg = _prereg()
    timing = prereg["event_source"]["timing_basis"]
    assert timing["q025_workflow_run_id"] == 36310848531
    assert timing["q025_artifact_id"] == 10928822681
    assert timing["rule"].endswith(
        "first XNYS session strictly after auction_date."
    )
