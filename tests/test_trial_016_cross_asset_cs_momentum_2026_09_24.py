from pathlib import Path

from automation.trial_016_cross_asset_cs_momentum_2026_09_24 import (
    ASSETS,
    LOOKBACK,
    REBALANCE_DAYS,
    SKIP,
    TOP_N,
)


def test_trial_016_contract_is_fixed():
    assert ASSETS == ("DBA", "DBB", "FXA", "FXY", "MUB", "SHV", "EMB", "BWX")
    assert LOOKBACK == 252
    assert SKIP == 21
    assert REBALANCE_DAYS == 21
    assert TOP_N == 2
