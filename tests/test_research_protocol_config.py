import json
from datetime import datetime, timedelta, timezone

from automation.backtest_runner import _rolling_window_sizes, run_dataset
from automation.one_command_research import main as one_command_main
from automation.research_run import build_run_identity
from automation.research_workflow import DEFAULT_RESEARCH_RUN_OPTIONS
from backtesting.models import Candle
from research.protocol import ResearchProtocol
from config.parameter_space import ParameterSpace
from data.market_store import MarketDataStore


def make_candles(count=100):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        Candle(
            timestamp=start + timedelta(days=i),
            open=100.0 + i,
            high=100.0 + i,
            low=100.0 + i,
            close=100.0 + i,
            volume=1000.0,
        )
        for i in range(count)
    )


def make_space():
    return ParameterSpace(
        momentum_lookbacks=[3],
        mean_reversion_windows=[5],
        mean_reversion_thresholds=[0.02],
        risk_per_trade_values=[0.01],
        leverage_values=[1.0],
    )


def test_rolling_window_sizes_are_data_relative():
    assert _rolling_window_sizes(
        900,
        train_ratio=0.5,
        test_ratio=0.1,
        step_ratio=0.1,
    ) == (450, 90, 90)

    assert _rolling_window_sizes(
        9000,
        train_ratio=0.5,
        test_ratio=0.1,
        step_ratio=0.1,
    ) == (4500, 900, 900)


def test_execution_config_is_explicit_and_stable():
    assert DEFAULT_RESEARCH_RUN_OPTIONS == {
        "optimizer_top_n": 5,
        "selection_profile": "score_max",
        "train_ratio": 0.7,
        "rolling_train_ratio": 0.5,
        "rolling_test_ratio": 0.1,
        "rolling_step_ratio": 0.1,
        "minimum_trades_required": 30,
    }


def test_run_identity_changes_when_rolling_config_changes(tmp_path):
    store = MarketDataStore(tmp_path / "data")
    store.save("TEST", "1d", make_candles())
    space = make_space()

    base = build_run_identity(
        [("TEST", "1d")],
        store,
        protocol=ResearchProtocol(),
        parameter_space=space,
        execution_config={"rolling_train_ratio": 0.5},
    )
    changed = build_run_identity(
        [("TEST", "1d")],
        store,
        protocol=ResearchProtocol(),
        parameter_space=space,
        execution_config={"rolling_train_ratio": 0.6},
    )

    assert base["run_fingerprint"] != changed["run_fingerprint"]


def test_valid_blocked_one_command_exit_is_zero(monkeypatch):
    monkeypatch.setattr(
        "automation.one_command_research.run_universe",
        lambda *_args, **_kwargs: {"status": "BLOCKED"},
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "one_command_research",
            "--universe",
            "small_cap_high_volatility",
        ],
    )

    import pytest

    with pytest.raises(SystemExit) as exc_info:
        one_command_main()

    assert exc_info.value.code == 0
