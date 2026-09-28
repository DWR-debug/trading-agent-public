from automation.q067_alpha_mechanisms import (
    E1_CORRELATION_LOOKBACK,
    E1_EXPOSURE_MULTIPLIER,
    E2_MIN_ABS_WEIGHT_CHANGE,
    GROSS_EXPOSURE_CAP,
    validate_gross_exposure_cap,
    Q067_SLEEVES,
    Q067_SYMBOLS,
    apply_common_mode_throttle,
    apply_turnover_hysteresis,
    common_mode_multipliers,
    equal_weight_ensemble,
    mean_pairwise_correlation,
)


def _base_sleeves(n=3500):
    return {
        name: tuple(
            {
                symbol: (0.125 if (idx + slot) % 8 == 0 else 0.0)
                for slot, symbol in enumerate(Q067_SYMBOLS)
            }
            for idx in range(n)
        )
        for name in Q067_SLEEVES
    }


def test_equal_weight_ensemble_is_symmetric():
    sleeves = _base_sleeves(4)
    ensemble = equal_weight_ensemble(sleeves)
    assert len(ensemble) == 4
    assert all(abs(sum(row.values()) - 0.125) < 1e-12 for row in ensemble)


def test_common_mode_multipliers_stay_off_until_three_high_observations():
    returns = {name: [0.01 * i for i in range(3500)] for name in Q067_SLEEVES}
    values = common_mode_multipliers(returns, decision_count=70)
    assert values[63] == 1.0
    assert values[65] == 1.0
    assert values[66] == E1_EXPOSURE_MULTIPLIER


def test_mean_pairwise_correlation_is_one_for_identical_series():
    history = {name: [float(i) for i in range(E1_CORRELATION_LOOKBACK)] for name in Q067_SLEEVES}
    assert abs(mean_pairwise_correlation(history) - 1.0) < 1e-12


def test_common_mode_throttle_scales_all_assets_when_active():
    sleeves = _base_sleeves(100)
    aggregate = equal_weight_ensemble(sleeves)
    returns = {name: [0.01 * i for i in range(3500)] for name in Q067_SLEEVES}
    throttled = apply_common_mode_throttle(aggregate, returns)
    assert throttled[66] != aggregate[66]
    assert all(
        abs(throttled[66][symbol] - aggregate[66][symbol] * E1_EXPOSURE_MULTIPLIER) < 1e-12
        for symbol in Q067_SYMBOLS
    )


def test_turnover_hysteresis_carries_small_nonzero_changes():
    aggregate = (
        {symbol: (0.125 if symbol == Q067_SYMBOLS[0] else 0.0) for symbol in Q067_SYMBOLS},
        {symbol: (0.125 - 0.5 * E2_MIN_ABS_WEIGHT_CHANGE if symbol == Q067_SYMBOLS[0] else 0.0) for symbol in Q067_SYMBOLS},
    )
    out = apply_turnover_hysteresis(aggregate)
    assert out[1][Q067_SYMBOLS[0]] == out[0][Q067_SYMBOLS[0]]


def test_turnover_hysteresis_does_not_block_entry_or_exit():
    aggregate = (
        {symbol: (0.125 if symbol == Q067_SYMBOLS[0] else 0.0) for symbol in Q067_SYMBOLS},
        {symbol: 0.0 for symbol in Q067_SYMBOLS},
        {symbol: (0.02 if symbol == Q067_SYMBOLS[0] else 0.0) for symbol in Q067_SYMBOLS},
    )
    out = apply_turnover_hysteresis(aggregate)
    assert out[1][Q067_SYMBOLS[0]] == 0.0
    assert out[2][Q067_SYMBOLS[0]] == 0.02


def test_gross_exposure_cap_accepts_preregistered_limit():
    weights = (
        {symbol: (0.125 if symbol == Q067_SYMBOLS[0] else 0.0) for symbol in Q067_SYMBOLS},
    )
    validate_gross_exposure_cap(weights)


def test_gross_exposure_cap_fails_closed_on_overage():
    weights = (
        {symbol: (GROSS_EXPOSURE_CAP / 2 + 0.01) for symbol in Q067_SYMBOLS},
    )
    try:
        validate_gross_exposure_cap(weights)
    except ValueError as exc:
        assert "gross exposure cap exceeded" in str(exc)
    else:
        raise AssertionError("gross exposure cap guard accepted an over-cap portfolio")
