from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from automation.frontier_feasibility import ILLUSION_LOOKBACK_SESSIONS, illusion_momentum_gap_at

TARGET_COUNT = 3500
STEP = 113


def _load(root: Path, symbols: tuple[str, ...]) -> dict[str, list[dict[str, float | str]]]:
    assets = {}
    for symbol in symbols:
        path = root / symbol / "1d.csv"
        if not path.is_file():
            raise FileNotFoundError(f"missing dataset: {symbol}")
        with path.open(newline="", encoding="utf-8") as handle:
            rows = []
            for row in csv.DictReader(handle):
                rows.append(
                    {
                        "timestamp": row["timestamp"],
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row["volume"]),
                    }
                )
        if len(rows) != TARGET_COUNT:
            raise ValueError(f"{symbol}: expected {TARGET_COUNT} rows, got {len(rows)}")
        assets[symbol] = rows
    return assets


def _mutate(assets: dict, decision_index: int, mode: str) -> dict:
    mutated = {
        symbol: [dict(row) for row in rows]
        for symbol, rows in assets.items()
    }
    for rows in mutated.values():
        if mode == "future":
            for i in range(decision_index + 1, len(rows)):
                rows[i]["close"] *= 7.0 + i
        elif mode == "next":
            i = decision_index + 1
            rows[i]["open"] *= 9.0
            rows[i]["high"] *= 9.0
            rows[i]["low"] *= 0.1
            rows[i]["close"] *= 0.1
    return mutated


def run(universe_root: Path, symbols: tuple[str, ...], output: Path) -> dict:
    assets = _load(universe_root, symbols)
    checks = []
    for index in range(ILLUSION_LOOKBACK_SESSIONS + 1, TARGET_COUNT - 1, STEP):
        original = {
            symbol: illusion_momentum_gap_at(
                [float(row["close"]) for row in assets[symbol]],
                index,
            )
            for symbol in symbols
        }
        future = {
            symbol: illusion_momentum_gap_at(
                [float(row["close"]) for row in mutated[symbol]],
                index,
            )
            for symbol in symbols
        } if False else None
        future_assets = _mutate(assets, index, "future")
        next_assets = _mutate(assets, index, "next")
        future_values = {
            symbol: illusion_momentum_gap_at(
                [float(row["close"]) for row in future_assets[symbol]],
                index,
            )
            for symbol in symbols
        }
        next_values = {
            symbol: illusion_momentum_gap_at(
                [float(row["close"]) for row in next_assets[symbol]],
                index,
            )
            for symbol in symbols
        }
        if original != future_values:
            raise AssertionError(f"future mutation changed C29 at decision {index}")
        if original != next_values:
            raise AssertionError(f"next-session mutation changed C29 at decision {index}")
        checks.append({"decision_index": index, "signals": original})

    checks_fingerprint = hashlib.sha256(
        json.dumps(
            checks,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    result = {
        "schema_version": "1.0",
        "trial_id": "T-2026-09-30-C29-COVERAGE-PIT",
        "status": "PIT_PASSED_NO_PERFORMANCE_EVIDENCE",
        "universe": "validation_2026_09_30_c29_fresh_input",
        "symbols": list(symbols),
        "target_count": TARGET_COUNT,
        "lookback_sessions": ILLUSION_LOOKBACK_SESSIONS,
        "checked_decision_points": len(checks),
        "future_mutation_checks_passed": True,
        "next_session_mutation_checks_passed": True,
        "checks_fingerprint": checks_fingerprint,
        "performance_evaluation": False,
        "oos_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "candidate_ranking": False,
        "candidate_selection": False,
        "performance_authorized": False,
        "governance": {
            "performance_trial_authorized": False,
            "parameter_search": False,
            "threshold_search": False,
            "asset_search": False,
            "horizon_search": False,
            "variant_search": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["report_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("C29_PIT_STATUS:", result["status"])
    print("C29_PIT_CHECKED_DECISION_POINTS:", result["checked_decision_points"])
    print("C29_PIT_REPORT_FINGERPRINT:", result["report_fingerprint"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe-root", required=True)
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(Path(args.universe_root), tuple(args.symbols), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
