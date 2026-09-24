from research.long_short_strategies import (
    build_signed_exposure,
    sma_50_200_long_short_signal,
    tsm_ensemble_long_short_signal,
)


def test_sma_long_short_has_both_signed_states():
    closes = tuple([100.0] * 220 + [101.0 + i * 0.5 for i in range(20)])
    signal = sma_50_200_long_short_signal(closes)
    assert signal[-1] == 1

    down = tuple([200.0] * 200 + [60.0 - i * 2 for i in range(20)])
    signal_down = sma_50_200_long_short_signal(down)
    assert signal_down[-1] == -1


def test_tsm_is_symmetric_long_short():
    rising = tuple(float(i + 1) for i in range(300))
    falling = tuple(float(301 - i) for i in range(300))
    assert tsm_ensemble_long_short_signal(rising)[-1] == 1
    assert tsm_ensemble_long_short_signal(falling)[-1] == -1


def test_exposure_preserves_signal_direction():
    closes = tuple(100.0 + 0.2 * i + (i % 5) for i in range(120))
    signal = tuple([0] * 63 + [1] * 30 + [-1] * 27)
    exposure = build_signed_exposure(closes, signal, target_annualized_vol=0.2)
    assert max(exposure) >= 0.0
    assert min(exposure) <= 0.0