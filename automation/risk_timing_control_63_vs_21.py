"""Predeclared paired control for risk-layer response timing.

Baseline: fixed candidate with 63-session realized volatility.
Counterfactual: same fixed candidate with exactly one change, 21-session
realized volatility. No parameter search.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from automation.candidate_validation_50_50_vol_budget import (
    FEE_RATE,
    HOLDOUT_COUNT,
    RESEARCH_COUNT,
    SLIPPAGE_RATE,
    TARGET_COUNT,
    TARGET_VOL,
    TREND_STRATEGY,
    _align,
    _assets,
    _build_weight_path,
    _cs_weights,
    _manifest,
    _scenario,
)
from automation.independent_validation_2026_09_23 import (
    CS_UNIVERSE,
    TREND_UNIVERSE,
)
from config import settings

SOURCE_RUN_ID = 35839443616
SOURCE_ARTIFACT_ID = 10740188093
SOURCE_ARTIFACT_DIGEST = "sha256:eed3ec6105dec7bc8616ab989ce6f086107b249f7fa087f6e851709af6e47354"
BASELINE_VOL_WINDOW = 63
COUNTERFACTUAL_VOL_WINDOW = 21


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _vol(history: list[float], window: int) -> float | None:
    if len(history) < window:
        return None
    sample = history[-window:]
    mean = sum(sample) / len(sample)
    variance = sum((x - mean) ** 2 for x in sample) / len(sample)
    return math.sqrt(variance) * math.sqrt(252.0)


def _simulate(rows: tuple[dict[str, Any], ...], window: int) -> list[dict[str, Any]]:
    if window <= 0:
        raise ValueError("window must be positive")
    history: list[float] = []
    previous_scale = 1.0
    cost_rate = FEE_RATE + SLIPPAGE_RATE
    output = []
    for row in rows:
        realized_vol = _vol(history, window)
        scale = 1.0
        if realized_vol is not None and realized_vol > TARGET_VOL:
            scale = min(1.0, TARGET_VOL / realized_vol)
        turnover = scale * row["turnover"] + abs(scale - previous_scale)
        net = scale * row["gross_open"] - cost_rate * turnover
        output.append({
            "timestamp": row["timestamp"],
            "scale": scale,
            "net_return": net,
            "gross_return": scale * row["gross_open"],
            "realized_vol_estimate": realized_vol,
        })
        previous_scale = scale
        history.append(row["gross_open"] - cost_rate * row["turnover"])
    return output


def _stats(rows: list[dict[str, Any]], start: int, end: int) -> dict[str, Any]:
    segment = rows[start:end]
    if not segment:
        return {"period_return": 0.0, "max_drawdown_percent": 0.0, "profit_factor": 0.0, "day_count": 0}
    equity = peak = 1.0
    max_dd = 0.0
    gp = gl = 0.0
    scales = []
    for row in segment:
        value = row["net_return"]
        scales.append(row["scale"])
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak if equity > 0 else 1.0)
        if value > 0.0:
            gp += value
        elif value < 0.0:
            gl -= value
    pf = gp / gl if gl > 0.0 else ("inf" if gp > 0.0 else 0.0)
    ordered = sorted(scales)
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": pf,
        "day_count": len(segment),
        "median_scale": ordered[len(ordered) // 2],
        "minimum_scale": min(scales),
    }


def _rolling(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    width = RESEARCH_COUNT // 5
    out = []
    start = 0
    for index in range(5):
        end = RESEARCH_COUNT if index == 4 else start + width
        out.append({"window_index": index + 1, **_stats(rows, start, end)})
        start = end
    return out


def _summary(rows: list[dict[str, Any]], windows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [row["net_return"] for row in rows]
    gp = sum(x for x in values if x > 0.0)
    gl = -sum(x for x in values if x < 0.0)
    equity = 1.0
    for value in values:
        equity *= 1.0 + value
    return {
        "window_count": len(windows),
        "profitable_windows": sum(x["period_return"] > 0.0 for x in windows),
        "profitable_window_ratio": sum(x["period_return"] > 0.0 for x in windows) / len(windows),
        "total_net_return": equity - 1.0,
        "overall_profit_factor": gp / gl if gl > 0.0 else ("inf" if gp > 0.0 else 0.0),
        "average_drawdown_percent": sum(x["max_drawdown_percent"] for x in windows) / len(windows),
    }


def _run(rows: tuple[dict[str, Any], ...], window: int) -> dict[str, Any]:
    values = _simulate(rows, window)
    rolling = _rolling(values)
    return {
        "vol_window_sessions": window,
        "research": _stats(values, 0, RESEARCH_COUNT),
        "holdout": _stats(values, RESEARCH_COUNT, len(values)),
        "rolling_windows": rolling,
        "rolling_summary": _summary(values[:RESEARCH_COUNT], rolling),
    }


def _delta(baseline: dict[str, Any], counterfactual: dict[str, Any]) -> dict[str, Any]:
    return {
        "research_return_delta_percentage_points": (counterfactual["research"]["period_return"] - baseline["research"]["period_return"]) * 100.0,
        "research_drawdown_delta_percentage_points": counterfactual["research"]["max_drawdown_percent"] - baseline["research"]["max_drawdown_percent"],
        "research_profit_factor_delta": float(counterfactual["research"]["profit_factor"]) - float(baseline["research"]["profit_factor"]),
        "holdout_return_delta_percentage_points": (counterfactual["holdout"]["period_return"] - baseline["holdout"]["period_return"]) * 100.0,
        "holdout_drawdown_delta_percentage_points": counterfactual["holdout"]["max_drawdown_percent"] - baseline["holdout"]["max_drawdown_percent"],
        "holdout_profit_factor_delta": float(counterfactual["holdout"]["profit_factor"]) - float(baseline["holdout"]["profit_factor"]),
        "rolling": [
            {
                "window_index": left["window_index"],
                "baseline_return": left["period_return"],
                "counterfactual_return": right["period_return"],
                "return_delta_percentage_points": (right["period_return"] - left["period_return"]) * 100.0,
                "baseline_drawdown_percent": left["max_drawdown_percent"],
                "counterfactual_drawdown_percent": right["max_drawdown_percent"],
                "drawdown_delta_percentage_points": right["max_drawdown_percent"] - left["max_drawdown_percent"],
                "baseline_profit_factor": left["profit_factor"],
                "counterfactual_profit_factor": right["profit_factor"],
                "profit_factor_delta": float(right["profit_factor"]) - float(left["profit_factor"]),
            }
            for left, right in zip(baseline["rolling_windows"], counterfactual["rolling_windows"])
        ],
    }


def analyze(artifact_root: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-Only safety contract violated.")

    report = json.loads(
        (artifact_root / "research/independent_validation_2026_09_23/report.json").read_text(
            encoding="utf-8"
        )
    )
    stored_fp = report.get("report_fingerprint")
    if not isinstance(stored_fp, str) or not stored_fp:
        raise ValueError("Source report fingerprint missing.")
    payload = dict(report)
    payload.pop("report_fingerprint", None)
    if _fingerprint(payload) != stored_fp:
        raise ValueError("Source report fingerprint mismatch.")

    archive_path = (
        artifact_root
        / "research/independent_validation_2026_09_23/adjusted_close_archive.json"
    )
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    archive_fp = archive.get("archive_fingerprint")
    archive_payload = dict(archive)
    archive_payload.pop("archive_fingerprint", None)
    if archive_fp is None or _fingerprint(archive_payload) != archive_fp:
        raise ValueError("Adjusted-close archive fingerprint mismatch.")
    if report["source"]["adjusted_close_archive_fingerprint"] != archive_fp:
        raise ValueError("Adjusted-close archive does not match source report.")

    trend_manifest = _manifest(
        artifact_root / "research/independent_validation_2026_09_23/data_trend_manifest.json",
        TREND_UNIVERSE,
    )
    cs_manifest = _manifest(
        artifact_root / "research/independent_validation_2026_09_23/data_cs_manifest.json",
        CS_UNIVERSE,
    )
    data_dir = artifact_root / "data/market_data"
    trend = _assets(data_dir, trend_manifest)
    cs = _assets(data_dir, cs_manifest)
    if set(trend) & set(cs):
        raise ValueError("Validation universes are not disjoint.")

    trend_weights = _build_weight_path(trend, TREND_STRATEGY)
    cs_weights = _cs_weights(cs)
    close_proxy = {
        symbol: {bar.timestamp: bar.close for bar in bars}
        for symbol, bars in {**trend, **cs}.items()
    }
    from datetime import datetime

    adjusted = {
        symbol: {
            datetime.fromisoformat(timestamp): value
            for timestamp, value in values
        }
        for symbol, values in archive["datasets"].items()
    }
    rows = _align(
        trend,
        trend_weights,
        {symbol: adjusted[symbol] for symbol in trend},
        cs,
        cs_weights,
        {symbol: adjusted[symbol] for symbol in cs},
    )
    if len(rows) != RESEARCH_COUNT + HOLDOUT_COUNT:
        raise ValueError("Unexpected aligned return count.")

    baseline_expected = report["scenarios"]["base"]["vol_budget_10pct"]["price_only"]
    baseline_source = _scenario(rows, 1.0)["vol_budget_10pct"]["price_only"]
    if _canonical(baseline_source) != _canonical(baseline_expected):
        raise ValueError("63-session baseline does not reproduce the source report.")

    baseline = _run(rows, BASELINE_VOL_WINDOW)
    counterfactual = _run(rows, COUNTERFACTUAL_VOL_WINDOW)

    result = {
        "schema_version": 1,
        "diagnostic_type": "risk_timing_control_63_vs_21",
        "status": "COMPLETED",
        "source": {
            "candidate_validation_run_id": SOURCE_RUN_ID,
            "candidate_report_fingerprint": stored_fp,

            "trend_manifest_fingerprint": trend_manifest["manifest_fingerprint"],
            "cs_manifest_fingerprint": cs_manifest["manifest_fingerprint"],
            "raw_candle_count_per_asset": TARGET_COUNT,
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": HOLDOUT_COUNT,
            "new_data_downloads": False,
        },
        "hypothesis": {
            "question": "Does one predeclared faster realized-volatility estimator reduce the diagnosed risk-layer response lag?",
            "baseline_vol_window_sessions": BASELINE_VOL_WINDOW,
            "counterfactual_vol_window_sessions": COUNTERFACTUAL_VOL_WINDOW,
            "target_annualized_volatility": TARGET_VOL,
            "all_other_candidate_components_fixed": True,
            "parameter_search": False,
            "selection": False,
        },
        "baseline_63": baseline,
        "counterfactual_21": counterfactual,
        "delta_counterfactual_minus_baseline": _delta(baseline, counterfactual),
        "interpretation_scope": {
            "paired_same_data": True,
            "paired_same_split": True,
            "paired_same_execution_model": True,
            "paired_same_costs": True,
            "paired_same_signals": True,
            "paired_same_sleeves": True,
            "no_gate_recomputation_for_counterfactual": True,
            "descriptive_not_causal": True,
            "not_a_global_parameter_recommendation": True,
            "single_preregistered_counterfactual": True,
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
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")

    print("CONTROL_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    print("BASELINE_RESEARCH_DD:", result["baseline_63"]["research"]["max_drawdown_percent"])
    print("COUNTERFACTUAL_RESEARCH_DD:", result["counterfactual_21"]["research"]["max_drawdown_percent"])
    print("BASELINE_HOLDOUT_DD:", result["baseline_63"]["holdout"]["max_drawdown_percent"])
    print("COUNTERFACTUAL_HOLDOUT_DD:", result["counterfactual_21"]["holdout"]["max_drawdown_percent"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
