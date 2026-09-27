import json
from pathlib import Path

from research.asset_universes import get_universe


def test_t050_matches_fixed_discovery_batch_and_is_disjoint_from_t049():
    spec = json.loads(Path("research/preregistrations/trial_050_fixed_candidate_batch_02_coverage_2026_09_27.json").read_text(encoding="utf-8"))
    universe = get_universe(spec["universe"])
    assert tuple(universe.symbols) == tuple(spec["symbols"])
    assert universe.target_count == 3520
    assert tuple(spec["symbols"]) == ("PRU","ALL","TRV","AFL","AIZ","CB","HIG","CINF","GL","MKC","ED","PEG")
    assert set(spec["symbols"]).isdisjoint(get_universe("validation_2026_09_27_fixed_candidate_batch").symbols)
    assert spec["source_discovery"]["performance_used_for_selection"] is False
    assert spec["source_discovery"]["holdout_used_for_selection"] is False
    assert spec["governance"]["performance_trial_authorized"] is False
    assert spec["safety"]["paper_only"] is True
    assert spec["safety"]["live_trading_enabled"] is False
    assert spec["safety"]["orders_enabled"] is False
    assert spec["safety"]["automatic_promotion"] is False
