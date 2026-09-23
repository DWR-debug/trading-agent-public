"""
Tests für die Trading-Strategien.

Wichtig:
Diese Tests prüfen ausschließlich die Signalerzeugung.
Es werden keine Orders ausgeführt.
"""

from strategies.signals import SignalType
from strategies.momentum import MomentumStrategy
from strategies.mean_reversion import MeanReversionStrategy


def test_momentum_buy():
    strategy = MomentumStrategy(lookback=3)

    signal = strategy.generate_signal(
        "TEST",
        [100, 101, 102, 105],
    )

    assert signal.signal == SignalType.BUY
    assert signal.symbol == "TEST"
    assert 0.0 <= signal.confidence <= 1.0


def test_momentum_sell():
    strategy = MomentumStrategy(lookback=3)

    signal = strategy.generate_signal(
        "TEST",
        [105, 104, 103, 100],
    )

    assert signal.signal == SignalType.SELL


def test_momentum_hold():
    strategy = MomentumStrategy(lookback=3)

    signal = strategy.generate_signal(
        "TEST",
        [100, 100, 100, 100],
    )

    assert signal.signal == SignalType.HOLD


def test_mean_reversion_buy():
    strategy = MeanReversionStrategy(
        window=5,
        threshold=0.02,
    )

    signal = strategy.generate_signal(
        "TEST",
        [100, 100, 100, 100, 95],
    )

    assert signal.signal == SignalType.BUY


def test_mean_reversion_sell():
    strategy = MeanReversionStrategy(
        window=5,
        threshold=0.02,
    )

    signal = strategy.generate_signal(
        "TEST",
        [100, 100, 100, 100, 105],
    )

    assert signal.signal == SignalType.SELL


def test_mean_reversion_hold():
    strategy = MeanReversionStrategy(
        window=5,
        threshold=0.02,
    )

    signal = strategy.generate_signal(
        "TEST",
        [100, 100, 100, 100, 101],
    )

    assert signal.signal == SignalType.HOLD


def test_invalid_prices_are_rejected():
    strategy = MomentumStrategy(lookback=3)

    try:
        strategy.generate_signal(
            "TEST",
            [100, 101, 0, 105],
        )
        raise AssertionError("Ungültiger Preis wurde akzeptiert.")
    except ValueError:
        pass


def test_insufficient_data_is_rejected():
    strategy = MomentumStrategy(lookback=5)

    try:
        strategy.generate_signal(
            "TEST",
            [100, 101, 102],
        )
        raise AssertionError("Zu wenige Daten wurden akzeptiert.")
    except ValueError:
        pass



def test_strategy_engine_confirms_buy():
    from config.parameters import StrategyParameters
    from strategies.strategy_engine import StrategyEngine

    engine = StrategyEngine(StrategyParameters())

    signal = engine.generate_signal(
        "TEST",
        [80, 110, 110, 110, 110, 100],
    )

    assert signal.signal == SignalType.BUY
    assert 0.0 <= signal.confidence <= 1.0


def test_strategy_engine_confirms_sell():
    from config.parameters import StrategyParameters
    from strategies.strategy_engine import StrategyEngine

    engine = StrategyEngine(StrategyParameters())

    signal = engine.generate_signal(
        "TEST",
        [120, 90, 90, 90, 90, 100],
    )

    assert signal.signal == SignalType.SELL
    assert 0.0 <= signal.confidence <= 1.0


def test_signal_combiner_allows_strong_signal_against_weak_signal():
    from strategies.signals import TradingSignal
    from strategies.strategy_engine import StrategyEngine

    engine = StrategyEngine()

    momentum_signal = TradingSignal(
        symbol="TEST",
        signal=SignalType.BUY,
        confidence=0.8,
        reason="Test Momentum BUY",
    )

    mean_reversion_signal = TradingSignal(
        symbol="TEST",
        signal=SignalType.SELL,
        confidence=0.2,
        reason="Test Mean-Reversion SELL",
    )

    combined = engine._combine_signals(
        momentum_signal,
        mean_reversion_signal,
    )

    assert combined.signal == SignalType.BUY
    assert combined.confidence == 0.3


def test_signal_combiner_holds_when_score_is_weak():
    from strategies.signals import TradingSignal
    from strategies.strategy_engine import StrategyEngine

    engine = StrategyEngine()

    momentum_signal = TradingSignal(
        symbol="TEST",
        signal=SignalType.BUY,
        confidence=0.3,
        reason="Test Momentum BUY",
    )

    mean_reversion_signal = TradingSignal(
        symbol="TEST",
        signal=SignalType.SELL,
        confidence=0.2,
        reason="Test Mean-Reversion SELL",
    )

    combined = engine._combine_signals(
        momentum_signal,
        mean_reversion_signal,
    )

    assert combined.signal == SignalType.HOLD

def run_tests():
    tests = [
        test_momentum_buy,
        test_momentum_sell,
        test_momentum_hold,
        test_mean_reversion_buy,
        test_mean_reversion_sell,
        test_mean_reversion_hold,
        test_invalid_prices_are_rejected,
        test_insufficient_data_is_rejected,
        test_strategy_engine_confirms_buy,
        test_strategy_engine_confirms_sell,
        test_signal_combiner_allows_strong_signal_against_weak_signal,
        test_signal_combiner_holds_when_score_is_weak,
    ]

    passed = 0

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
        passed += 1

    print()
    print(f"{passed}/{len(tests)} Strategie-Tests bestanden.")


if __name__ == "__main__":
    run_tests()
