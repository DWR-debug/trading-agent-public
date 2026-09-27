"""Performance-free PIT validation for the fixed core signal implementations."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from automation.candidate_validation_50_50_vol_budget import _cs_weights
from automation.cross_asset_trend_replication import _sma_signal


def _fp(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def _load_assets(root: Path, expected_assets: int = 12) -> dict[str, list[SimpleNamespace]]:
    assets = {}
    for csv_path in sorted(root.glob("*/1d.csv")):
        rows = []
        with csv_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                rows.append(SimpleNamespace(
                    timestamp=row["timestamp"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                ))
        if len(rows) != 3500:
            raise ValueError(f"{csv_path.name}: expected 3500 rows, got {len(rows)}")
        if any(rows[i].timestamp >= rows[i + 1].timestamp for i in range(len(rows) - 1)):
            raise ValueError(f"{csv_path}: timestamps are not strictly increasing")
        assets[csv_path.parent.name] = rows
    if len(assets) != expected_assets:
        raise ValueError(f"Expected {expected_assets} assets, got {len(assets)}")
    lengths = {len(rows) for rows in assets.values()}
    if lengths != {3500}:
        raise ValueError("Asset lengths are not uniform at 3500")
    first = next(iter(assets.values()))
    common = [r.timestamp for r in first]
    for symbol, rows in assets.items():
        if [r.timestamp for r in rows] != common:
            raise ValueError(f"{symbol}: timestamp calendar mismatch")
    return assets


def _sma_pit(assets: dict[str, list[SimpleNamespace]]) -> dict[str, object]:
    checked = 0
    baseline_fp = []
    for symbol, rows in assets.items():
        closes = [r.close for r in rows]
        for index in range(199, len(rows) - 1, 37):
            baseline = _sma_signal(closes, index)
            mutated = list(closes)
            for future in range(index + 1, len(mutated)):
                mutated[future] *= 1.7
            if _sma_signal(mutated, index) != baseline:
                raise AssertionError(f"SMA look-ahead detected for {symbol} at {index}")
            checked += 1
            baseline_fp.append([symbol, index, baseline])
    return {"status":"PIT_PASSED","checked_decisions":checked,"fingerprint":_fp(baseline_fp)}


def _cs_pit(assets: dict[str, list[SimpleNamespace]]) -> dict[str, object]:
    baseline = _cs_weights(assets)
    checked = 0
    checks = []
    rebalance_indices = [i for i in range(273, len(next(iter(assets.values())))) if i % 21 == 0]
    for index in rebalance_indices[::7]:
        mutated = {symbol:[SimpleNamespace(**vars(row)) for row in rows] for symbol, rows in assets.items()}
        for rows in mutated.values():
            for future in range(index + 1, len(rows)):
                rows[future].close *= 1.7
                rows[future].open *= 0.2
        candidate = _cs_weights(mutated)
        if candidate[index] != baseline[index]:
            raise AssertionError(f"CS look-ahead detected at {index}")
        checked += 1
        checks.append([index, baseline[index]])
    # Explicitly mutate the next-session OHLC only; decision weights must remain unchanged.
    for index in rebalance_indices[::11]:
        mutated = {symbol:[SimpleNamespace(**vars(row)) for row in rows] for symbol, rows in assets.items()}
        for rows in mutated.values():
            if index + 1 < len(rows):
                rows[index + 1].open *= 9.0
                rows[index + 1].high *= 9.0
                rows[index + 1].low *= 0.2
                rows[index + 1].close *= 0.2
        candidate = _cs_weights(mutated)
        if candidate[index] != baseline[index]:
            raise AssertionError(f"CS next-session return leakage detected at {index}")
    return {"status":"PIT_PASSED","checked_rebalances":checked,"fingerprint":_fp(checks)}


def run(universe_root: Path, output: Path, universe: str, trial_id: str, expected_assets: int = 12) -> dict:
    assets = _load_assets(universe_root, expected_assets=expected_assets)
    sma = _sma_pit(assets)
    cs = _cs_pit(assets)
    report = {
        "schema_version":"1.0",
        "trial_id":trial_id,
        "universe":universe,
        "status":"PIT_PASSED",
        "signal_results":{"trend_sma_50_200":sma,"cs_momentum_12_1_top2":cs},
        "performance_evaluation":False,
        "oos_evaluation":False,
        "holdout_evaluation":False,
        "selection_used":False,
        "holdout_used_for_selection":False,
        "governance":{
            "performance_trial_authorized":False,
            "automatic_promotion":False,
        },
        "safety":{
            "paper_only":True,
            "live_trading_enabled":False,
            "orders_enabled":False,
            "automatic_promotion":False,
        },
    }
    report["report_fingerprint"] = _fp(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--universe", required=True)
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--expected-assets", type=int, default=12)
    args = parser.parse_args()
    report = run(Path(args.universe_root), Path(args.output), args.universe, args.trial_id, expected_assets=args.expected_assets)
    print("T051_PIT_STATUS:", report["status"])
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
