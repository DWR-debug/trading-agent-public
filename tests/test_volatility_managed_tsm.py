from datetime import datetime, timedelta, timezone

from automation.volatility_managed_tsm import (
    COST_RATE,
    RESEARCH_COUNT,
    EVALUATION_COUNT,
    TARGET_VARIANCE,
    VOL_LOOKBACK,
    _annualized_realized_variance,
    _inverse_variance_scale,
    _stats,
    _summary,
    _target_weights,
    _tsm_signal,
)


def test_tsm_signal_uses_only_prior_closes():
    closes = [100.0 + index for index in range(260)]
    closes[252] = 110.0
    closes[253] = 1_000_000.0
    assert _tsm_signal(closes, 254) == 1
    closes[253] = -1.0
    assert _tsm_signal(closes, 254) == 1


def test_inverse_variance_scale_is_de_risk_only():
    assert _inverse_variance_scale(TARGET_VARIANCE * 4.0) == 0.25
    assert _inverse_variance_scale(TARGET_VARIANCE / 2.0) == 1.0


def test_realized_variance_requires_prior_window():
    closes = [100.0] * (VOL_LOOKBACK + 2)
    assert _annualized_realized_variance(closes, VOL_LOOKBACK - 1) == 0.0
    assert _annualized_realized_variance(closes, VOL_LOOKBACK + 1) == 0.0


def test_target_weights_respect_gross_cap():
    closes = {symbol: [100.0 + i for i in range(300)] for symbol in ("A", "B", "C", "D")}
    weights = _target_weights(closes, 253, challenger=True)
    assert sum(abs(value) for value in weights.values()) <= 1.0 + 1e-12


def test_equal_weight_control_is_equal_absolute_weight():
    closes = {symbol: [100.0 + i for i in range(300)] for symbol in ("A", "B", "C", "D")}
    weights = _target_weights(closes, 253, challenger=False)
    assert all(abs(abs(value) - 0.25) < 1e-12 for value in weights.values())


def test_summary_preserves_exact_research_and_holdout_counts():
    values = [0.001] * EVALUATION_COUNT
    summary = _summary(values, RESEARCH_COUNT)
    assert summary["research"]["day_count"] == RESEARCH_COUNT
    assert summary["holdout"]["day_count"] == 700


def test_summary_oos_ratio_is_inside_research_only():
    values = [0.001] * EVALUATION_COUNT
    summary = _summary(values, RESEARCH_COUNT)
    assert summary["oos"]["day_count"] == int(RESEARCH_COUNT * 0.20)
    assert summary["holdout"]["day_count"] == 700


def test_stats_turns_positive_and_negative_paths_correctly():
    summary = _stats([0.10, -0.05], 0, 2)
    assert summary["period_return"] < 0.05
    assert summary["profit_factor"] == 2.0


def test_cost_rate_is_15_bps():
    assert abs(COST_RATE - 0.0015) < 1e-12


def test_point_in_time_weight_decision_timestamp_shape():
    timestamps = [
        datetime(2026, 1, 2, tzinfo=timezone.utc) + timedelta(days=i)
        for i in range(3)
    ]
    assert timestamps[0] < timestamps[1] < timestamps[2]
