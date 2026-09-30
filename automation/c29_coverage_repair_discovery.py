from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from config import settings
from data.yahoo_loader import load_yahoo_history
from research.asset_universes import list_universes

ROOT = Path(__file__).resolve().parents[1]
TARGET_IN_WINDOW = 3500
RAW_FETCH = 5000
START = date(2011, 1, 1)
END = date(2025, 9, 24)
POOL = ("ICE", "MCK", "PNR", "ROP", "HUM", "CMG")


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def fingerprint(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def run(output: str | Path) -> dict:
    assert settings.PAPER_ONLY is True
    assert settings.LIVE_TRADING_ENABLED is False
    assert settings.ORDERS_ENABLED is False
    assert settings.AUTOMATIC_PROMOTION is False

    used = {symbol for universe in list_universes() for symbol in universe.symbols}
    overlap = sorted(set(POOL) & used)
    if overlap:
        raise RuntimeError("REPAIR_POOL_OVERLAPS_EXISTING_UNIVERSE:" + ",".join(overlap))

    rows = []
    for symbol in POOL:
        quality: dict[str, int] = {}
        try:
            bars = load_yahoo_history(
                symbol,
                "1d",
                RAW_FETCH,
                allow_partial=True,
                skip_invalid_ohlc=True,
                quality_report=quality,
            )
            in_window = [bar for bar in bars if START <= bar.timestamp.date() <= END]
            count = len(in_window)
            rows.append({
                "symbol": symbol,
                "rows_returned": len(bars),
                "in_window_count": count,
                "status": "COVERAGE_VALID" if count >= TARGET_IN_WINDOW else "DATA_INVALID",
                "start": in_window[0].timestamp.isoformat() if in_window else None,
                "end": in_window[-1].timestamp.isoformat() if in_window else None,
                "quality": quality,
            })
        except (ValueError, OSError) as exc:
            rows.append({
                "symbol": symbol,
                "rows_returned": 0,
                "in_window_count": 0,
                "status": "DATA_INVALID",
                "start": None,
                "end": None,
                "quality": quality,
                "error": str(exc),
            })

    valid = [row["symbol"] for row in rows if row["status"] == "COVERAGE_VALID"]
    selected = valid[0] if valid else None
    result = {
        "schema_version": "1.0",
        "task_id": "T-2026-09-30-C29-COVERAGE-REPAIR-DISCOVERY",
        "parent_trial_id": "T-2026-09-30-C29-COVERAGE-PIT",
        "status": "COVERAGE_REPAIR_CANDIDATE_AVAILABLE" if selected else "NO_COVERAGE_VALID_REPAIR_CANDIDATE",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "candidate_pool": list(POOL),
        "replacement_rule": "first coverage-valid symbol in fixed source order",
        "minimum_in_window_candles": TARGET_IN_WINDOW,
        "requested_raw_candles": RAW_FETCH,
        "study_window": {"start": START.isoformat(), "end": END.isoformat()},
        "results": rows,
        "coverage_valid_candidates": valid,
        "selected_replacement": selected,
        "selection_basis": "coverage_only_fixed_source_order",
        "performance_evaluation": False,
        "oos_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "candidate_ranking": False,
        "candidate_selection": False,
        "parameter_search": False,
        "threshold_search": False,
        "horizon_search": False,
        "performance_authorized": False,
        "scientific_outcome": "NO_SCIENTIFIC_OUTCOME",
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["fingerprint"] = fingerprint(result)
    path = Path(output)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("C29_REPAIR_DISCOVERY_STATUS:", result["status"])
    print("C29_REPAIR_SELECTED_REPLACEMENT:", selected)
    print("C29_REPAIR_DISCOVERY_FINGERPRINT:", result["fingerprint"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="research/runs/c29_repair_discovery/result.json")
    args = parser.parse_args()
    run(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
