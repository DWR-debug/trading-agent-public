"""Mechanism-only diagnostic for frozen H06 residual momentum.

This diagnostic uses the frozen common-calendar OHLCV snapshot from the H06
coverage run. It evaluates only the research segment. No forward returns,
P&L, holdout observations, parameter search, asset selection, or promotion
decisions are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SYMBOLS = (
    "TXN", "ADI", "AMAT",
    "MDT", "SYK", "BDX",
    "ETN", "ITW", "GD",
    "CL", "KMB", "GIS",
    "AEP", "XEL", "DTE",
)
SECTOR_MAP = {
    "technology": ("TXN", "ADI", "AMAT"),
    "healthcare": ("MDT", "SYK", "BDX"),
    "industrials": ("ETN", "ITW", "GD"),
    "consumer_staples": ("CL", "KMB", "GIS"),
    "utilities": ("AEP", "XEL", "DTE"),
}
TARGET_COMMON_CANDLES = 3500
RESEARCH_CANDLES = 2798
LOOKBACK = 252
SKIP = 21
SOURCE_RUN_ID = 36229318877
SOURCE_ARTIFACT_ID = 10902436135
SOURCE_ARTIFACT_DIGEST = "sha256:8bebfb1198a511809d7a578321b75a8695ef823e9d03146f1be00c65fa26126e"
SOURCE_COVERAGE_FINGERPRINT = "db378f9ebf95ad5b9ce9d90367feb9c1b5c43716fb9e8945984fda6af8712186"
SOURCE_STUDY_START = "2011-10-24"
SOURCE_RESEARCH_END = "2022-12-05"


def _canon(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _load_csv(data_root: Path, symbol: str) -> tuple[list[str], list[float]]:
    path = data_root / symbol / "1d.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "timestamp,open,high,low,close,volume":
        raise ValueError(f"{symbol}: unexpected snapshot header")
    timestamps: list[str] = []
    closes: list[float] = []
    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) != 6:
            raise ValueError(f"{symbol}: malformed CSV row")
        timestamps.append(parts[0])
        closes.append(float(parts[4]))
    if len(timestamps) != TARGET_COMMON_CANDLES:
        raise ValueError(
            f"{symbol}: expected {TARGET_COMMON_CANDLES} candles, got {len(timestamps)}"
        )
    return timestamps, closes


def _spearman(values_a: list[float], values_b: list[float]) -> float:
    order_a = {value: rank for rank, value in enumerate(sorted(values_a), start=1)}
    order_b = {value: rank for rank, value in enumerate(sorted(values_b), start=1)}
    da2 = sum(
        (order_a[a] - order_b[b]) ** 2
        for a, b in zip(values_a, values_b)
    )
    n = len(values_a)
    return 1.0 - (6.0 * da2) / (n * (n * n - 1))


def _pearson(values_a: list[float], values_b: list[float]) -> float:
    mean_a = statistics.fmean(values_a)
    mean_b = statistics.fmean(values_b)
    da = [value - mean_a for value in values_a]
    db = [value - mean_b for value in values_b]
    denom = (sum(x * x for x in da) * sum(y * y for y in db)) ** 0.5
    if denom == 0.0:
        return 0.0
    return sum(x * y for x, y in zip(da, db)) / denom


def _sector_count(selected: tuple[str, ...]) -> int:
    selected_set = set(selected)
    return sum(
        bool(selected_set.intersection(members))
        for members in SECTOR_MAP.values()
    )


def _run(data_root: Path, source_manifest: Path | None = None) -> dict:
    if source_manifest is not None:
        manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
        if manifest.get("fingerprint") != SOURCE_COVERAGE_FINGERPRINT:
            raise ValueError("Source coverage fingerprint mismatch")
        if manifest.get("research_candles_used") != RESEARCH_CANDLES:
            raise ValueError("Source research geometry mismatch")
        if manifest.get("holdout_candles_unused") != 702:
            raise ValueError("Unexpected source holdout geometry")
        if manifest.get("governance", {}).get("holdout_used_for_selection") is not False:
            raise ValueError("Source manifest indicates holdout selection")

    timestamps_by_symbol: dict[str, list[str]] = {}
    closes: dict[str, list[float]] = {}
    for symbol in SYMBOLS:
        timestamps, values = _load_csv(data_root, symbol)
        timestamps_by_symbol[symbol] = timestamps
        closes[symbol] = values

    reference_timestamps = timestamps_by_symbol[SYMBOLS[0]]
    if any(
        timestamps_by_symbol[symbol] != reference_timestamps
        for symbol in SYMBOLS
    ):
        raise ValueError("Frozen snapshot timestamps are not identical across symbols")

    decision_rows: list[dict] = []
    for index in range(LOOKBACK, RESEARCH_CANDLES):
        raw = {
            symbol: (
                closes[symbol][index - SKIP]
                / closes[symbol][index - LOOKBACK]
            ) - 1.0
            for symbol in SYMBOLS
        }
        residual = dict(raw)
        for members in SECTOR_MAP.values():
            mean = statistics.fmean(raw[symbol] for symbol in members)
            for symbol in members:
                residual[symbol] = raw[symbol] - mean

        raw_values = [raw[symbol] for symbol in SYMBOLS]
        residual_values = [residual[symbol] for symbol in SYMBOLS]
        raw_variance = statistics.pvariance(raw_values)
        residual_variance = statistics.pvariance(residual_values)

        raw_top2 = tuple(sorted(SYMBOLS, key=lambda s: raw[s], reverse=True)[:2])
        residual_top2 = tuple(
            sorted(SYMBOLS, key=lambda s: residual[s], reverse=True)[:2]
        )

        within_sector_preserved = True
        for members in SECTOR_MAP.values():
            raw_order = tuple(sorted(members, key=lambda s: raw[s], reverse=True))
            residual_order = tuple(
                sorted(members, key=lambda s: residual[s], reverse=True)
            )
            within_sector_preserved = (
                within_sector_preserved and raw_order == residual_order
            )

        raw_rank = {
            symbol: rank
            for rank, symbol in enumerate(
                sorted(SYMBOLS, key=lambda s: raw[s], reverse=True),
                start=1,
            )
        }
        residual_rank = {
            symbol: rank
            for rank, symbol in enumerate(
                sorted(SYMBOLS, key=lambda s: residual[s], reverse=True),
                start=1,
            )
        }

        decision_rows.append(
            {
                "timestamp": reference_timestamps[index],
                "pearson": _pearson(raw_values, residual_values),
                "spearman": _spearman(raw_values, residual_values),
                "top2_overlap_fraction": (
                    len(set(raw_top2).intersection(residual_top2)) / 2.0
                ),
                "raw_top2_same_sector": _sector_count(raw_top2) == 1,
                "residual_top2_same_sector": _sector_count(residual_top2) == 1,
                "raw_top2_sector_count": _sector_count(raw_top2),
                "residual_top2_sector_count": _sector_count(residual_top2),
                "mean_abs_rank_change": statistics.fmean(
                    abs(raw_rank[symbol] - residual_rank[symbol])
                    for symbol in SYMBOLS
                ),
                "variance_ratio_residual_to_raw": (
                    residual_variance / raw_variance
                    if raw_variance > 0.0
                    else 0.0
                ),
                "within_sector_rank_preserved": within_sector_preserved,
            }
        )

    def aggregate(rows: list[dict]) -> dict:
        mean_overlap = statistics.fmean(
            row["top2_overlap_fraction"] for row in rows
        )
        return {
            "decision_count": len(rows),
            "mean_pearson": statistics.fmean(
                row["pearson"] for row in rows
            ),
            "median_pearson": statistics.median(
                row["pearson"] for row in rows
            ),
            "mean_spearman": statistics.fmean(
                row["spearman"] for row in rows
            ),
            "median_spearman": statistics.median(
                row["spearman"] for row in rows
            ),
            "mean_top2_overlap_fraction": mean_overlap,
            "mean_top2_overlap_percent": 100.0 * mean_overlap,
            "raw_top2_same_sector_percent": 100.0 * statistics.fmean(
                1.0 if row["raw_top2_same_sector"] else 0.0
                for row in rows
            ),
            "residual_top2_same_sector_percent": 100.0 * statistics.fmean(
                1.0 if row["residual_top2_same_sector"] else 0.0
                for row in rows
            ),
            "mean_top2_sector_count_raw": statistics.fmean(
                row["raw_top2_sector_count"] for row in rows
            ),
            "mean_top2_sector_count_residual": statistics.fmean(
                row["residual_top2_sector_count"] for row in rows
            ),
            "mean_abs_rank_change": statistics.fmean(
                row["mean_abs_rank_change"] for row in rows
            ),
            "mean_variance_ratio_residual_to_raw": statistics.fmean(
                row["variance_ratio_residual_to_raw"] for row in rows
            ),
            "within_sector_rank_preserved_percent": 100.0 * statistics.fmean(
                1.0 if row["within_sector_rank_preserved"] else 0.0
                for row in rows
            ),
        }

    window_edges = [
        round(len(decision_rows) * fraction / 5)
        for fraction in range(6)
    ]
    windows = []
    for window_index in range(5):
        rows = decision_rows[
            window_edges[window_index]:window_edges[window_index + 1]
        ]
        windows.append(
            {
                "window_index": window_index + 1,
                **aggregate(rows),
            }
        )

    result = {
        "schema_version": "1.0",
        "task_id": "H06-MECHANISM-DIAGNOSTIC-2026-09-26",
        "hypothesis_id": "H06",
        "diagnostic_type": "mechanism_only",
        "source": {
            "coverage_workflow_run_id": SOURCE_RUN_ID,
            "coverage_artifact_id": SOURCE_ARTIFACT_ID,
            "coverage_artifact_digest": SOURCE_ARTIFACT_DIGEST,
            "coverage_fingerprint": SOURCE_COVERAGE_FINGERPRINT,
            "study_start": SOURCE_STUDY_START,
            "research_end": SOURCE_RESEARCH_END,
            "common_calendar_candles": TARGET_COMMON_CANDLES,
            "research_candles_used": RESEARCH_CANDLES,
            "holdout_candles_used": 0,
        },
        "fixed_design": {
            "symbols": list(SYMBOLS),
            "sector_map": {
                key: list(value) for key, value in SECTOR_MAP.items()
            },
            "formation_lookback_sessions": LOOKBACK,
            "skip_sessions": SKIP,
            "raw_signal": "252-session return with 21-session skip",
            "residual_signal": (
                "raw signal minus equal-weight sector mean"
            ),
            "selection_rule": "descriptive_only_no_selection",
        },
        "findings": {
            "aggregate": aggregate(decision_rows),
            "temporal_windows": windows,
        },
        "governance": {
            "forward_returns_used": False,
            "pnl_used": False,
            "holdout_used": False,
            "parameter_search": False,
            "asset_selection": False,
            "threshold_selection": False,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
        },
        "scientific_interpretation": (
            "Descriptive mechanism diagnostic only. It tests whether sector "
            "residualization materially changes cross-sectional signal geometry "
            "relative to raw momentum; it does not test profitability or promotion."
        ),
    }
    result["fingerprint"] = _fingerprint(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument(
        "--output",
        default="research/runs/wide_search/h06_mechanism_diagnostic_2026_09_26.json",
    )
    args = parser.parse_args()
    result = _run(Path(args.data_root), Path(args.source_manifest))
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "task_id": result["task_id"],
                "fingerprint": result["fingerprint"],
                "decision_count": result["findings"]["aggregate"]["decision_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
