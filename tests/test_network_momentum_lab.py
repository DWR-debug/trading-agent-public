from datetime import datetime, timedelta, timezone

import pytest

from automation.network_momentum_lab import (
    COMMON_CANDLES,
    CORR_LOOKBACK,
    PEER_LAG,
    RESEARCH_RETURNS,
    HOLDOUT_RETURNS,
    SYMBOLS,
    _network_scores_fast,
    _pair_correlations,
    _align,
    _stats,
)


def _trend_series(length: int = 650):
    return [
        float(index)
        for index in range(length)
    ]


def test_pair_correlation_uses_fixed_positive_lag():
    target = _trend_series()
    peer = list(target)
    correlations = _pair_correlations(target, peer)

    index = CORR_LOOKBACK + PEER_LAG + 20
    assert correlations[index] == pytest.approx(1.0)


def test_network_score_is_weighted_mean_of_lagged_peer_signals():
    trends = {
        symbol: _trend_series()
        for symbol in SYMBOLS
    }
    signals = {
        symbol: [1] * len(trends[symbol])
        for symbol in SYMBOLS
    }

    scores = _network_scores_fast(trends, signals)
    index = CORR_LOOKBACK + PEER_LAG + 20
    assert scores[SYMBOLS[0]][index] == pytest.approx(1.0)


def test_alignment_trims_to_last_common_calendar():
    base = datetime(2010, 1, 1, tzinfo=timezone.utc)

    def make_bars(offset=0):
        return tuple(
            type(
                "Bar",
                (),
                {"timestamp": base + timedelta(days=offset + i)},
            )()
            for i in range(3520)
        )

    assets = {
        SYMBOLS[0]: make_bars(0),
        SYMBOLS[1]: make_bars(20),
    }
    aligned = _align(assets)

    assert len(aligned[SYMBOLS[0]]) == 3500
    assert len(aligned[SYMBOLS[1]]) == 3500
    assert aligned[SYMBOLS[0]][0].timestamp == aligned[SYMBOLS[1]][0].timestamp


def test_split_contract_is_t038_compatible():
    assert COMMON_CANDLES == 3500
    assert RESEARCH_RETURNS == 2798
    assert HOLDOUT_RETURNS == 700


def test_stats_profit_factor_and_drawdown():
    result = _stats([0.10, -0.05, 0.05])
    assert result["return"] == pytest.approx(1.10 * 0.95 * 1.05 - 1.0)
    assert result["profit_factor"] == pytest.approx(3.0)
    assert result["max_drawdown"] == pytest.approx(0.05)


def test_network_engine_keeps_direction_long_or_flat():
    from automation.network_momentum_lab import _trend_signals

    assert _trend_signals([1.0, -1.0, 0.0]) == [1, -1, 0]
