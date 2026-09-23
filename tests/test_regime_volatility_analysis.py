import csv
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from automation.regime_volatility_analysis import analyze, dataset_fingerprint


def write_csv(path: Path, count: int = 40) -> list[dict]:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    for i in range(count):
        close = 100.0 + i
        rows.append({
            "timestamp": start + timedelta(days=i),
            "open": close - 0.1,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 1000.0 + i,
        })
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for r in rows:
            writer.writerow([r["timestamp"].isoformat(), r["open"], r["high"], r["low"], r["close"], r["volume"]])
    return rows


def candidate(momentum=8, window=20, threshold=0.02):
    return {
        "risk_per_trade": 0.01,
        "leverage": 1.0,
        "strategy": {
            "momentum": {"lookback": momentum},
            "mean_reversion": {"window": window, "threshold": threshold},
        },
    }


def window(index, start, end, cand, profit, pf):
    return {
        "window_index": index,
        "test_start_index": start,
        "test_end_index": end,
        "test_start": f"2020-01-{start+1:02d}T00:00:00+00:00",
        "test_end": f"2020-01-{end:02d}T00:00:00+00:00",
        "candidate": cand,
        "net_profit_eur": profit,
        "profit_factor": pf,
        "max_drawdown_percent": 2.0,
        "trade_count": 10,
    }


def rolling(rows):
    fp = dataset_fingerprint(rows)
    return {
        "diagnostic_type": "rolling_geometry_time_phase_control",
        "diagnostic_fingerprint": "source",
        "code_version": "code",
        "target_count": len(rows),
        "research_candle_count": len(rows),
        "universe": "benchmark",
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False},
        "datasets": [{
            "symbol": "TEST",
            "full_data_fingerprint": fp,
            "research_fingerprint": fp,
            "profiles": [{
                "selection_profile": "score_max",
                "small": {"windows": [
                    window(1, 22, 30, candidate(), 2.0, 1.2),
                    window(2, 30, 38, candidate(momentum=13), -1.0, 0.8),
                ]},
                "large": {"windows": [
                    window(1, 22, 30, candidate(), 2.0, 1.2),
                    window(2, 30, 38, candidate(), -1.0, 0.8),
                ]},
            }],
        }],
    }


def manifest(rows, csv_path):
    return {
        "datasets": [{
            "symbol": "TEST",
            "interval": "1d",
            "byte_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
            "dataset_fingerprint": dataset_fingerprint(rows),
            "candle_count": len(rows),
        }]
    }


def test_exact_archive_and_migration_are_analyzed(tmp_path):
    csv_path = tmp_path / "data" / "TEST" / "1d.csv"
    rows = write_csv(csv_path)
    result = analyze(rolling(rows), manifest(rows, csv_path), tmp_path / "data")
    assert result["archive_integrity"][0]["full_candle_count"] == 40
    assert result["evaluation_count"] == 4
    assert result["migration_summary"]["migration_count"] == 1
    assert result["safety"]["paper_only"] is True


def test_changed_raw_bytes_fail_closed(tmp_path):
    csv_path = tmp_path / "data" / "TEST" / "1d.csv"
    rows = write_csv(csv_path)
    archive = manifest(rows, csv_path)
    csv_path.write_text(csv_path.read_text(encoding="utf-8").replace("1000.0", "1001.0"), encoding="utf-8")
    with pytest.raises(ValueError, match="byte SHA-256 mismatch"):
        analyze(rolling(rows), archive, tmp_path / "data")


def test_regime_definition_is_ex_ante(tmp_path):
    csv_path = tmp_path / "data" / "TEST" / "1d.csv"
    rows = write_csv(csv_path)
    result = analyze(rolling(rows), manifest(rows, csv_path), tmp_path / "data")
    scope = result["interpretation_scope"]
    assert scope["regime_labels_are_ex_ante_relative_to_each_test_start"] is True
    assert scope["no_new_backtest"] is True
    assert scope["no_new_data_download"] is True


def test_analysis_fingerprint_is_deterministic(tmp_path):
    csv_path = tmp_path / "data" / "TEST" / "1d.csv"
    rows = write_csv(csv_path)
    r1 = analyze(rolling(rows), manifest(rows, csv_path), tmp_path / "data")
    r2 = analyze(rolling(rows), manifest(rows, csv_path), tmp_path / "data")
    assert r1["analysis_fingerprint"] == r2["analysis_fingerprint"]
