"""Coverage-only discovery against the fixed formal study window.

The candidate order comes from the existing ex-ante asset-universe source
order. No performance, return, holdout, parameter, threshold, or variant data
is consulted. A symbol is valid only when its actual OHLCV timestamps cover
at least 3500 sessions inside the fixed 2011-01-01 through 2025-09-24 window.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path

from config import settings
from data.yahoo_loader import load_yahoo_history
from research.asset_universes import list_universes

ROOT = Path(__file__).resolve().parents[1]
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
TARGET_COMMON_COUNT = 3500
RAW_FETCH_COUNT = 5000
DEFAULT_SYMBOL_LIMIT = 48

# Fixed, ex-ante pool of mature US-listed equities kept outside the existing
# research universes when this pool was created. Order is frozen and contains
# no performance-derived ranking.
CANDIDATE_POOL = (
    "TAP", "CLX", "HSY", "K", "KR", "SYY", "STT", "USB",
    "TROW", "BEN", "NTRS", "PNC", "MET", "PRU", "ALL", "TRV",
    "AFL", "AIZ", "CB", "HIG", "CINF", "GL", "MKC", "ED",
    "PEG", "ETR", "PPL", "WEC", "FE", "D", "EXR", "PSA",
    "O", "SPG", "CCI", "EQIX", "AVB", "EQR", "ESS", "ARE",
    "WY", "PLD", "KIM", "VTR", "DRE", "IRM", "UDR", "MAA",
)


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _fixed_symbol_order() -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for universe in sorted(list_universes(), key=lambda item: (item.priority, item.name)):
        for symbol in universe.symbols:
            if symbol not in seen:
                seen.add(symbol)
                ordered.append(symbol)
    return ordered


def _window_timestamps(symbol: str) -> tuple[list[str], dict]:
    quality: dict[str, int] = {}
    bars = load_yahoo_history(
        symbol,
        "1d",
        RAW_FETCH_COUNT,
        allow_partial=True,
        skip_invalid_ohlc=True,
        quality_report=quality,
    )
    in_window = [
        bar.timestamp.isoformat()
        for bar in bars
        if STUDY_START <= bar.timestamp.date() <= STUDY_END
    ]
    return in_window, quality


def _prior_research_symbols() -> set[str]:
    """Collect symbols already touched by frozen research artifacts/preregistrations."""
    used: set[str] = set()

    ledger = ROOT / "research" / "evidence" / "trial_ledger.json"
    if ledger.exists():
        data = json.loads(ledger.read_text(encoding="utf-8"))
        for trial in data.get("trials", []):
            if not isinstance(trial, dict):
                continue
            scope = trial.get("data_scope", {})
            if not isinstance(scope, dict):
                continue
            for key in ("symbols", "trend_symbols", "cross_sectional_symbols", "requested_symbols", "universe_symbols"):
                values = scope.get(key)
                if isinstance(values, list):
                    used.update(str(v) for v in values)

    prereg_root = ROOT / "research" / "preregistrations"
    if prereg_root.exists():
        for path in sorted(prereg_root.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                continue
            if not isinstance(data, dict):
                continue
            symbols = data.get("symbols")
            if isinstance(symbols, list) and symbols:
                # Design documents without a concrete universe normally have no symbols.
                # Once a concrete universe is registered, its symbols become unavailable
                # for later fresh-disjoint validation.
                used.update(str(v) for v in symbols if isinstance(v, (str, int, float)))

    evidence_root = ROOT / "research" / "evidence"
    if evidence_root.exists():
        for path in sorted(evidence_root.glob("**/*asset_freeze*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                continue
            if not isinstance(data, dict):
                continue
            symbols = data.get("symbols")
            if isinstance(symbols, list):
                used.update(str(v) for v in symbols if isinstance(v, (str, int, float)))

    return used


def run_discovery(
    *,
    output: str | Path,
    symbol_limit: int = DEFAULT_SYMBOL_LIMIT,
    workers: int = 8,
) -> dict:
    if settings.PAPER_ONLY is not True:
        raise RuntimeError("Fixed-window discovery requires PAPER_ONLY=True.")
    if settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Fixed-window discovery requires LIVE_TRADING_ENABLED=False.")
    if settings.ORDERS_ENABLED is not False:
        raise RuntimeError("Fixed-window discovery requires ORDERS_ENABLED=False.")
    if settings.AUTOMATIC_PROMOTION is not False:
        raise RuntimeError("Fixed-window discovery requires AUTOMATIC_PROMOTION=False.")
    if symbol_limit < 1:
        raise ValueError("symbol_limit must be positive.")

    used_symbols = {
        symbol
        for universe in list_universes()
        for symbol in universe.symbols
    }
    used_symbols |= _prior_research_symbols()
    excluded_existing_universe_symbols = [
        symbol for symbol in CANDIDATE_POOL if symbol in used_symbols
    ]
    candidates = [
        symbol for symbol in CANDIDATE_POOL if symbol not in used_symbols
    ][:symbol_limit]
    if not candidates:
        raise RuntimeError(
            "Fixed candidate pool has no unused symbols available for discovery."
        )

    results: dict[str, dict] = {}
    # Cache the exact timestamps returned by the first fetch so coverage
    # selection never mixes two different source snapshots for one run.
    timestamp_cache: dict[str, list[str]] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(_window_timestamps, symbol): symbol for symbol in candidates}
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                timestamps, quality = future.result()
                unique = sorted(set(timestamps))
                timestamp_cache[symbol] = unique
                count = len(unique)
                results[symbol] = {
                    "symbol": symbol,
                    "status": "WINDOW_COVERAGE_VALID" if count >= TARGET_COMMON_COUNT else "DATA_INVALID",
                    "window_count": count,
                    "window_start": unique[0] if unique else None,
                    "window_end": unique[-1] if unique else None,
                    "quality": quality,
                }
            except Exception as exc:
                results[symbol] = {
                    "symbol": symbol,
                    "status": "DATA_INVALID",
                    "window_count": 0,
                    "window_start": None,
                    "window_end": None,
                    "quality": {},
                    "error": str(exc),
                }

    ordered_results = [results[symbol] for symbol in candidates]
    valid = [item for item in ordered_results if item["status"] == "WINDOW_COVERAGE_VALID"]

    selected: list[dict] = []
    timestamp_sets = {item["symbol"]: set(timestamp_cache[item["symbol"]]) for item in valid}
    intersection: set[str] | None = None
    for item in valid:
        ts_set = timestamp_sets[item["symbol"]]
        intersection = ts_set if intersection is None else intersection & ts_set
        if intersection is not None and len(intersection) >= TARGET_COMMON_COUNT:
            selected.append(item)
        if len(selected) >= 12:
            break

    selected_symbols = [item["symbol"] for item in selected]
    intersection_dates = sorted(intersection) if intersection is not None else []
    if len(intersection_dates) > TARGET_COMMON_COUNT:
        intersection_dates = intersection_dates[-TARGET_COMMON_COUNT:]

    payload = {
        "schema_version": "1.0",
        "discovery_id": "FIXED-WINDOW-COVERAGE-DISCOVERY-2026-09-27",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "study_window": {
            "start": STUDY_START.isoformat(),
            "end": STUDY_END.isoformat(),
            "target_common_count": TARGET_COMMON_COUNT,
            "raw_fetch_count": RAW_FETCH_COUNT,
        },
        "source_order_rule": "Fixed CANDIDATE_POOL order is frozen in source; symbols already claimed by registered universes are excluded, then the first unused symbols satisfying only the fixed 2011-01-01 through 2025-09-24 coverage contract are selected.",
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "asset_selection_by_performance": False,
        "candidate_pool_limit": symbol_limit,
        "candidate_pool": list(CANDIDATE_POOL),
        "eligible_candidate_pool": candidates,
        "excluded_existing_universe_symbols": excluded_existing_universe_symbols,
        "results": ordered_results,
        "coverage_valid_candidates": [item["symbol"] for item in valid],
        "selected_coverage_batch": selected_symbols,
        "selected_common_count": len(intersection_dates),
        "selected_common_start": intersection_dates[0] if intersection_dates else None,
        "selected_common_end": intersection_dates[-1] if intersection_dates else None,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    payload["fingerprint"] = _fingerprint(payload)
    out = Path(output)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="research/runs/fixed_window_candidate_discovery/discovery.json")
    parser.add_argument("--symbol-limit", type=int, default=DEFAULT_SYMBOL_LIMIT)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    report = run_discovery(output=args.output, symbol_limit=args.symbol_limit, workers=args.workers)
    print("FIXED_WINDOW_DISCOVERY_STATUS:", "CANDIDATES_AVAILABLE" if report["selected_coverage_batch"] else "NO_COVERAGE_VALID_BATCH")
    print("SELECTED_COVERAGE_BATCH:", report["selected_coverage_batch"])
    print("SELECTED_COMMON_COUNT:", report["selected_common_count"])
    print("DISCOVERY_FINGERPRINT:", report["fingerprint"])
    return 0 if report["selected_coverage_batch"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
