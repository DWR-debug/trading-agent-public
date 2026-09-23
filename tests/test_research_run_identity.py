from datetime import datetime, timedelta, timezone
import json

import pytest

from automation.research_run import (
    build_run_identity,
    same_run_identity,
)
from automation.research_workflow import load_or_create_run_manifest
from config.parameter_space import ParameterSpace
from data.market_store import MarketDataStore
from research.protocol import ResearchProtocol, dataset_fingerprint
from backtesting.models import Candle


def make_candles(count=4):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        Candle(
            timestamp=start + timedelta(hours=i),
            open=100.0 + i,
            high=101.0 + i,
            low=99.0 + i,
            close=100.5 + i,
            volume=1000.0,
        )
        for i in range(count)
    )


def test_run_identity_is_deterministic(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_COMMIT_SHA", "abc123")

    store = MarketDataStore(tmp_path / "data")
    store.save("TEST", "1h", make_candles())

    protocol = ResearchProtocol()
    space = ParameterSpace(
        momentum_lookbacks=[3],
        mean_reversion_windows=[5],
        mean_reversion_thresholds=[0.02],
        risk_per_trade_values=[0.01],
        leverage_values=[1.0],
    )

    first = build_run_identity(
        [("TEST", "1h")],
        store,
        protocol,
        space,
    )
    second = build_run_identity(
        [("TEST", "1h")],
        store,
        protocol,
        space,
    )

    assert first == second
    assert len(first["run_fingerprint"]) == 64
    assert first["safety"]["paper_only"] is True
    assert first["safety"]["live_trading_enabled"] is False


def test_run_identity_changes_when_protocol_changes(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_COMMIT_SHA", "abc123")

    store = MarketDataStore(tmp_path / "data")
    store.save("TEST", "1h", make_candles())

    space = ParameterSpace(
        momentum_lookbacks=[3],
        mean_reversion_windows=[5],
        mean_reversion_thresholds=[0.02],
        risk_per_trade_values=[0.01],
        leverage_values=[1.0],
    )

    first = build_run_identity(
        [("TEST", "1h")],
        store,
        ResearchProtocol(),
        space,
    )
    second = build_run_identity(
        [("TEST", "1h")],
        store,
        ResearchProtocol(permutation_seed=123),
        space,
    )

    assert not same_run_identity(first, second)


def test_run_identity_changes_when_dataset_changes(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_COMMIT_SHA", "abc123")

    store = MarketDataStore(tmp_path / "data")
    store.save("TEST", "1h", make_candles())

    space = ParameterSpace(
        momentum_lookbacks=[3],
        mean_reversion_windows=[5],
        mean_reversion_thresholds=[0.02],
        risk_per_trade_values=[0.01],
        leverage_values=[1.0],
    )

    first = build_run_identity(
        [("TEST", "1h")],
        store,
        ResearchProtocol(),
        space,
    )

    changed = list(make_candles())
    changed[-1] = Candle(
        timestamp=changed[-1].timestamp,
        open=changed[-1].open,
        high=changed[-1].high + 1.0,
        low=changed[-1].low,
        close=changed[-1].close,
        volume=changed[-1].volume,
    )
    store.save("TEST_CHANGED", "1h", tuple(changed))

    second = build_run_identity(
        [("TEST_CHANGED", "1h")],
        store,
        ResearchProtocol(),
        space,
    )

    assert not same_run_identity(first, second)


def test_manifest_refuses_changed_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_COMMIT_SHA", "abc123")

    store = MarketDataStore(tmp_path / "data")
    store.save("TEST", "1h", make_candles())

    space = ParameterSpace(
        momentum_lookbacks=[3],
        mean_reversion_windows=[5],
        mean_reversion_thresholds=[0.02],
        risk_per_trade_values=[0.01],
        leverage_values=[1.0],
    )
    manifest = tmp_path / "run_manifest.json"

    load_or_create_run_manifest(
        [("TEST", "1h")],
        store=store,
        protocol=ResearchProtocol(),
        parameter_space=space,
        path=manifest,
    )

    with pytest.raises(RuntimeError, match="Resume"):
        load_or_create_run_manifest(
            [("TEST", "1h")],
            store=store,
            protocol=ResearchProtocol(permutation_seed=123),
            parameter_space=space,
            path=manifest,
        )


def test_manifest_fingerprint_refuses_tampering(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_COMMIT_SHA", "abc123")

    store = MarketDataStore(tmp_path / "data")
    store.save("TEST", "1h", make_candles())

    space = ParameterSpace(
        momentum_lookbacks=[3],
        mean_reversion_windows=[5],
        mean_reversion_thresholds=[0.02],
        risk_per_trade_values=[0.01],
        leverage_values=[1.0],
    )
    data_manifest = tmp_path / "data_manifest.json"
    data_manifest.write_text(
        json.dumps(
            {
                "universe": "test",
                "datasets": [
                    {
                        "symbol": "TEST",
                        "interval": "1h",
                        "candle_count": 4,
                        "fingerprint": dataset_fingerprint(make_candles()),
                    }
                ],
                "manifest_fingerprint": "tampered",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="gültigen Fingerprint"):
        build_run_identity(
            [("TEST", "1h")],
            store,
            ResearchProtocol(),
            space,
            data_manifest_path=data_manifest,
        )
