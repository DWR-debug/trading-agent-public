"""Failure/risk diagnosis for the third independent validation artifact.

Diagnostic-only: consumes one immutable validation artifact and its archived raw
candles. It does not alter signals, parameters, sleeve weights, gates or data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean, pstdev

from automation import candidate_validation_50_50_vol_budget as base
from automation.independent_validation_2026_09_23_third import (
    CS_UNIVERSE,
    TREND_UNIVERSE,
    _manifest,
)
from config import settings
from research.asset_universes import get_universe

RESEARCH_COUNT = base.RESEARCH_COUNT
HOLDOUT_COUNT = base.HOLDOUT_COUNT
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
        if value > 0.0:
            gross_profit += value
            positive += 1
        elif value < 0.0:
            gross_loss -= value

    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": (
            gross_profit / gross_loss if gross_loss else ("inf" if gross_profit else 0.0)
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


def _max_drawdown_interval(rows: list[dict], key: str) -> dict:
    equity = peak = 1.0
    peak_index = 0
    best = (0.0, 0, 0)
    for index, value in enumerate(row[key] for row in rows):
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
        "duration_sessions": best[2] - best[1] + 1,
    }


def _asset_and_sleeve_rows(
    assets,
    trend_weights,
    cs_weights,
    scales,
) -> list[dict]:
    trend_symbols = tuple(get_universe(TREND_UNIVERSE).symbols)
    cs_symbols = tuple(get_universe(CS_UNIVERSE).symbols)
    symbols = tuple(assets)
    rows = []

    for index in range(len(scales)):
        contributions = {}
        for symbol in symbols:
            bars = assets[symbol]
            market_return = (
                bars[index + 2].open / bars[index + 1].open - 1.0
            )
            weight = (
                trend_weights[index].get(symbol, 0.0)
                if symbol in trend_symbols
                else cs_weights[index].get(symbol, 0.0)
            )
            contributions[symbol] = (
                scales[index] * 0.5 * weight * market_return
            )

        rows.append(
            {
                "timestamp": assets[symbols[0]][index + 2].timestamp,
                "trend_return": sum(
                    contributions[symbol] for symbol in trend_symbols
                ),
                "cs_return": sum(
                    contributions[symbol] for symbol in cs_symbols
                ),
                "asset_contributions": contributions,
            }
        )
    return rows


def run_diagnosis(
    artifact_root: Path,
    output_path: Path,
) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-Only-Sicherheitsvertrag verletzt.")

    report_path = (
        artifact_root
        / "research/third_independent_validation_2026_09_23/report.json"
    )
    trend_manifest_path = (
        artifact_root
        / "research/third_independent_validation_2026_09_23/data_trend_manifest.json"
    )
    cs_manifest_path = (
        artifact_root
        / "research/third_independent_validation_2026_09_23/data_cs_manifest.json"
    )
    data_dir = artifact_root / "data/market_data"

    report = json.loads(report_path.read_text(encoding="utf-8"))
    stored_report_fingerprint = report.pop("report_fingerprint")
    if _fingerprint(report) != stored_report_fingerprint:
        raise ValueError("Report-Fingerprint ungültig.")
    if report.get("candidate_status") != "BLOCKED":
        raise ValueError("Diagnose erwartet den archivierten BLOCKED-Report.")

    trend_manifest = _manifest(trend_manifest_path, TREND_UNIVERSE)
    cs_manifest = _manifest(cs_manifest_path, CS_UNIVERSE)
    trend = base._assets(data_dir, trend_manifest)
    cs = base._assets(data_dir, cs_manifest)

    if set(trend) & set(cs):
        raise ValueError("Universen sind nicht disjunkt.")

    trend_weights = base._build_weight_path(trend, base.TREND_STRATEGY)
    cs_weights = base._cs_weights(cs)
    all_assets = {**trend, **cs}
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
    simulated = base._simulate(rows, 1.0, True, False)
    reference = report["scenarios"]["base"]["vol_budget_10pct"]["price_only"]
    expected_count = reference["research"]["day_count"] + reference["holdout"]["day_count"]
    if len(simulated) != expected_count:
        raise ValueError("Simulationslänge stimmt nicht mit dem archivierten Report überein.")

    recomputed = _stats(
        [item["net_return"] for item in simulated[:RESEARCH_COUNT]]
    )["period_return"]
    if abs(recomputed - reference["research"]["period_return"]) > 1e-12:
        raise ValueError("Research-Return-Reproduktion fehlgeschlagen.")

    scales = [item["scale"] for item in simulated]
    detailed = _asset_and_sleeve_rows(
        all_assets,
        trend_weights,
        cs_weights,
        scales,
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
                    trend_values,
                    cs_values,
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
    portfolio_negative_windows = [
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

    failure_signature = {
        "portfolio_negative_window_count": len(portfolio_negative_windows),
        "cross_sectional_negative_window_count": len(cs_negative_windows),
        "trend_negative_window_count": len(trend_negative_windows),
        "cross_sectional_more_negative_windows_than_trend": (
            len(cs_negative_windows) > len(trend_negative_windows)
        ),
        "max_drawdown_interval": _max_drawdown_interval(
            research,
            "net_return",
        ),
        "research_scale": {
            "median": sorted(row["scale"] for row in research)[len(research) // 2],
            "minimum": min(row["scale"] for row in research),
            "fraction_below_0_75": (
                sum(row["scale"] < 0.75 for row in research) / len(research)
            ),
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
        "diagnostic_type": "third_validation_failure_risk_diagnosis_2026_09_23",
        "status": "COMPLETED",
        "input": {
            "source_report_fingerprint": stored_report_fingerprint,
            "source_candidate_status": report["candidate_status"],
            "source_run_code_version": report["code_version"],
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": HOLDOUT_COUNT,
            "trend_universe": list(get_universe(TREND_UNIVERSE).symbols),
            "cs_universe": list(get_universe(CS_UNIVERSE).symbols),
        },
        "windows": windows,
        "failure_signature": failure_signature,
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
    result = run_diagnosis(
        Path(args.artifact_root),
        Path(args.output),
    )
    print("THIRD_FAILURE_DIAGNOSIS_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    print(
        "PORTFOLIO_NEGATIVE_WINDOWS:",
        result["failure_signature"]["portfolio_negative_window_count"],
    )
    print(
        "CS_NEGATIVE_WINDOWS:",
        result["failure_signature"]["cross_sectional_negative_window_count"],
    )
    print(
        "TREND_NEGATIVE_WINDOWS:",
        result["failure_signature"]["trend_negative_window_count"],
    )
    print(
        "MAX_DD_INTERVAL:",
        result["failure_signature"]["max_drawdown_interval"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
