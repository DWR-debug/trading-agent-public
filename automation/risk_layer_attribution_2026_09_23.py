"""Descriptive attribution of the existing 63-session risk layer.

Compares the fixed candidate with and without the existing 10% volatility
budget on two already archived, independent validation artifacts.

No parameter search, selection, gate changes, new data downloads, or
production mutation.
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


CASES = (
    {
        "name": "second_validation",
        "artifact_id": 10740188093,
        "run_id": 35839443616,
        "root": "research/independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_trend",
        "cs_universe": "validation_2026_09_23_cs",
        "archive_fingerprint": "eed3ec6105dc7bc8616ab989ce6f086107b249f7fa087f6e851709af6e47354",
    },
    {
        "name": "third_validation",
        "artifact_id": 10745697729,
        "run_id": 35851876264,
        "root": "research/third_independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_third_trend",
        "cs_universe": "validation_2026_09_23_third_cs",
        "archive_fingerprint": "b6a408b41abb218d285e06af4b91f66da3ed4ce431aef72907ca5873ffa2c731",
    },
)


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode()).hexdigest()


def _pf(value: float | str) -> float:
    return float("inf") if value == "inf" else float(value)


def _stats(rows: list[dict[str, Any]], start: int, end: int) -> dict[str, Any]:
    segment = rows[start:end]
    equity = peak = 1.0
    max_dd = 0.0
    gp = gl = 0.0
    total_cost_return = 0.0
    de_risk_count = 0
    scales: list[float] = []
    for row in segment:
        value = row["net_return"]
        gross = row["gross_return"]
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak if equity > 0 else 1.0)
        gp += max(value, 0.0)
        gl += max(-value, 0.0)
        total_cost_return += gross - value
        scales.append(row["scale"])
        de_risk_count += row["scale"] < 1.0
    if not segment:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "day_count": 0,
            "median_scale": 1.0,
            "minimum_scale": 1.0,
            "de_risk_fraction": 0.0,
            "aggregate_cost_drag_percentage_points": 0.0,
        }
    ordered = sorted(scales)
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": gp / gl if gl > 0 else ("inf" if gp > 0 else 0.0),
        "day_count": len(segment),
        "median_scale": ordered[len(ordered) // 2],
        "minimum_scale": min(scales),
        "de_risk_fraction": de_risk_count / len(segment),
        "aggregate_cost_drag_percentage_points": total_cost_return * 100.0,
    }


def _rolling(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    width = base.RESEARCH_COUNT // 5
    windows = []
    start = 0
    for index in range(5):
        end = base.RESEARCH_COUNT if index == 4 else start + width
        windows.append({"window_index": index + 1, **_stats(rows, start, end)})
        start = end
    return windows


def _load_rows(artifact_root: Path, case: dict[str, Any]) -> tuple[tuple[dict[str, Any], ...], dict[str, Any]]:
    root = artifact_root / case["root"]
    report = json.loads((root / "report.json").read_text(encoding="utf-8"))
    stored = report.get("report_fingerprint")
    if not isinstance(stored, str) or not stored:
        raise ValueError(f'{case["name"]}: report fingerprint missing')
    payload = dict(report)
    payload.pop("report_fingerprint", None)
    if _fp(payload) != stored:
        raise ValueError(f'{case["name"]}: report fingerprint mismatch')
    if report["status"] != "COMPLETED":
        raise ValueError(f'{case["name"]}: source report not completed')
    if report["source"]["fully_disjoint_from_prior_universes"] is not True:
        raise ValueError(f'{case["name"]}: source is not fully disjoint')

    archive = json.loads((root / "adjusted_close_archive.json").read_text(encoding="utf-8"))
    archive_fp = archive.get("archive_fingerprint")
    archive_payload = dict(archive)
    archive_payload.pop("archive_fingerprint", None)
    if not archive_fp or _fp(archive_payload) != archive_fp:
        raise ValueError(f'{case["name"]}: archive fingerprint mismatch')
    if archive_fp != report["source"]["adjusted_close_archive_fingerprint"]:
        raise ValueError(f'{case["name"]}: archive does not match report')

    trend_manifest = base._manifest(root / "data_trend_manifest.json", case["trend_universe"])
    cs_manifest = base._manifest(root / "data_cs_manifest.json", case["cs_universe"])
    trend = base._assets(artifact_root / "data/market_data", trend_manifest)
    cs = base._assets(artifact_root / "data/market_data", cs_manifest)
    if set(trend) & set(cs):
        raise ValueError(f'{case["name"]}: validation universes overlap')

    trend_weights = base._build_weight_path(trend, base.TREND_STRATEGY)
    cs_weights = base._cs_weights(cs)
    adjusted = {
        symbol: {datetime.fromisoformat(ts): value for ts, value in values}
        for symbol, values in archive["datasets"].items()
    }
    rows = base._align(
        trend,
        trend_weights,
        {symbol: adjusted[symbol] for symbol in trend},
        cs,
        cs_weights,
        {symbol: adjusted[symbol] for symbol in cs},
    )
    if len(rows) != base.RESEARCH_COUNT + base.HOLDOUT_COUNT:
        raise ValueError(f'{case["name"]}: unexpected return count')

    return rows, {
        "report_fingerprint": stored,
        "trend_manifest_fingerprint": trend_manifest["manifest_fingerprint"],
        "cs_manifest_fingerprint": cs_manifest["manifest_fingerprint"],
    }


def _delta(unscaled: list[dict[str, Any]], budget: list[dict[str, Any]], start: int, end: int) -> dict[str, Any]:
    a = _stats(unscaled, start, end)
    b = _stats(budget, start, end)
    return {
        "return_delta_percentage_points": (b["period_return"] - a["period_return"]) * 100.0,
        "drawdown_delta_percentage_points": b["max_drawdown_percent"] - a["max_drawdown_percent"],
        "profit_factor_delta": _pf(b["profit_factor"]) - _pf(a["profit_factor"]),
        "budget_de_risk_fraction": b["de_risk_fraction"],
        "budget_median_scale": b["median_scale"],
        "budget_minimum_scale": b["minimum_scale"],
        "budget_aggregate_cost_drag_percentage_points": b["aggregate_cost_drag_percentage_points"],
    }


def analyze(artifact_root: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-Only safety contract violated.")

    cases_out = {}
    for case in CASES:
        rows, source = _load_rows(artifact_root, case)
        unscaled = base._simulate(rows, 1.0, False, False)
        budget = base._simulate(rows, 1.0, True, False)
        cases_out[case["name"]] = {
            "source": {
                "validation_run_id": case["run_id"],
                "artifact_id": case["artifact_id"],
                **source,
            },
            "unscaled": {
                "research": _stats(unscaled, 0, base.RESEARCH_COUNT),
                "holdout": _stats(unscaled, base.RESEARCH_COUNT, len(unscaled)),
                "rolling_windows": _rolling(unscaled),
            },
            "vol_budget_10pct_63": {
                "research": _stats(budget, 0, base.RESEARCH_COUNT),
                "holdout": _stats(budget, base.RESEARCH_COUNT, len(budget)),
                "rolling_windows": _rolling(budget),
            },
            "budget_minus_unscaled": {
                "research": _delta(unscaled, budget, 0, base.RESEARCH_COUNT),
                "holdout": _delta(unscaled, budget, base.RESEARCH_COUNT, len(budget)),
            },
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "risk_layer_attribution_2026_09_23",
        "status": "COMPLETED",
        "scope": {
            "question": "How much of the observed risk/return profile is attributable to the existing 63-session 10% vol-budget layer versus the unscaled reference and its cost drag?",
            "new_data_downloads": False,
            "parameter_search": False,
            "selection": False,
            "gate_changes": False,
            "production_mutation": False,
        },
        "methodology": {
            "candidate_fixed": True,
            "vol_budget_window_sessions": base.VOL_WINDOW,
            "target_annualized_volatility": base.TARGET_VOL,
            "same_data": True,
            "same_signals": True,
            "same_sleeve_weights": True,
            "same_costs": True,
            "same_execution_model": True,
            "research_holdout_split_fixed": True,
            "descriptive_not_causal": True,
        },
        "cases": cases_out,
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
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = analyze(Path(args.artifact_root))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print("RISK_LAYER_ATTRIBUTION_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    for name, case in result["cases"].items():
        for segment in ("research", "holdout"):
            d = case["budget_minus_unscaled"][segment]
            print(f"{name.upper()}_{segment.upper()}_RETURN_DELTA_PP:", d["return_delta_percentage_points"])
            print(f"{name.upper()}_{segment.upper()}_DD_DELTA_PP:", d["drawdown_delta_percentage_points"])
            print(f"{name.upper()}_{segment.upper()}_PF_DELTA:", d["profit_factor_delta"])
            print(f"{name.upper()}_{segment.upper()}_COST_DRAG_PP:", d["budget_aggregate_cost_drag_percentage_points"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
