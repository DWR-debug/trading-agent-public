from config import settings
from execution.execution_guard import execute_live_order, SecurityError
from execution.paper_broker import PaperBroker
from execution.trading_engine import TradingEngine
from risk.risk_engine import calculate_position, RiskError


def test_normal_paper_trade():
    broker = PaperBroker(initial_capital=500)

    result = broker.execute_order(
        symbol="TEST",
        side="BUY",
        quantity=2.5,
        price=100,
        leverage=3,
    )

    assert result["status"] == "PAPER_FILLED"
    assert broker.account_status()["open_positions"] == 1


def test_excessive_leverage_is_rejected():
    try:
        calculate_position(500, 100, 98, 4)
        assert False
    except RiskError:
        assert True


def test_live_order_is_blocked():
    try:
        execute_live_order({"symbol": "TEST"})
        assert False
    except SecurityError:
        assert True


def test_paper_only_configuration():
    assert settings.PAPER_ONLY is True


def test_live_trading_disabled():
    assert settings.LIVE_TRADING_ENABLED is False


def test_invalid_price_is_rejected():
    broker = PaperBroker(initial_capital=500)

    try:
        broker.execute_order(
            symbol="TEST",
            side="BUY",
            quantity=1,
            price=0,
            leverage=1,
        )
        assert False
    except ValueError:
        assert True


def test_max_open_positions():
    engine = TradingEngine()

    for i in range(settings.MAX_OPEN_POSITIONS):
        engine.create_paper_trade(
            symbol=f"TEST{i}",
            side="BUY",
            entry_price=100,
            stop_price=98,
            leverage=1,
        )

    try:
        engine.create_paper_trade(
            symbol="EXTRA",
            side="BUY",
            entry_price=100,
            stop_price=98,
            leverage=1,
        )
        assert False
    except RiskError:
        assert True


def test_daily_loss_kill_switch():
    engine = TradingEngine()

    try:
        engine.portfolio_risk.update_equity(
            500 - settings.MAX_DAILY_LOSS_EUR
        )
        assert False
    except RiskError:
        assert True

    assert engine.portfolio_risk.kill_switch is True


def test_drawdown_kill_switch():
    engine = TradingEngine()

    try:
        engine.portfolio_risk.update_equity(
            500 * (1 - settings.MAX_DRAWDOWN_PERCENT / 100)
        )
        assert False
    except RiskError:
        assert True

    assert engine.portfolio_risk.kill_switch is True


def test_kill_switch_remains_active_after_recovery():
    engine = TradingEngine()

    try:
        engine.portfolio_risk.update_equity(
            500 - settings.MAX_DAILY_LOSS_EUR
        )
        assert False
    except RiskError:
        assert True

    assert engine.portfolio_risk.kill_switch is True

    try:
        engine.portfolio_risk.update_equity(500)
    except RiskError:
        pass

    assert engine.portfolio_risk.kill_switch is True

def test_paper_position_lifecycle_long():
    broker = PaperBroker(
        initial_capital=500,
        fee_rate=0.0005,
        slippage_rate=0,
    )

    opened = broker.execute_order(
        symbol="TEST",
        side="BUY",
        quantity=1,
        price=100,
        leverage=1,
    )

    assert opened["status"] == "PAPER_FILLED"
    assert broker.account_status()["open_positions"] == 1

    unrealized = broker.unrealized_pnl(
        symbol="TEST",
        current_price=110,
    )

    assert unrealized == 10

    closed = broker.close_position(
        symbol="TEST",
        price=110,
    )

    assert closed["status"] == "PAPER_CLOSED"
    assert closed["net_pnl"] > 0
    assert broker.account_status()["open_positions"] == 0


def test_paper_position_lifecycle_short():
    broker = PaperBroker(
        initial_capital=500,
        fee_rate=0.0005,
        slippage_rate=0,
    )

    broker.execute_order(
        symbol="TEST",
        side="SELL",
        quantity=1,
        price=100,
        leverage=1,
    )

    unrealized = broker.unrealized_pnl(
        symbol="TEST",
        current_price=90,
    )

    assert unrealized == 10

    closed = broker.close_position(
        symbol="TEST",
        price=90,
    )

    assert closed["status"] == "PAPER_CLOSED"
    assert closed["net_pnl"] > 0


def test_duplicate_position_is_rejected():
    broker = PaperBroker(initial_capital=500)

    broker.execute_order(
        symbol="TEST",
        side="BUY",
        quantity=1,
        price=100,
        leverage=1,
    )

    try:
        broker.execute_order(
            symbol="TEST",
            side="BUY",
            quantity=1,
            price=100,
            leverage=1,
        )
        assert False
    except ValueError:
        assert True


def test_missing_position_close_is_rejected():
    broker = PaperBroker(initial_capital=500)

    try:
        broker.close_position("MISSING", 100)
        assert False
    except ValueError:
        assert True


def test_market_equity_updates_portfolio_risk():
    engine = TradingEngine()

    engine.create_paper_trade(
        symbol="TEST",
        side="BUY",
        entry_price=100,
        stop_price=98,
        leverage=1,
    )

    result = engine.update_market_equity({"TEST": 98})

    assert result["equity"] < 500
    assert result["portfolio_risk"]["equity"] == result["equity"]
    assert result["portfolio_risk"]["kill_switch"] is False


def test_market_equity_triggers_daily_loss_kill_switch():
    engine = TradingEngine()

    engine.create_paper_trade(
        symbol="TEST",
        side="BUY",
        entry_price=100,
        stop_price=98,
        leverage=1,
    )

    try:
        engine.update_market_equity({"TEST": 50})
        assert False
    except RiskError:
        assert True

    assert engine.portfolio_risk.kill_switch is True


def test_closed_position_updates_equity_and_position_count():
    engine = TradingEngine()

    engine.create_paper_trade(
        symbol="TEST",
        side="BUY",
        entry_price=100,
        stop_price=98,
        leverage=1,
    )

    result = engine.close_paper_position(
        symbol="TEST",
        price=110,
    )

    assert result["status"] == "PAPER_CLOSED"
    assert result["portfolio_risk"]["open_positions"] == 0
    assert engine.broker.positions == {}


def test_long_stop_loss_is_detected():
    broker = PaperBroker(
        initial_capital=500,
        fee_rate=0,
        slippage_rate=0,
    )

    broker.execute_order(
        symbol="TEST",
        side="BUY",
        quantity=1,
        price=100,
        leverage=1,
        stop_price=98,
    )

    assert broker.check_stop_loss("TEST", 99) is False
    assert broker.check_stop_loss("TEST", 98) is True

    result = broker.execute_stop_loss(
        symbol="TEST",
        current_price=98,
    )

    assert result["reason"] == "STOP_LOSS"
    assert broker.account_status()["open_positions"] == 0


def test_short_stop_loss_is_detected():
    broker = PaperBroker(
        initial_capital=500,
        fee_rate=0,
        slippage_rate=0,
    )

    broker.execute_order(
        symbol="TEST",
        side="SELL",
        quantity=1,
        price=100,
        leverage=1,
        stop_price=102,
    )

    assert broker.check_stop_loss("TEST", 101) is False
    assert broker.check_stop_loss("TEST", 102) is True

    result = broker.execute_stop_loss(
        symbol="TEST",
        current_price=102,
    )

    assert result["reason"] == "STOP_LOSS"
    assert broker.account_status()["open_positions"] == 0


def test_invalid_long_stop_price_is_rejected():
    broker = PaperBroker(initial_capital=500)

    try:
        broker.execute_order(
            symbol="TEST",
            side="BUY",
            quantity=1,
            price=100,
            leverage=1,
            stop_price=101,
        )
        assert False
    except ValueError:
        assert True


def test_invalid_short_stop_price_is_rejected():
    broker = PaperBroker(initial_capital=500)

    try:
        broker.execute_order(
            symbol="TEST",
            side="SELL",
            quantity=1,
            price=100,
            leverage=1,
            stop_price=99,
        )
        assert False
    except ValueError:
        assert True


def test_trading_engine_stores_stop_price():
    engine = TradingEngine()

    engine.create_paper_trade(
        symbol="TEST",
        side="BUY",
        entry_price=100,
        stop_price=98,
        leverage=1,
    )

    assert engine.broker.positions["TEST"].stop_price == 98


def test_trading_engine_automatic_long_stop():
    engine = TradingEngine()

    engine.create_paper_trade(
        symbol="TEST",
        side="BUY",
        entry_price=100,
        stop_price=98,
        leverage=1,
    )

    result = engine.update_market_equity({"TEST": 98})

    assert len(result["stop_losses"]) == 1
    assert result["stop_losses"][0]["reason"] == "STOP_LOSS"
    assert result["portfolio_risk"]["open_positions"] == 0
    assert engine.broker.positions == {}


def test_trading_engine_automatic_short_stop():
    engine = TradingEngine()

    engine.create_paper_trade(
        symbol="TEST",
        side="SELL",
        entry_price=100,
        stop_price=102,
        leverage=1,
    )

    result = engine.update_market_equity({"TEST": 102})

    assert len(result["stop_losses"]) == 1
    assert result["stop_losses"][0]["reason"] == "STOP_LOSS"
    assert result["portfolio_risk"]["open_positions"] == 0
    assert engine.broker.positions == {}


def test_trading_engine_does_not_stop_before_price():
    engine = TradingEngine()

    engine.create_paper_trade(
        symbol="TEST",
        side="BUY",
        entry_price=100,
        stop_price=98,
        leverage=1,
    )

    result = engine.update_market_equity({"TEST": 99})

    assert len(result["stop_losses"]) == 0
    assert result["portfolio_risk"]["open_positions"] == 1
    assert "TEST" in engine.broker.positions


def test_stop_loss_updates_realized_pnl():
    engine = TradingEngine()

    engine.create_paper_trade(
        symbol="TEST",
        side="BUY",
        entry_price=100,
        stop_price=98,
        leverage=1,
    )

    result = engine.update_market_equity({"TEST": 98})

    assert len(result["stop_losses"]) == 1
    assert result["account"]["realized_pnl"] < 0
    assert result["account"]["open_positions"] == 0


def run_all_tests():
    tests = [
        test_normal_paper_trade,
        test_excessive_leverage_is_rejected,
        test_live_order_is_blocked,
        test_paper_only_configuration,
        test_live_trading_disabled,
        test_invalid_price_is_rejected,
        test_max_open_positions,
        test_daily_loss_kill_switch,
        test_drawdown_kill_switch,
        test_kill_switch_remains_active_after_recovery,
        test_paper_position_lifecycle_long,
        test_paper_position_lifecycle_short,
        test_duplicate_position_is_rejected,
        test_missing_position_close_is_rejected,
        test_market_equity_updates_portfolio_risk,
        test_market_equity_triggers_daily_loss_kill_switch,
        test_closed_position_updates_equity_and_position_count,
        test_long_stop_loss_is_detected,
        test_short_stop_loss_is_detected,
        test_invalid_long_stop_price_is_rejected,
        test_invalid_short_stop_price_is_rejected,
        test_trading_engine_stores_stop_price,
        test_trading_engine_automatic_long_stop,
        test_trading_engine_automatic_short_stop,
        test_trading_engine_does_not_stop_before_price,
        test_stop_loss_updates_realized_pnl,
    ]

    passed = 0

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
        passed += 1

    print()
    print(f"{passed}/{len(tests)} Sicherheitstests bestanden.")




# ============================================================
# ParameterSpace Sicherheitstests
# ============================================================

def test_parameter_space_size():
    from config.parameter_space import ParameterSpace

    space = ParameterSpace()

    assert space.size() == 1280


def test_parameter_space_rejects_excessive_leverage():
    from config.parameter_space import ParameterSpace

    try:
        ParameterSpace(leverage_values=[4.0])
    except ValueError:
        return

    raise AssertionError(
        "ParameterSpace darf 4x Hebel nicht akzeptieren."
    )


def test_parameter_space_rejects_excessive_risk():
    from config.parameter_space import ParameterSpace

    try:
        ParameterSpace(risk_per_trade_values=[0.02])
    except ValueError:
        return

    raise AssertionError(
        "ParameterSpace darf 2% Risiko nicht akzeptieren."
    )


def test_parameter_space_accepts_maximum_leverage():
    from config.parameter_space import ParameterSpace

    space = ParameterSpace(leverage_values=[3.0])

    candidate = next(space.candidates())

    assert candidate.leverage == 3.0


def test_parameter_space_accepts_maximum_risk():
    from config.parameter_space import ParameterSpace

    space = ParameterSpace(risk_per_trade_values=[0.01])

    candidate = next(space.candidates())

    assert candidate.risk_per_trade == 0.01


def run_parameter_space_tests():
    tests = [
        test_parameter_space_size,
        test_parameter_space_rejects_excessive_leverage,
        test_parameter_space_rejects_excessive_risk,
        test_parameter_space_accepts_maximum_leverage,
        test_parameter_space_accepts_maximum_risk,
    ]

    passed = 0

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
        passed += 1

    print()
    print(f"{passed}/{len(tests)} ParameterSpace-Sicherheitstests bestanden.")


if __name__ == "__main__":
    run_all_tests()
    run_parameter_space_tests()
