from __future__ import annotations

import json
from pathlib import Path

from research.asset_universes import get_universe, list_universes


def test_q107_universe_is_frozen_and_globally_disjoint():
    root = Path(__file__).parents[1]
    prereg = json.loads(
        (root / "research/preregistrations/q107_q104_fresh_equity_coverage_2026_10_01.json").read_text(
            encoding="utf-8"
        )
    )
    universe = get_universe(prereg["universe"])
    symbols = tuple(prereg["symbols"])
    assert universe.symbols == symbols
    assert len(symbols) == 8
    assert len(symbols) == len(set(symbols))
    others = [u for u in list_universes() if u.name != universe.name]
    assert all(not set(symbols).intersection(u.symbols) for u in others)
    assert prereg["governance"]["asset_selection_by_performance"] is False
    assert prereg["governance"]["performance_trial_authorized"] is False
