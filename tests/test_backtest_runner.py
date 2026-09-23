from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from automation.backtest_runner import run_all, run_dataset
from backtesting.models import Candle
from config.parameter_space import ParameterSpace
from research.protocol import dataset_fingerprint
from data.market_store import MarketDataStore


def make_candles(count=50):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        Candle(
            timestamp=start + timedelta(minutes=i),
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


def test_run_dataset():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)
        store.save("TEST", "1h", make_candles())

        result = run_dataset(
            "TEST",
            "1h",
            store=store,
            parameter_space=make_space(),
            optimizer_top_n=1,
            train_ratio=0.7,
            rolling_train_size=20,
            rolling_test_size=10,
            rolling_step_size=10,
            minimum_trades_required=1,
        )

        assert result["candle_count"] == 50
        assert result["research_candle_count"] == 45
        assert result["holdout_candle_count"] == 5
        assert result["walk_forward"]["train_candles"] == 31
        assert result["walk_forward"]["test_candles"] == 14
        assert result["protocol"]["holdout_ratio"] == 0.10
        assert len(result["optimization"]) == 1
        assert result["holdout"]["trade_count"] >= 0
        assert result["safety"]["paper_only"] is True
        assert result["safety"]["live_trading_enabled"] is False

        candles = tuple(store.load("TEST", "1h"))
        research_count = result["research_candle_count"]
        holdout_count = result["holdout_candle_count"]

        assert (
            result["research_dataset_fingerprint"]
            == dataset_fingerprint(candles[:research_count])
        )
        assert (
            result["holdout_dataset_fingerprint"]
            == dataset_fingerprint(candles[research_count:])
        )
        assert research_count + holdout_count == len(candles)
        assert result["research_end"] < result["holdout_start"]


def test_run_dataset_rejects_missing_data():
    with TemporaryDirectory() as tmp:
        store = MarketDataStore(tmp)

        try:
            run_dataset(
                "MISSING",
                "1h",
                store=store,
                parameter_space=make_space(),
            )
        except ValueError:
            return

        raise AssertionError("Fehlende Marktdaten wurden akzeptiert.")


def test_run_all_creates_report_and_checkpoint():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = MarketDataStore(root / "data")
        store.save("TEST", "1h", make_candles())

        report, path = run_all(
            [("TEST", "1h")],
            store=store,
            parameter_space=make_space(),
            optimizer_top_n=1,
            output_dir=root / "reports",
            checkpoint_path=root / "checkpoints" / "latest.json",
        )

        assert path.exists()
        assert len(report["datasets"]) == 1
        assert (
            root / "checkpoints" / "latest.json"
        ).exists()


def test_run_all_resume_returns_completed_report():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = MarketDataStore(root / "data")
        store.save("TEST", "1h", make_candles())

        checkpoint_path = root / "checkpoints" / "latest.json"

        run_all(
            [("TEST", "1h")],
            store=store,
            parameter_space=make_space(),
            optimizer_top_n=1,
            output_dir=root / "reports",
            checkpoint_path=checkpoint_path,
            run_fingerprint="run-abc",
        )

        report, _ = run_all(
            [("TEST", "1h")],
            store=store,
            parameter_space=make_space(),
            optimizer_top_n=1,
            output_dir=root / "reports",
            checkpoint_path=checkpoint_path,
            resume=True,
            run_fingerprint="run-abc",
        )

        assert len(report["datasets"]) == 1


def test_run_all_resume_requires_run_fingerprint():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = MarketDataStore(root / "data")
        store.save("TEST", "1h", make_candles())
        checkpoint_path = root / "checkpoints" / "latest.json"

        run_all(
            [("TEST", "1h")],
            store=store,
            parameter_space=make_space(),
            optimizer_top_n=1,
            output_dir=root / "reports",
            checkpoint_path=checkpoint_path,
            run_fingerprint="run-abc",
        )

        try:
            run_all(
                [("TEST", "1h")],
                store=store,
                parameter_space=make_space(),
                optimizer_top_n=1,
                output_dir=root / "reports",
                checkpoint_path=checkpoint_path,
                resume=True,
            )
        except RuntimeError as exc:
            assert "Run-Identität" in str(exc)
        else:
            raise AssertionError(
                "Resume ohne run_fingerprint wurde akzeptiert."
            )


def test_run_all_resume_rejects_different_run_fingerprint():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = MarketDataStore(root / "data")
        store.save("TEST", "1h", make_candles())
        checkpoint_path = root / "checkpoints" / "latest.json"

        run_all(
            [("TEST", "1h")],
            store=store,
            parameter_space=make_space(),
            optimizer_top_n=1,
            output_dir=root / "reports",
            checkpoint_path=checkpoint_path,
            run_fingerprint="run-abc",
        )

        try:
            run_all(
                [("TEST", "1h")],
                store=store,
                parameter_space=make_space(),
                optimizer_top_n=1,
                output_dir=root / "reports",
                checkpoint_path=checkpoint_path,
                resume=True,
                run_fingerprint="run-def",
            )
        except RuntimeError as exc:
            assert "anderen" in str(exc)
        else:
            raise AssertionError(
                "Resume mit fremder run_fingerprint wurde akzeptiert."
            )



def test_run_all_resumes_after_interruption_without_repeating_completed_dataset(
    monkeypatch,
):
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        checkpoint_path = root / "checkpoints" / "latest.json"

        calls = []
        failed_once = {"value": False}

        def fake_run_dataset(symbol, interval, **kwargs):
            calls.append((symbol, interval))
            if interval == "2h" and not failed_once["value"]:
                failed_once["value"] = True
                raise RuntimeError("simulierter Abbruch")
            return {
                "symbol": symbol,
                "interval": interval,
                "candle_count": 1,
            }

        monkeypatch.setattr(
            "automation.backtest_runner.run_dataset",
            fake_run_dataset,
        )

        datasets = [("TEST", "1h"), ("TEST", "2h")]

        try:
            run_all(
                datasets,
                output_dir=root / "reports",
                checkpoint_path=checkpoint_path,
                run_fingerprint="run-abc",
            )
        except RuntimeError as exc:
            assert "simulierter Abbruch" in str(exc)
        else:
            raise AssertionError("Simulierter Abbruch wurde nicht ausgelöst.")

        assert calls == [("TEST", "1h"), ("TEST", "2h")]

        report, _ = run_all(
            datasets,
            output_dir=root / "reports",
            checkpoint_path=checkpoint_path,
            resume=True,
            run_fingerprint="run-abc",
        )

        assert calls == [
            ("TEST", "1h"),
            ("TEST", "2h"),
            ("TEST", "2h"),
        ]
        assert len(report["datasets"]) == 2
        assert {
            (item["symbol"], item["interval"])
            for item in report["datasets"]
        } == set(datasets)



def test_run_all_reports_optimization_search_size():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = MarketDataStore(root / "data")
        store.save("TEST", "1h", make_candles())

        report, _ = run_all(
            [("TEST", "1h")],
            store=store,
            parameter_space=make_space(),
            optimizer_top_n=1,
            output_dir=root / "reports",
            checkpoint_path=root / "checkpoints" / "latest.json",
            run_fingerprint="run-statistics",
        )

        assert report["datasets"][0]["optimization_candidate_count"] == 1
        assert report["datasets"][0]["optimization_reported_top_n"] == 1
