"""H06 sector-neutral residual-momentum PIT mutation harness.

No performance evaluation or holdout selection is performed. The harness checks that
the fixed signal at each decision bar is invariant to any future mutation and to
mutation of the next actionable session, and that prefix truncation reproduces the
same signal. The test is exhaustive across all research decision points.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

RESEARCH_CANDLES = 2798
TARGET_COMMON_CANDLES = 3500
LOOKBACK = 252
SKIP = 21
SYMBOLS = (
    "TXN", "ADI", "AMAT", "MDT", "SYK", "BDX", "ETN", "ITW", "GD",
    "CL", "KMB", "GIS", "AEP", "XEL", "DTE",
)
SECTOR_MAP = {
    "technology": ("TXN", "ADI", "AMAT"),
    "healthcare": ("MDT", "SYK", "BDX"),
    "industrials": ("ETN", "ITW", "GD"),
    "consumer_staples": ("CL", "KMB", "GIS"),
    "utilities": ("AEP", "XEL", "DTE"),
}

@dataclass(frozen=True)
class Bar:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


def _fp(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _load(root: Path) -> dict[str, list[Bar]]:
    assets: dict[str, list[Bar]] = {}
    for symbol in SYMBOLS:
        path = root / symbol / "1d.csv"
        rows: list[Bar] = []
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                rows.append(Bar(
                    timestamp=row["timestamp"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                ))
        if len(rows) != TARGET_COMMON_CANDLES:
            raise ValueError(f"{symbol}: expected {TARGET_COMMON_CANDLES} rows, got {len(rows)}")
        if any(rows[i].timestamp >= rows[i + 1].timestamp for i in range(len(rows) - 1)):
            raise ValueError(f"{symbol}: timestamps not strictly increasing")
        assets[symbol] = rows
    return assets


def _signal(assets: dict[str, list[Bar]], index: int) -> dict[str, float]:
    raw = {
        symbol: assets[symbol][index - SKIP].close / assets[symbol][index - LOOKBACK].close - 1.0
        for symbol in SYMBOLS
    }
    residual: dict[str, float] = {}
    for members in SECTOR_MAP.values():
        mean = sum(raw[symbol] for symbol in members) / len(members)
        for symbol in members:
            residual[symbol] = raw[symbol] - mean
    return residual


def _mutate_future(assets: dict[str, list[Bar]], index: int, include_next: bool) -> dict[str, list[Bar]]:
    out = {symbol: list(bars) for symbol, bars in assets.items()}
    first_future = index + (1 if include_next else 2)
    for symbol in SYMBOLS:
        series = out[symbol]
        for cursor in range(first_future, len(series)):
            bar = series[cursor]
            series[cursor] = Bar(bar.timestamp, bar.open * 0.17, bar.high * 1.83, bar.low * 0.23, bar.close * 1.61, bar.volume * 3.0)
    if include_next and index + 1 < len(out[SYMBOLS[0]]):
        for symbol in SYMBOLS:
            bar = out[symbol][index + 1]
            out[symbol][index + 1] = Bar(bar.timestamp, bar.open * 7.0, bar.high * 8.0, bar.low * 0.11, bar.close * 0.09, bar.volume * 4.0)
    return out


def run(root: Path, output: Path, coverage_result_path: Path) -> dict:
    coverage = json.loads(coverage_result_path.read_text(encoding="utf-8"))
    if coverage.get("coverage", {}).get("status") != "COVERAGE_READY":
        raise ValueError("H06 coverage prerequisite is not COVERAGE_READY")
    if coverage.get("governance", {}).get("performance_trial_authorized") is not False:
        raise ValueError("H06 coverage prerequisite unexpectedly authorizes performance")
    if coverage.get("governance", {}).get("holdout_evaluation") is not False:
        raise ValueError("H06 coverage prerequisite evaluates holdout")
    assets = _load(root)
    checks = []
    last_research_index = RESEARCH_CANDLES - 1
    for index in range(LOOKBACK, last_research_index):
        original = _signal(assets, index)
        prefix_assets = {symbol: bars[: index + 1] for symbol, bars in assets.items()}
        prefix = _signal(prefix_assets, index)
        if original != prefix:
            raise AssertionError(f'prefix truncation changed H06 signal at {index}')
        future = _signal(_mutate_future(assets, index, include_next=False), index)
        if original != future:
            raise AssertionError(f'future mutation changed H06 signal at {index}')
        next_session = _signal(_mutate_future(assets, index, include_next=True), index)
        if original != next_session:
            raise AssertionError(f'next-session mutation changed H06 signal at {index}')
        checks.append({
            "index": index,
            "prefix_truncation_invariant": True,
            "future_mutation_invariant": True,
            "next_session_mutation_invariant": True,
        })

    result = {
        "schema_version": "1.0",
        "trial_id": "H06-REPAIR-2026-09-25",
        "status": "PIT_PASSED",
        "universe": "validation_2026_09_25_sector_neutral_residual_momentum_repair",
        "symbols": list(SYMBOLS),
        "research_candles": RESEARCH_CANDLES,
        "target_common_candles": TARGET_COMMON_CANDLES,
        "checked_decision_points": len(checks),
        "signal_definition": {
            "formation_lookback_sessions": LOOKBACK,
            "skip_sessions": SKIP,
            "raw_score": "close[t-skip] / close[t-lookback] - 1",
            "residualization": "equal_weight_sector_demean",
            "action_rule": "decision_bar_next_bar",
        },
        "checks": {
            "prefix_truncation_checks_passed": True,
            "future_mutation_checks_passed": True,
            "next_session_mutation_checks_passed": True,
        },
        "governance": {
            "performance_evaluation": False,
            "oos_evaluation": False,
            "holdout_evaluation": False,
            "holdout_used_for_selection": False,
            "selection_used": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "coverage_input": {
            "coverage_result": str(coverage_result_path).replace("\\", "/"),
            "coverage_fingerprint": coverage["fingerprint"],
            "snapshot_manifest": "research/runs/wide_search/h06_repair_datasets/snapshot_manifest.json",
            "snapshot_fingerprint": coverage["snapshot_fingerprint"],
            "snapshot_required": True,
        },
        "check_fingerprint": _fp(checks),
    }
    result["report_fingerprint"] = _fp(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("H06_PIT_STATUS:", result["status"])
    print("H06_PIT_CHECKED_DECISION_POINTS:", result["checked_decision_points"])
    print("H06_PIT_REPORT_FINGERPRINT:", result["report_fingerprint"])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--coverage-result", required=True)
    args = parser.parse_args()
    run(Path(args.universe_root), Path(args.output), Path(args.coverage_result))
