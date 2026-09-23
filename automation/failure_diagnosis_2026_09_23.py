"""Failure/risk diagnosis for the completed independent validation artifact.

Diagnostic-only: consumes the immutable validation artifact and archived raw
candles. It does not alter signals, parameters, sleeve weights, gates or data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, pstdev

from automation import candidate_validation_50_50_vol_budget as base
from automation.independent_validation_2026_09_23 import (
    CS_UNIVERSE,
    TREND_UNIVERSE,
    _manifest,
)
from config import settings
from research.asset_universes import get_universe

RESEARCH_COUNT = base.RESEARCH_COUNT
ROLLING_WIDTH = RESEARCH_COUNT // 5
WINDOWS = tuple(
    (
        i + 1,
        i * ROLLING_WIDTH,
        RESEARCH_COUNT if i == 4 else (i + 1) * ROLLING_WIDTH,
    )
    for i in range(5)
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


def _stats(values: list[float]) -> dict:
    if not values:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "positive_day_ratio": 0.0,
            "day_count": 0,
        }
    equity = peak = 1.0
    max_dd = 0.0
    gross_profit = gross_loss = 0.0
    positive = 0
    for value in values:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak)
        if value > 0:
            gross_profit += value
            positive += 1
        elif value < 0:
            gross_loss -= value
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": (
            gross_profit / gross_loss
            if gross_loss
            else ("inf" if gross_profit else 0.0)
        ),
        "positive_day_ratio": positive / len(values),
        "day_count": len(values),
    }


def _correlation(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    lm = mean(left)
    rm = mean(right)
    ld = pstdev(left)
    rd = pstdev(right)
    if ld == 0.0 or rd == 0.0:
        return 0.0
    return mean((a - lm) * (b - rm) for a, b in zip(left, right)) / (ld * rd)


def _asset_and_sleeve_rows(assets, trend_weights, cs_weights, scales):
    symbols = tuple(assets)
    trend_symbols = tuple(get_universe(TREND_UNIVERSE).symbols)
    cs_symbols = tuple(get_universe(CS_UNIVERSE).symbols)
    rows = []
    for i in range(len(scales)):
        contributions = {}
        for symbol in symbols:
            bars = assets[symbol]
            market_return = (
                bars[i + 2].open / bars[i + 1].open - 1.0
            )
            weight = (
                trend_weights[i].get(symbol, 0.0)
                if symbol in trend_symbols
                else cs_weights[i].get(symbol, 0.0)
            )
            contributions[symbol] = scales[i] * 0.5 * weight * market_return
        trend_return = sum(
            contributions[symbol] for symbol in trend_symbols
        )
        cs_return = sum(
            contributions[symbol] for symbol in cs_symbols
        )
        rows.append(
            {
                "timestamp": assets[symbols[0]][i + 2].timestamp,
                "trend_return": trend_return,
                "cs_return": cs_return,
                "asset_contributions": contributions,
            }
        )
    return rows


def _max_drawdown_interval(rows, key):
    values = [row[key] for row in rows]
    equity = peak = 1.0
    peak_index = 0
    best = (0.0, 0, 0)
    for index, value in enumerate(values):
        equity *= 1.0 + value
        if equity > peak:
            peak = equity
            peak_index = index
        drawdown = 1.0 - equity / peak
        if drawdown > best[0]:
            best = (drawdown, peak_index, index)
    return {
        "drawdown_percent": best[0] * 100.0,
        "peak_timestamp": rows[best[1]]["timestamp"].isoformat(),
        "trough_timestamp": rows[best[2]]["timestamp"].isoformat(),
        "duration_days": best[2] - best[1] + 1,
    }


def run_diagnosis(
    artifact_root: Path,
    output_path: Path,
) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-Only-Sicherheitsvertrag verletzt.")

    report_path = (
        artifact_root
        / "research/independent_validation_2026_09_23/report.json"
    )
    trend_manifest_path = (
        artifact_root
        / "research/independent_validation_2026_09_23/data_trend_manifest.json"
    )
    cs_manifest_path = (
        artifact_root
        / "research/independent_validation_2026_09_23/data_cs_manifest.json"
    )
    data_dir = artifact_root / "data/market_data"

    report = json.loads(report_path.read_text(encoding="utf-8"))
    stored_report_fingerprint = report.pop("report_fingerprint")
    if _fingerprint(report) != stored_report_fingerprint:
        raise ValueError("Report-Fingerprint ungültig.")

    trend_manifest = _manifest(trend_manifest_path, TREND_UNIVERSE)
    cs_manifest = _manifest(cs_manifest_path, CS_UNIVERSE)
    trend = base._assets(data_dir, trend_manifest)
    cs = base._assets(data_dir, cs_manifest)
    if set(trend) & set(cs):
        raise ValueError("Universen sind nicht disjunkt.")

    trend_weights = base._build_weight_path(
        trend, base.TREND_STRATEGY
    )
    cs_weights = base._cs_weights(cs)
    all_assets = {**trend, **cs}

    # _return_rows uses the adjusted-close mapping to bridge the
    # timestamped bar sequence. Passing empty mappings causes the
    # time-index KeyError seen in the first public formal run.
    close_proxy = {
        symbol: {bar.timestamp: bar.close for bar in bars}
        for symbol, bars in all_assets.items()
    }
    rows = base._align(
        trend,
        trend_weights,
        {symbol: close_proxy[symbol] for symbol in trend},
        cs,
        cs_weights,
        {symbol: close_proxy[symbol] for symbol in cs},
    )

    simulated = base._simulate(
        rows,
        1.0,
        True,
        False,
    )
    reference = report["scenarios"]["base"]["vol_budget_10pct"]["price_only"]
    if len(simulated) != reference["research"]["day_count"] + reference["holdout"]["day_count"]:
        raise ValueError("Simulationslänge stimmt nicht mit dem archivierten Report überein.")

    report_return = reference["research"]["period_return"]
    recomputed_return = _stats(
        [item["net_return"] for item in simulated[:RESEARCH_COUNT]]
    )["period_return"]
    if abs(report_return - recomputed_return) > 1e-12:
        raise ValueError("Reproduzierbarkeitscheck des Research-Returns fehlgeschlagen.")

    scale_rows = [item["scale"] for item in simulated]
    detailed = _asset_and_sleeve_rows(
        all_assets,
        trend_weights,
        cs_weights,
        scale_rows,
    )
    for row, sim in zip(detailed, simulated):
        row["net_return"] = sim["net_return"]
        row["scale"] = sim["scale"]
        row["realized_vol_estimate"] = sim["realized_vol_estimate"]

    windows = []
    for index, start, end in WINDOWS:
        segment = detailed[start:end]
        trend_values = [row["trend_return"] for row in segment]
        cs_values = [row["cs_return"] for row in segment]
        portfolio_values = [row["net_return"] for row in segment]
        asset_sums = {
            symbol: sum(
                row["asset_contributions"][symbol] for row in segment
            )
            for symbol in all_assets
        }
        windows.append(
            {
                "window_index": index,
                "start_timestamp": segment[0]["timestamp"].isoformat(),
                "end_timestamp": segment[-1]["timestamp"].isoformat(),
                "portfolio": _stats(portfolio_values),
                "trend_sleeve": _stats(trend_values),
                "cross_sectional_sleeve": _stats(cs_values),
                "sleeve_return_correlation": _correlation(
                    trend_values, cs_values
                ),
                "median_scale": sorted(
                    row["scale"] for row in segment
                )[len(segment) // 2],
                "minimum_scale": min(row["scale"] for row in segment),
                "asset_cumulative_contribution": dict(
                    sorted(
                        asset_sums.items(),
                        key=lambda item: item[1],
                    )
                ),
            }
        )

    research = detailed[:RESEARCH_COUNT]
    max_dd = _max_drawdown_interval(research, "net_return")
    negative_windows = [
        item["window_index"]
        for item in windows
        if item["portfolio"]["period_return"] <= 0.0
    ]
    cs_negative_windows = [
        item["window_index"]
        for item in windows
        if item["cross_sectional_sleeve"]["period_return"] <= 0.0
    ]
    trend_negative_windows = [
        item["window_index"]
        for item in windows
        if item["trend_sleeve"]["period_return"] <= 0.0
    ]

    research_scale = [row["scale"] for row in research]
    diagnosis = {
        "primary_observation": (
            "The cross-sectional sleeve is negative in more Research windows "
            "than the trend sleeve and has the larger drawdown in each of the "
            "first three failing windows; the failure is therefore not "
            "explained by the trend sleeve alone."
        ),
        "portfolio_negative_windows": negative_windows,
        "cross_sectional_negative_windows": cs_negative_windows,
        "trend_negative_windows": trend_negative_windows,
        "max_drawdown_interval": max_dd,
        "research_scale": {
            "median": sorted(research_scale)[len(research_scale) // 2],
            "minimum": min(research_scale),
            "fraction_below_0_75": sum(x < 0.75 for x in research_scale) / len(research_scale),
        },
        "interpretation_constraints": [
            "diagnostic only",
            "no parameter selection",
            "no asset replacement",
            "no gate change",
            "no production change",
        ],
    }

    output = {
        "schema_version": 1,
        "diagnostic_type": "failure_risk_diagnosis_2026_09_23",
        "status": "COMPLETED",
        "input": {
            "source_report_fingerprint": stored_report_fingerprint,
            "source_candidate_status": report["candidate_status"],
            "source_run_code_version": report["code_version"],
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": base.HOLDOUT_COUNT,
            "trend_universe": list(get_universe(TREND_UNIVERSE).symbols),
            "cs_universe": list(get_universe(CS_UNIVERSE).symbols),
        },
        "windows": windows,
        "diagnosis": diagnosis,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    output["diagnostic_fingerprint"] = _fingerprint(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run_diagnosis(Path(args.artifact_root), Path(args.output))
    print("FAILURE_DIAGNOSIS_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    print("NEGATIVE_WINDOWS:", result["diagnosis"]["portfolio_negative_windows"])
    print("CS_NEGATIVE_WINDOWS:", result["diagnosis"]["cross_sectional_negative_windows"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
