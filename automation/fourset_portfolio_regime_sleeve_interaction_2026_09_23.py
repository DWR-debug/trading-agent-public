"""Four-set descriptive portfolio-regime and sleeve-interaction diagnosis.

This extends the existing two-set interaction diagnosis to all four immutable
validation families. It does not modify the candidate.

Research-only:
- fixed 50/50 candidate
- fixed 63-session / 10% de-risking layer
- fixed five Research rolling windows per validation
- Holdout is not reported and cannot affect classification
- no parameter search, selection, gate changes, or production mutation
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
from config import settings
from research.asset_universes import get_universe

RESEARCH_COUNT = base.RESEARCH_COUNT
WINDOW_COUNT = 5

CASES = (
    {
        "name": "validation_1",
        "artifact_id": 10751817990,
        "run_id": 35865847394,
        "root": "research/candidate_validation",
        "trend_universe": "validation_trend",
        "cs_universe": "validation_cs",
    },
    {
        "name": "validation_2",
        "artifact_id": 10740188093,
        "run_id": 35839443616,
        "root": "research/independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_trend",
        "cs_universe": "validation_2026_09_23_cs",
    },
    {
        "name": "validation_3",
        "artifact_id": 10745697729,
        "run_id": 35851876264,
        "root": "research/third_independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_third_trend",
        "cs_universe": "validation_2026_09_23_third_cs",
    },
    {
        "name": "validation_4",
        "artifact_id": 10753545703,
        "run_id": 35867637587,
        "run_id_expected": 35867637587,
        "root": "research/fourth_independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_fourth_trend",
        "cs_universe": "validation_2026_09_23_fourth_cs",
    },
)


def _canon(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode()).hexdigest()


def _load_sleeves(
    source_root: Path,
    case: dict[str, Any],
) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    root = source_root / case["root"]
    report = json.loads((root / "report.json").read_text(encoding="utf-8"))
    stored_report_fp = report["report_fingerprint"]
    report_payload = dict(report)
    report_payload.pop("report_fingerprint", None)
    if _fp(report_payload) != stored_report_fp:
        raise ValueError(f'{case["name"]}: report fingerprint mismatch')
    if report["status"] != "COMPLETED":
        raise ValueError(f'{case["name"]}: source report not completed')
    if report["candidate_status"] != "BLOCKED":
        raise ValueError(f'{case["name"]}: source candidate must remain BLOCKED')
    if report["source"]["independent_asset_universes"] is not True:
        raise ValueError(f'{case["name"]}: independence flag missing')

    archive = json.loads(
        (root / "adjusted_close_archive.json").read_text(encoding="utf-8")
    )
    stored_archive_fp = archive["archive_fingerprint"]
    archive_payload = dict(archive)
    archive_payload.pop("archive_fingerprint", None)
    if _fp(archive_payload) != stored_archive_fp:
        raise ValueError(f'{case["name"]}: archive fingerprint mismatch')
    if stored_archive_fp != report["source"]["adjusted_close_archive_fingerprint"]:
        raise ValueError(f'{case["name"]}: report/archive mismatch')

    trend_manifest = base._manifest(
        root / "data_trend_manifest.json",
        case["trend_universe"],
    )
    cs_manifest = base._manifest(
        root / "data_cs_manifest.json",
        case["cs_universe"],
    )
    data_dir = source_root / "data/market_data"

    trend = base._assets(data_dir, trend_manifest)
    cs = base._assets(data_dir, cs_manifest)
    if set(trend) & set(cs):
        raise ValueError(f'{case["name"]}: trend/CS universes overlap')

    adjusted = {
        symbol: {
            datetime.fromisoformat(ts): float(value)
            for ts, value in values
        }
        for symbol, values in archive["datasets"].items()
    }

    trend_weights = base._build_weight_path(trend, base.TREND_STRATEGY)
    cs_weights = base._cs_weights(cs)

    trend_rows = {
        row["timestamp"]: row
        for row in base._return_rows(
            trend,
            trend_weights,
            {symbol: adjusted[symbol] for symbol in trend},
        )
    }
    cs_rows = {
        row["timestamp"]: row
        for row in base._return_rows(
            cs,
            cs_weights,
            {symbol: adjusted[symbol] for symbol in cs},
        )
    }

    common = sorted(set(trend_rows) & set(cs_rows))
    expected = RESEARCH_COUNT + base.HOLDOUT_COUNT
    if len(common) != expected:
        raise ValueError(
            f'{case["name"]}: unexpected common return count {len(common)}'
        )

    return (
        tuple(trend_rows[ts] for ts in common),
        tuple(cs_rows[ts] for ts in common),
    )


def _window_bounds() -> tuple[tuple[int, int], ...]:
    width = RESEARCH_COUNT // WINDOW_COUNT
    bounds = []
    start = 0
    for index in range(WINDOW_COUNT):
        end = RESEARCH_COUNT if index == WINDOW_COUNT - 1 else start + width
        bounds.append((start, end))
        start = end
    return tuple(bounds)


def _corr(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or len(a) < 2:
        return 0.0
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if va <= 0.0 or vb <= 0.0:
        return 0.0
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return cov / math.sqrt(va * vb)


def _stats_return(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {"period_return": 0.0, "max_drawdown_percent": 0.0, "profit_factor": 0.0}
    equity = peak = 1.0
    gp = gl = 0.0
    max_dd = 0.0
    for row in rows:
        value = row["net_return"]
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak if equity > 0 else 1.0)
        gp += max(value, 0.0)
        gl += max(-value, 0.0)
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": gp / gl if gl > 0 else ("inf" if gp > 0 else 0.0),
    }


def _window_diagnosis(
    trend_sim: list[dict[str, Any]],
    cs_sim: list[dict[str, Any]],
    portfolio_sim: list[dict[str, Any]],
    start: int,
    end: int,
) -> dict[str, Any]:
    t = _stats_return(trend_sim[start:end])
    c = _stats_return(cs_sim[start:end])
    p = _stats_return(portfolio_sim[start:end])

    trend_neg = t["period_return"] < 0
    cs_neg = c["period_return"] < 0
    port_neg = p["period_return"] < 0

    if trend_neg and cs_neg:
        failure_class = "joint_sleeve_weakness"
    elif trend_neg:
        failure_class = "trend_only_weakness"
    elif cs_neg:
        failure_class = "cross_sectional_only_weakness"
    else:
        failure_class = "no_sleeve_negative"

    scales = [row["scale"] for row in portfolio_sim[start:end]]
    gross_t = [row["gross_return"] for row in trend_sim[start:end]]
    gross_c = [row["gross_return"] for row in cs_sim[start:end]]
    gross_p = [row["gross_return"] for row in portfolio_sim[start:end]]

    return {
        "window_start_index": start,
        "window_end_index_exclusive": end,
        "portfolio_period_return": p["period_return"],
        "portfolio_drawdown_percent": p["max_drawdown_percent"],
        "portfolio_profit_factor": p["profit_factor"],
        "trend_period_return": t["period_return"],
        "trend_drawdown_percent": t["max_drawdown_percent"],
        "trend_profit_factor": t["profit_factor"],
        "cross_sectional_period_return": c["period_return"],
        "cross_sectional_drawdown_percent": c["max_drawdown_percent"],
        "cross_sectional_profit_factor": c["profit_factor"],
        "portfolio_negative": port_neg,
        "trend_negative": trend_neg,
        "cross_sectional_negative": cs_neg,
        "failure_class": failure_class,
        "both_sleeves_negative": trend_neg and cs_neg,
        "de_risk_fraction": sum(scale < 1.0 for scale in scales) / len(scales),
        "mean_scale": sum(scales) / len(scales),
        "median_scale": sorted(scales)[len(scales) // 2],
        "minimum_scale": min(scales),
        "trend_portfolio_return_corr": _corr(gross_t, gross_p),
        "cs_portfolio_return_corr": _corr(gross_c, gross_p),
        "sleeve_return_corr": _corr(gross_t, gross_c),
    }


def _case_consensus(windows: list[dict[str, Any]]) -> dict[str, Any]:
    negative = [w for w in windows if w["portfolio_negative"]]
    joint = [w for w in negative if w["both_sleeves_negative"]]
    trend_only = [w for w in negative if w["failure_class"] == "trend_only_weakness"]
    cs_only = [w for w in negative if w["failure_class"] == "cross_sectional_only_weakness"]

    return {
        "negative_portfolio_windows": len(negative),
        "joint_sleeve_weakness_windows": len(joint),
        "joint_sleeve_weakness_rate": len(joint) / len(negative) if negative else 0.0,
        "trend_only_weakness_windows": len(trend_only),
        "cross_sectional_only_weakness_windows": len(cs_only),
        "mean_de_risk_fraction_negative_windows": (
            sum(w["de_risk_fraction"] for w in negative) / len(negative)
            if negative
            else None
        ),
        "mean_de_risk_fraction_positive_windows": (
            sum(w["de_risk_fraction"] for w in windows if not w["portfolio_negative"])
            / len([w for w in windows if not w["portfolio_negative"]])
            if any(not w["portfolio_negative"] for w in windows)
            else None
        ),
        "mean_sleeve_return_corr_negative_windows": (
            sum(w["sleeve_return_corr"] for w in negative) / len(negative)
            if negative
            else None
        ),
    }


def analyze_case(
    trend_rows: tuple[dict[str, Any], ...],
    cs_rows: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    portfolio_rows = tuple(
        {
            "timestamp": t["timestamp"],
            "gross_open": 0.5 * t["gross_open"] + 0.5 * c["gross_open"],
            "gross_close": 0.5 * t["gross_close"] + 0.5 * c["gross_close"],
            "gross_adjusted_close": (
                0.5 * t["gross_adjusted_close"]
                + 0.5 * c["gross_adjusted_close"]
            ),
            "turnover": 0.5 * t["turnover"] + 0.5 * c["turnover"],
        }
        for t, c in zip(trend_rows, cs_rows)
    )

    trend_sim = base._simulate(trend_rows, 1.0, False, False)
    cs_sim = base._simulate(cs_rows, 1.0, False, False)
    portfolio_sim = base._simulate(portfolio_rows, 1.0, True, False)

    windows = [
        _window_diagnosis(
            trend_sim,
            cs_sim,
            portfolio_sim,
            start,
            end,
        )
        for start, end in _window_bounds()
    ]

    return {
        "windows": windows,
        "consensus": _case_consensus(windows),
        "full_research_portfolio": _stats_return(portfolio_sim[:RESEARCH_COUNT]),
    }


def analyze(source_root: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    cases = {}
    for case in CASES:
        trend_rows, cs_rows = _load_sleeves(source_root, case)
        cases[case["name"]] = {
            "source": {
                "validation_run_id": case["run_id"],
                "artifact_id": case["artifact_id"],
                "trend_symbols": list(get_universe(case["trend_universe"]).symbols),
                "cs_symbols": list(get_universe(case["cs_universe"]).symbols),
            },
            "analysis": analyze_case(trend_rows, cs_rows),
        }

    all_windows = [
        window
        for case in cases.values()
        for window in case["analysis"]["windows"]
    ]
    negative = [w for w in all_windows if w["portfolio_negative"]]
    joint = [w for w in negative if w["both_sleeves_negative"]]
    trend_only = [w for w in negative if w["failure_class"] == "trend_only_weakness"]
    cs_only = [w for w in negative if w["failure_class"] == "cross_sectional_only_weakness"]

    result = {
        "schema_version": 1,
        "diagnostic_type": "fourset_portfolio_regime_sleeve_interaction_2026_09_23",
        "status": "COMPLETED",
        "question": (
            "Across all four independent validations and 20 fixed Research "
            "windows, are negative portfolio windows predominantly caused by "
            "joint sleeve weakness, one sleeve alone, or insufficient de-risking?"
        ),
        "scope": {
            "datasets": 4,
            "research_windows": 20,
            "research_return_count_per_dataset": RESEARCH_COUNT,
            "holdout_used_for_decision": False,
            "holdout_metrics_reported": False,
            "new_data_downloads": False,
            "parameter_search": False,
            "asset_selection": False,
            "gate_changes": False,
            "production_mutation": False,
        },
        "methodology": {
            "candidate_architecture_fixed": True,
            "sleeve_weight_trend": 0.5,
            "sleeve_weight_cross_sectional": 0.5,
            "risk_layer_window_sessions": base.VOL_WINDOW,
            "risk_layer_target_annualized_volatility": base.TARGET_VOL,
            "failure_window_definition": "portfolio Research rolling window period_return < 0",
            "joint_weakness_definition": "Trend and Cross-Sectional Research window returns both < 0",
            "de_risk_metrics_descriptive_only": True,
            "same_pit_semantics": True,
            "same_cost_model": True,
            "descriptive_not_causal": True,
        },
        "cases": cases,
        "aggregate": {
            "negative_portfolio_windows": len(negative),
            "joint_sleeve_weakness_windows": len(joint),
            "joint_sleeve_weakness_rate": len(joint) / len(negative) if negative else 0.0,
            "trend_only_weakness_windows": len(trend_only),
            "cross_sectional_only_weakness_windows": len(cs_only),
            "mean_negative_window_de_risk_fraction": (
                sum(w["de_risk_fraction"] for w in negative) / len(negative)
                if negative
                else None
            ),
            "mean_positive_window_de_risk_fraction": (
                sum(w["de_risk_fraction"] for w in all_windows if not w["portfolio_negative"])
                / len([w for w in all_windows if not w["portfolio_negative"]])
                if any(not w["portfolio_negative"] for w in all_windows)
                else None
            ),
            "mean_negative_window_sleeve_return_corr": (
                sum(w["sleeve_return_corr"] for w in negative) / len(negative)
                if negative
                else None
            ),
        },
        "interpretation_rules": {
            "no_universal_root_cause_threshold": True,
            "purpose": "descriptive evidence synthesis before any new intervention",
            "holdout_excluded": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }

    result["diagnostic_fingerprint"] = _fp(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = analyze(Path(args.source_root))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )

    print("FOURSET_REGIME_SLEEVE_STATUS:", result["status"])
    print("NEGATIVE_PORTFOLIO_WINDOWS:", result["aggregate"]["negative_portfolio_windows"])
    print("JOINT_SLEEVE_WEAKNESS_WINDOWS:", result["aggregate"]["joint_sleeve_weakness_windows"])
    print("JOINT_SLEEVE_WEAKNESS_RATE:", result["aggregate"]["joint_sleeve_weakness_rate"])
    print("TREND_ONLY_WINDOWS:", result["aggregate"]["trend_only_weakness_windows"])
    print("CS_ONLY_WINDOWS:", result["aggregate"]["cross_sectional_only_weakness_windows"])
    print("MEAN_NEGATIVE_WINDOW_DE_RISK:", result["aggregate"]["mean_negative_window_de_risk_fraction"])
    print("MEAN_POSITIVE_WINDOW_DE_RISK:", result["aggregate"]["mean_positive_window_de_risk_fraction"])
    print("MEAN_NEGATIVE_WINDOW_SLEEVE_CORR:", result["aggregate"]["mean_negative_window_sleeve_return_corr"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
