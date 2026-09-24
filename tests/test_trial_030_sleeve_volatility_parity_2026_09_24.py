from datetime import datetime, timezone

from automation.trial_030_sleeve_volatility_parity_2026_09_24 import (
    SLEEVE_VOL_WINDOW,
    TARGET_VOL,
    _sleeve_parity_weights,
    _vol,
)


def test_fixed_parameters_are_unchanged():
    assert SLEEVE_VOL_WINDOW == 63
    assert TARGET_VOL == 0.10


def test_sleeve_vol_warmup_is_none():
    assert _vol([0.0] * (SLEEVE_VOL_WINDOW - 1)) is None


def test_inverse_vol_parity_moves_weight_toward_lower_vol_sleeve():
    trend = [0.0015 if i % 2 else 0.0005 for i in range(SLEEVE_VOL_WINDOW)]
    cs = [0.03 if i % 2 else -0.03 for i in range(SLEEVE_VOL_WINDOW)]
    trend_weight, cs_weight = _sleeve_parity_weights(trend, cs)
    assert trend_weight > 0.5
    assert cs_weight < 0.5
    assert abs(trend_weight + cs_weight - 1.0) < 1e-12


def test_parity_uses_equal_weights_when_history_is_not_available():
    trend_weight, cs_weight = _sleeve_parity_weights([], [])
    assert trend_weight == 0.5
    assert cs_weight == 0.5
