"""Q038 fixed-order, symbol-disjoint coverage preflight.

This module performs data-availability and common-calendar checks only. It never
computes strategy performance, uses holdout data for selection, or ranks assets
by returns/risk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from config import settings
from data.yahoo_loader import load_yahoo_history
from research.asset_universes import list_universes

ROOT = Path(__file__).resolve().parents[1]

REQUESTED_CANDLES = 4000
TARGET_COMMON_CANDLES = 3500
TARGET_UNIVERSE_SIZE = 8
CANDIDATE_POOL = (
    "IVE",
    "IWL",
    "DLN",
    "DHS",
    "DON",
    "DES",
    "USRT",
    "ITB",
)


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def run_coverage(*, output: str | Path = "research/runs/q038/q038_coverage.json") -> dict:
    if settings.PAPER_ONLY is not True:
        raise RuntimeError("Q038 coverage requires PAPER_ONLY=True.")
    if settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Q038 coverage requires LIVE_TRADING_ENABLED=False.")
    if settings.ORDERS_ENABLED is not False:
        raise RuntimeError("Q038 coverage requires ORDERS_ENABLED=False.")
    if settings.AUTOMATIC_PROMOTION is not False:
        raise RuntimeError("Q038 coverage requires AUTOMATIC_PROMOTION=False.")
    if len(CANDIDATE_POOL) != TARGET_UNIVERSE_SIZE:
        raise RuntimeError("Q038 candidate pool size must equal target universe size.")
    if len(CANDIDATE_POOL) != len(set(CANDIDATE_POOL)):
        raise RuntimeError("Q038 candidate pool contains duplicates.")

    used_symbols = {
        symbol
        for universe in list_universes()
        for symbol in universe.symbols
    }
    overlap = sorted(symbol for symbol in CANDIDATE_POOL if symbol in used_symbols)
    if overlap:
        raise RuntimeError(
            "Q038 candidate pool overlaps an existing registered universe: "
            + ", ".join(overlap)
        )

    accepted: list[str] = []
    common_timestamps: set[object] | None = None
    results: list[dict] = []

    for symbol in CANDIDATE_POOL:
        quality: dict[str, int] = {}
        bars = load_yahoo_history(
            symbol,
            "1d",
            REQUESTED_CANDLES,
            allow_partial=True,
            skip_invalid_ohlc=True,
            quality_report=quality,
        )
        timestamps = {bar.timestamp for bar in bars}
        individual_count = len(timestamps)
        if individual_count < TARGET_COMMON_CANDLES:
            results.append({
                "symbol": symbol,
                "individual_count": individual_count,
                "status": "DATA_INVALID",
                "accepted": False,
                "common_count_if_consumed": (
                    len(common_timestamps & timestamps)
                    if common_timestamps is not None
                    else individual_count
                ),
                "start": min(timestamps).isoformat() if timestamps else None,
                "end": max(timestamps).isoformat() if timestamps else None,
                "quality": quality,
            })
            continue

        proposed_common = (
            timestamps
            if common_timestamps is None
            else common_timestamps & timestamps
        )
        common_count = len(proposed_common)
        accepted_here = common_count >= TARGET_COMMON_CANDLES
        results.append({
            "symbol": symbol,
            "individual_count": individual_count,
            "status": "COVERAGE_VALID" if accepted_here else "COMMON_CALENDAR_INSUFFICIENT",
            "accepted": accepted_here,
            "common_count_if_consumed": common_count,
            "start": min(timestamps).isoformat() if timestamps else None,
            "end": max(timestamps).isoformat() if timestamps else None,
            "quality": quality,
        })
        if accepted_here:
            accepted.append(symbol)
            common_timestamps = proposed_common

    final_common = common_timestamps or set()
    status = (
        "COVERAGE_VALIDATED"
        if len(accepted) == TARGET_UNIVERSE_SIZE
        and len(final_common) >= TARGET_COMMON_CANDLES
        else "DATA_INSUFFICIENT"
    )

    payload = {
        "schema_version": "1.0",
        "coverage_id": "Q038-FRESH-DISJOINT-COVERAGE-2026-09-27",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "candidate_pool": list(CANDIDATE_POOL),
        "requested_candles": REQUESTED_CANDLES,
        "target_common_candles": TARGET_COMMON_CANDLES,
        "target_universe_size": TARGET_UNIVERSE_SIZE,
        "selection_rule": (
            "Fixed source order with consumed-symbol exclusion and common-calendar "
            "feasibility only; no performance or holdout metric is consulted."
        ),
        "results": results,
        "accepted_symbols": accepted,
        "common_calendar_count": len(final_common),
        "common_calendar_start": (
            min(final_common).isoformat() if final_common else None
        ),
        "common_calendar_end": (
            max(final_common).isoformat() if final_common else None
        ),
        "status": status,
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "governance": {
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "family_search": False,
            "asset_performance_selection": False,
            "performance_trial_authorized": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    payload["fingerprint"] = _fingerprint(payload)

    path = Path(output)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="research/runs/q038/q038_coverage.json")
    args = parser.parse_args()
    report = run_coverage(output=args.output)
    print("Q038_STATUS:", report["status"])
    print("Q038_ACCEPTED:", ",".join(report["accepted_symbols"]))
    print("Q038_COMMON_CALENDAR:", report["common_calendar_count"])
    print("Q038_FINGERPRINT:", report["fingerprint"])


if __name__ == "__main__":
    main()
