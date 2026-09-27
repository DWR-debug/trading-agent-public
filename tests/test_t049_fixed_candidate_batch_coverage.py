from research.asset_universes import get_universe, list_universes


def test_t049_preregistration_matches_fixed_discovered_batch_and_is_coverage_only():
    import json
    from pathlib import Path

    path = Path("research/preregistrations/trial_049_fixed_candidate_batch_coverage_2026_09_27.json")
    spec = json.loads(path.read_text(encoding="utf-8"))
    symbols = tuple(spec["symbols"])
    universe = get_universe(spec["universe"])
    assert universe.symbols == symbols
    assert universe.target_count == spec["requested_candles"] == 3520
    assert spec["target_candles"] == 3500
    assert spec["minimum_in_window_candles"] == 3500
    assert spec["source_discovery"]["performance_used_for_selection"] is False
    assert spec["source_discovery"]["holdout_used_for_selection"] is False
    assert spec["governance"]["performance_evaluation"] is False
    assert spec["governance"]["holdout_evaluation"] is False
    assert spec["governance"]["asset_selection_by_performance"] is False
    assert spec["governance"]["performance_trial_authorized"] is False
    assert spec["safety"]["paper_only"] is True
    assert spec["safety"]["live_trading_enabled"] is False
    assert spec["safety"]["orders_enabled"] is False
    assert spec["safety"]["automatic_promotion"] is False

    for other in list_universes():
        if other.name == universe.name:
            continue
        assert not set(symbols).intersection(other.symbols), other.name
