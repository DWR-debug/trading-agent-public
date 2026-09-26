"""Research-only coverage repair preflight for H06 sector-neutral residual momentum.

No forward-return evaluation, no holdout use, no parameter search, no asset selection.
The preflight verifies the fixed sector map, common calendar, and signal-history contract.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from datetime import date
from pathlib import Path

from config import settings
from data.yahoo_loader import load_yahoo_history
from research.protocol import dataset_fingerprint
from research.asset_universes import get_universe

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = "validation_2026_09_25_sector_neutral_residual_momentum_repair"
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
TARGET_COMMON_CANDLES = 3500
RESEARCH_CANDLES = 2798
REQUESTED_CANDLES = 4000
LOOKBACK = 252
SKIP = 21

SECTOR_MAP = {
    "technology": ("TXN", "ADI", "AMAT"),
    "healthcare": ("MDT", "SYK", "BDX"),
    "industrials": ("ETN", "ITW", "GD"),
    "consumer_staples": ("CL", "KMB", "GIS"),
    "utilities": ("AEP", "XEL", "DTE"),
}


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_common_calendar() -> dict[str, list]:
    universe = get_universe(UNIVERSE)
    bars_by_symbol: dict[str, list] = {}
    for symbol in universe.symbols:
        bars = load_yahoo_history(
            symbol,
            "1d",
            REQUESTED_CANDLES,
            allow_partial=True,
            skip_invalid_ohlc=True,
        )
        bars = [
            bar
            for bar in bars
            if STUDY_START <= bar.timestamp.date() <= STUDY_END
        ]
        if len(bars) < TARGET_COMMON_CANDLES:
            raise RuntimeError(
                f"{symbol}: only {len(bars)} bars in fixed study window"
            )
        # Keep the full fixed study-window history until the cross-symbol
        # timestamp intersection is formed; only then select the last
        # TARGET_COMMON_CANDLES common timestamps.
        bars_by_symbol[symbol] = bars

    common = set.intersection(
        *[{bar.timestamp for bar in bars} for bars in bars_by_symbol.values()]
    )
    if len(common) < TARGET_COMMON_CANDLES:
        raise RuntimeError(
            f"Common calendar is {len(common)}, expected at least {TARGET_COMMON_CANDLES}"
        )

    timestamps = sorted(common)[-TARGET_COMMON_CANDLES:]
    aligned = {}
    for symbol, bars in bars_by_symbol.items():
        lookup = {bar.timestamp: bar for bar in bars}
        aligned[symbol] = [lookup[timestamp] for timestamp in timestamps]
    return aligned


def _raw_score(closes: list[float], index: int) -> float:
    return (
        closes[index - SKIP] / closes[index - LOOKBACK]
    ) - 1.0


def run(
    *,
    output_path: str | Path =
    "research/runs/wide_search/h06_sector_neutral_residual_momentum_repair_coverage.json",
) -> dict:
    if (
        settings.PAPER_ONLY is not True
        or settings.LIVE_TRADING_ENABLED is not False
        or settings.ORDERS_ENABLED is not False
    ):
        raise RuntimeError("H06 coverage requires the paper-only safety configuration.")

    universe = get_universe(UNIVERSE)
    expected_symbols = tuple(
        symbol for members in SECTOR_MAP.values() for symbol in members
    )
    if tuple(universe.symbols) != expected_symbols:
        raise RuntimeError("Fixed H06 universe does not match its preregistered sector map.")
    if any(len(members) != 3 for members in SECTOR_MAP.values()):
        raise RuntimeError("Each preregistered H06 sector must contain exactly three assets.")

    assets = _load_common_calendar()
    closes = {symbol: [bar.close for bar in bars] for symbol, bars in assets.items()}

    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    snapshot_dir = output.parent / "h06_repair_datasets"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_datasets = []
    for symbol in universe.symbols:
        bars = tuple(assets[symbol])
        csv_path = snapshot_dir / symbol / "1d.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(("timestamp", "open", "high", "low", "close", "volume"))
            for bar in bars:
                writer.writerow((
                    bar.timestamp.isoformat(),
                    bar.open,
                    bar.high,
                    bar.low,
                    bar.close,
                    bar.volume,
                ))
        snapshot_datasets.append({
            "symbol": symbol,
            "interval": "1d",
            "path": str(csv_path.relative_to(ROOT)),
            "candle_count": len(bars),
            "fingerprint": dataset_fingerprint(bars),
        })

    decision_dates = RESEARCH_CANDLES - LOOKBACK
    complete_dates = 0
    nondegenerate_dates = 0
    sector_residual_sum_max_abs = 0.0
    residual_abs_values: list[float] = []

    for index in range(LOOKBACK, RESEARCH_CANDLES):
        raw = {
            symbol: _raw_score(closes[symbol], index)
            for symbol in universe.symbols
        }
        if not all(math.isfinite(value) for value in raw.values()):
            continue
        complete_dates += 1

        residuals = {}
        for sector, members in SECTOR_MAP.items():
            sector_mean = statistics.fmean(raw[symbol] for symbol in members)
            for symbol in members:
                residuals[symbol] = raw[symbol] - sector_mean
            sector_sum = sum(residuals[symbol] for symbol in members)
            sector_residual_sum_max_abs = max(
                sector_residual_sum_max_abs,
                abs(sector_sum),
            )

        dispersion = max(residuals.values()) - min(residuals.values())
        if dispersion > 0.0:
            nondegenerate_dates += 1
        residual_abs_values.extend(abs(value) for value in residuals.values())

    coverage_ready = (
        complete_dates == decision_dates
        and nondegenerate_dates == decision_dates
        and sector_residual_sum_max_abs < 1e-12
    )

    result = {
        "schema_version": "1.0",
        "task_id": "WIDE-SEARCH-H06-SECTOR-NEUTRAL-RESIDUAL-MOMENTUM-REPAIR",
        "hypothesis_id": "H06-REPAIR",
        "recorded_at": date.today().isoformat(),
        "universe": UNIVERSE,
        "repair_of": "WIDE-SEARCH-H06-SECTOR-NEUTRAL-RESIDUAL-MOMENTUM",
        "symbols": list(universe.symbols),
        "sector_map": {key: list(value) for key, value in SECTOR_MAP.items()},
        "research_candles_used": RESEARCH_CANDLES,
        "holdout_candles_unused": TARGET_COMMON_CANDLES - RESEARCH_CANDLES,
        "data_snapshot": {
            "format": "csv_ohlcv_common_calendar",
            "selection_rule": "last_3500_timestamps_from_full_fixed_study_window_intersection",
            "datasets": snapshot_datasets,
        },
        "fixed_signal": {
            "formation_lookback_sessions": LOOKBACK,
            "skip_sessions": SKIP,
            "residualization": "equal_weight_sector_demean",
        },
        "coverage": {
            "status": "COVERAGE_READY" if coverage_ready else "DATA_INSUFFICIENT",
            "decision_dates_expected": decision_dates,
            "complete_decision_dates": complete_dates,
            "nondegenerate_decision_dates": nondegenerate_dates,
            "sector_residual_sum_max_abs": sector_residual_sum_max_abs,
            "median_abs_residual_score": (
                statistics.median(residual_abs_values)
                if residual_abs_values
                else 0.0
            ),
            "calendar_selection_rule": "last_3500_timestamps_from_full_fixed_window_intersection",
            "repair_reason": "Original 3520 request is sliced to the newest bars by Yahoo loader before the fixed 2025-09-24 study cutoff; 4000 preserves the same study window while supplying acquisition headroom.",
            "research_calendar_start": (
                assets[next(iter(assets))][0].timestamp.date().isoformat()
                if assets
                else None
            ),
            "research_calendar_end": (
                assets[next(iter(assets))][RESEARCH_CANDLES - 1].timestamp.date().isoformat()
                if assets and len(assets[next(iter(assets))]) >= RESEARCH_CANDLES
                else None
            ),
            "holdout_calendar_start": (
                assets[next(iter(assets))][RESEARCH_CANDLES].timestamp.date().isoformat()
                if assets and len(assets[next(iter(assets))]) > RESEARCH_CANDLES
                else None
            ),
            "holdout_calendar_end": (
                assets[next(iter(assets))][-1].timestamp.date().isoformat()
                if assets
                else None
            ),
        },
        "governance": {
            "coverage_only": True,
            "performance_evaluation": False,
            "holdout_evaluation": False,
            "holdout_used_for_selection": False,
            "selection_used": False,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["fingerprint"] = _fingerprint(result)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "task_id": result["task_id"],
                "status": result["coverage"]["status"],
                "complete_dates": result["coverage"]["complete_decision_dates"],
                "fingerprint": result["fingerprint"],
            },
            sort_keys=True,
        )
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="research/runs/wide_search/"
        "h06_sector_neutral_residual_momentum_repair_coverage.json",
    )
    args = parser.parse_args()
    run(output_path=args.output)


if __name__ == "__main__":
    main()
