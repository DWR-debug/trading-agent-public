from datetime import datetime, timezone

from automation.literature_strategy_lab import (
    ASSETS,
    STRATEGIES,
    _donchian_signal,
    _sma_long_flat_signal,
    _tsm_signal,
    generate_signal,
)


def test_strategy_family_set_is_small_and_fixed():
    assert STRATEGIES == (
        "buy_and_hold",
        "tsm_126",
        "tsm_ensemble",
        "donchian_55_20",
        "sma_50_200_long_flat",
        "mean_reversion_20_2",
    )


def test_supported_assets_are_the_archived_benchmark_assets():
    assert ASSETS == ("SPY", "QQQ", "IWM")


def test_tsm_signal_uses_only_past_data():
    closes = [100.0] * 10 + [110.0]
    signal = _tsm_signal(closes, 5)
    assert signal[:5] == [0] * 5
    assert signal[-1] == 1


def test_donchian_and_sma_emit_deterministic_signals():
    closes = [100.0 + index for index in range(250)]
    donchian = _donchian_signal(closes, 10, 5)
    sma = _sma_long_flat_signal(closes, 20, 50)

    assert len(donchian) == len(closes)
    assert len(sma) == len(closes)
    assert donchian[-1] in {-1, 0, 1}
    assert sma[-1] in {0, 1}


def test_generate_signal_rejects_unknown_family():
    class DummyBar:
        timestamp = datetime(2020, 1, 1, tzinfo=timezone.utc)
        open = high = low = close = volume = 1.0

    try:
        generate_signal((DummyBar(),), "unknown")
    except ValueError:
        return

    raise AssertionError("Unbekannte Strategie wurde akzeptiert.")


def test_evaluate_does_not_include_returns_before_segment_start():
    from automation.literature_strategy_lab import evaluate

    class Bar:
        def __init__(self, price):
            self.open = price
            self.high = price + 1.0
            self.low = price - 1.0
            self.close = price
            self.volume = 1000.0
            self.timestamp = datetime(2020, 1, 1, tzinfo=timezone.utc)

    bars = tuple(Bar(float(value)) for value in range(100, 110))
    exposure = [1.0] * len(bars)

    whole = evaluate(bars, exposure, 0, len(bars))
    segment = evaluate(bars, exposure, 5, len(bars))

    assert segment["active_days"] < whole["active_days"]
