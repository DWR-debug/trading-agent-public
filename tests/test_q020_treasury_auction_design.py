import json
from pathlib import Path

from research.asset_universes import get_universe, list_universes

ROOT = Path(__file__).resolve().parents[1]


def test_q020_preregistration_is_fixed_and_performance_locked():
    spec = json.loads(
        (ROOT / "research" / "preregistrations" / "q020_treasury_auction_performance_2026_09_26.json").read_text(
            encoding="utf-8"
        )
    )
    assert spec["status"] == "PREREGISTERED_DESIGN_ONLY"
    assert spec["event_source"]["fixed_signal"].startswith(
        "Signed change in bid-to-cover ratio"
    )
    assert spec["trading_rule"]["exposure"].endswith("outside event sessions exposure is zero.")
    assert spec["trading_rule"]["sizing"].endswith("no leverage.")
    assert spec["authorization"]["performance_trial_authorized"] is False
    assert spec["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def test_q020_universe_is_fresh_and_exact():
    symbols = ("ACN","AMT","APD","BK","CME","CTAS","GPC","LLY","MCO","NOC","ROST","SHW")
    universe = get_universe("validation_2026_09_26_treasury_auction_performance")
    assert universe.symbols == symbols
    assert universe.target_count == 3520
    expected = set(symbols)
    for existing in list_universes():
        if existing.name == universe.name:
            continue
        if existing.name == "validation_2026_09_26_treasury_auction_performance_repair":
            continue
        assert not expected.intersection(existing.symbols), existing.name


def test_q020_repair_declares_acquisition_headroom_and_window_minimum_separately():
    spec = json.loads(
        (
            ROOT
            / "research"
            / "preregistrations"
            / "q020_treasury_auction_coverage_repair_2026_09_26.json"
        ).read_text(encoding="utf-8")
    )
    assert spec["requested_candles"] == 4000
    assert spec["minimum_in_window_candles"] == 3500
    assert spec["target_candles"] == 3500
    assert spec["repair_change"]["minimum_required_in_window_candles"] == 3500
    assert spec["governance"]["performance_execution"] is False
