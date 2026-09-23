"""Descriptive sleeve co-movement diagnostic for the second independent validation.

Uses the immutable public validation artifact. No parameter search, no
counterfactual, no gate change, no production mutation and no orders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from automation import candidate_validation_50_50_vol_budget as base
from automation.independent_validation_2026_09_23 import (
    CS_UNIVERSE,
    TREND_UNIVERSE,
)
from config import settings

SOURCE_RUN_ID = 35839443616
SOURCE_ARTIFACT_ID = 10740188093
SOURCE_ARTIFACT_DIGEST = (
    "eed3ec6105dec7bc8616ab989ce6f086107b249f7fa087f6e851709af6e47354"
)
WINDOW_COUNT = 5


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


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = _mean(values)
    return _mean([(value - mean) ** 2 for value in values])


def _covariance(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    left_mean = _mean(left)
    right_mean = _mean(right)
    return _mean(
        [(a - left_mean) * (b - right_mean) for a, b in zip(left, right)]
    )


def _correlation(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    left_var = _variance(left)
    right_var = _variance(right)
    if left_var <= 0.0 or right_var <= 0.0:
        return 0.0
    return _covariance(left, right) / math.sqrt(left_var * right_var)


def _quantile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("Quantil einer leeren Liste.")
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _interaction(
    trend: list[float],
    cs: list[float],
) -> dict[str, float]:
    if len(trend) != len(cs):
        raise ValueError("Sleeve-Zeitreihen unterschiedlich lang.")
    portfolio = [0.5 * a + 0.5 * b for a, b in zip(trend, cs)]
    count = len(portfolio)
    if count == 0:
        raise ValueError("Keine gemeinsamen Beobachtungen.")

    both_negative = sum(
        a < 0.0 and b < 0.0 for a, b in zip(trend, cs)
    )
    trend_negative_cs_positive = sum(
        a < 0.0 and b > 0.0 for a, b in zip(trend, cs)
    )
    trend_positive_cs_negative = sum(
        a > 0.0 and b < 0.0 for a, b in zip(trend, cs)
    )
    worst_cut = _quantile(portfolio, 0.05)
    worst_indices = [
        index for index, value in enumerate(portfolio) if value <= worst_cut
    ]
    worst_trend = [trend[index] for index in worst_indices]
    worst_cs = [cs[index] for index in worst_indices]

    trend_var = _variance([0.5 * value for value in trend])
    cs_var = _variance([0.5 * value for value in cs])
    covariance = _covariance(
        [0.5 * value for value in trend],
        [0.5 * value for value in cs],
    )
    portfolio_var = trend_var + cs_var + 2.0 * covariance

    return {
        "correlation": _correlation(trend, cs),
        "both_negative_rate": both_negative / count,
        "trend_negative_cs_positive_rate": (
            trend_negative_cs_positive / count
        ),
        "trend_positive_cs_negative_rate": (
            trend_positive_cs_negative / count
        ),
        "covariance_share_of_portfolio_variance": (
            (2.0 * covariance / portfolio_var)
            if portfolio_var > 0.0
            else 0.0
        ),
        "worst_5pct_portfolio_cut": worst_cut,
        "worst_5pct_count": float(len(worst_indices)),
        "worst_5pct_correlation": _correlation(
            worst_trend, worst_cs
        ),
    }


def _segment_rows(
    trend_rows: tuple[dict, ...],
    cs_rows: tuple[dict, ...],
    start: int,
    end: int,
) -> dict[str, Any]:
    timestamps = [
        trend_rows[index]["timestamp"]
        for index in range(start, end)
    ]
    trend = [
        0.5 * trend_rows[index]["gross_open"]
        for index in range(start, end)
    ]
    cs = [
        0.5 * cs_rows[index]["gross_open"]
        for index in range(start, end)
    ]
    portfolio = [a + b for a, b in zip(trend, cs)]
    equity = peak = 1.0
    max_dd = 0.0
    for value in portfolio:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak)
    return {
        "start_timestamp": timestamps[0].isoformat(),
        "end_timestamp": timestamps[-1].isoformat(),
        "day_count": len(portfolio),
        "portfolio_period_return": equity - 1.0,
        "portfolio_max_drawdown_percent": max_dd * 100.0,
        "interaction": _interaction(trend, cs),
    }


def analyze(artifact_root: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-Only safety contract violated.")

    root = artifact_root / "research/independent_validation_2026_09_23"
    report = json.loads((root / "report.json").read_text(encoding="utf-8"))
    stored_fp = report.get("report_fingerprint")
    if not isinstance(stored_fp, str) or not stored_fp:
        raise ValueError("Source report fingerprint missing.")
    report_payload = dict(report)
    report_payload.pop("report_fingerprint", None)
    if _fingerprint(report_payload) != stored_fp:
        raise ValueError("Source report fingerprint mismatch.")

    archive = json.loads(
        (root / "adjusted_close_archive.json").read_text(encoding="utf-8")
    )
    archive_fp = archive.get("archive_fingerprint")
    archive_payload = dict(archive)
    archive_payload.pop("archive_fingerprint", None)
    if archive_fp is None or _fingerprint(archive_payload) != archive_fp:
        raise ValueError("Adjusted-close archive fingerprint mismatch.")
    if report["source"]["adjusted_close_archive_fingerprint"] != archive_fp:
        raise ValueError("Adjusted-close archive mismatch.")

    trend_manifest = base._manifest(
        root / "data_trend_manifest.json",
        TREND_UNIVERSE,
    )
    cs_manifest = base._manifest(
        root / "data_cs_manifest.json",
        CS_UNIVERSE,
    )
    data_dir = artifact_root / "data/market_data"
    trend = base._assets(data_dir, trend_manifest)
    cs = base._assets(data_dir, cs_manifest)
    if set(trend) & set(cs):
        raise ValueError("Universen sind nicht disjunkt.")

    adjusted = {
        symbol: {
            datetime.fromisoformat(timestamp): value
            for timestamp, value in values
        }
        for symbol, values in archive["datasets"].items()
    }
    trend_weights = base._build_weight_path(trend, base.TREND_STRATEGY)
    cs_weights = base._cs_weights(cs)

    trend_rows = base._return_rows(
        trend,
        trend_weights,
        {symbol: adjusted[symbol] for symbol in trend},
    )
    cs_rows = base._return_rows(
        cs,
        cs_weights,
        {symbol: adjusted[symbol] for symbol in cs},
    )
    if len(trend_rows) != len(cs_rows):
        raise ValueError("Sleeve-Zeitachsen besitzen unterschiedliche Längen.")
    if any(
        left["timestamp"] != right["timestamp"]
        for left, right in zip(trend_rows, cs_rows)
    ):
        raise ValueError("Sleeve-Zeitachsen sind nicht identisch.")

    aligned = len(trend_rows)
    if aligned != base.RESEARCH_COUNT + base.HOLDOUT_COUNT:
        raise ValueError(f"Unerwartete Return-Anzahl: {aligned}")

    width = base.RESEARCH_COUNT // WINDOW_COUNT
    windows = []
    for window_index in range(WINDOW_COUNT):
        start = window_index * width
        end = base.RESEARCH_COUNT if window_index == WINDOW_COUNT - 1 else start + width
        windows.append(
            {
                "window_index": window_index + 1,
                **_segment_rows(trend_rows, cs_rows, start, end),
            }
        )

    research = _segment_rows(
        trend_rows,
        cs_rows,
        0,
        base.RESEARCH_COUNT,
    )
    holdout = _segment_rows(
        trend_rows,
        cs_rows,
        base.RESEARCH_COUNT,
        aligned,
    )

    result = {
        "schema_version": 1,
        "diagnostic_type": "sleeve_comovement_diagnostic_2026_09_23",
        "status": "COMPLETED",
        "source": {
            "validation_run_id": SOURCE_RUN_ID,
            "artifact_id": SOURCE_ARTIFACT_ID,
            "artifact_digest": SOURCE_ARTIFACT_DIGEST,
            "report_fingerprint": stored_fp,
            "adjusted_close_archive_fingerprint": archive_fp,
            "trend_manifest_fingerprint": trend_manifest["manifest_fingerprint"],
            "cs_manifest_fingerprint": cs_manifest["manifest_fingerprint"],
            "research_return_count": base.RESEARCH_COUNT,
            "holdout_return_count": base.HOLDOUT_COUNT,
            "raw_candle_count_per_asset": base.TARGET_COUNT,
        },
        "methodology": {
            "analysis_unit": "daily 50%-weighted trend and cross-sectional sleeve open-to-open returns",
            "portfolio_definition": "0.5 * trend sleeve + 0.5 * cross-sectional sleeve",
            "interaction_metrics": [
                "sleeve return correlation",
                "joint negative-day rate",
                "opposite-sign day rates",
                "covariance share of portfolio variance",
                "correlation on worst 5% portfolio-return days",
            ],
            "risk_scale_excluded_from_primary_interaction": True,
            "signals_unchanged": True,
            "sleeve_weights_unchanged": True,
            "parameters_searched": False,
            "selection_used": False,
            "gates_changed": False,
            "production_mutated": False,
            "orders_enabled": False,
        },
        "research_overall": research,
        "holdout_overall": holdout,
        "rolling_windows": windows,
        "interpretation_scope": {
            "descriptive_not_causal": True,
            "same_source_artifact": True,
            "same_research_holdout_split": True,
            "no_counterfactual": True,
            "no_parameter_search": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    result["diagnostic_fingerprint"] = _fingerprint(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = analyze(Path(args.artifact_root))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    print("DIAGNOSTIC_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    print(
        "RESEARCH_CORRELATION:",
        result["research_overall"]["interaction"]["correlation"],
    )
    print(
        "RESEARCH_BOTH_NEGATIVE_RATE:",
        result["research_overall"]["interaction"]["both_negative_rate"],
    )
    print(
        "HOLDOUT_CORRELATION:",
        result["holdout_overall"]["interaction"]["correlation"],
    )
    print(
        "HOLDOUT_BOTH_NEGATIVE_RATE:",
        result["holdout_overall"]["interaction"]["both_negative_rate"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
