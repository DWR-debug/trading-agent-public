"""Sleeve-specific timing diagnosis for the fixed 63-session risk layer.

Measures whether portfolio de-risking is concentrated around the worst 5%
days of the Trend or Cross-Sectional sleeve separately.

No tuning, selection, new data, gate changes, or production mutation.
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
    },
    {
        "name": "third_validation",
        "artifact_id": 10745697729,
        "run_id": 35851876264,
        "root": "research/third_independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_third_trend",
        "cs_universe": "validation_2026_09_23_third_cs",
    },
)

def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)

def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode()).hexdigest()

def _load_rows(artifact_root: Path, case: dict[str, Any]) -> tuple[dict[str, Any], tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    root = artifact_root / case["root"]
    report = json.loads((root / "report.json").read_text(encoding="utf-8"))
    stored = report["report_fingerprint"]
    payload = dict(report)
    payload.pop("report_fingerprint", None)
    if _fp(payload) != stored or report["status"] != "COMPLETED":
        raise ValueError(f'{case["name"]}: invalid report fingerprint/status')
    archive = json.loads((root / "adjusted_close_archive.json").read_text(encoding="utf-8"))
    archive_fp = archive["archive_fingerprint"]
    archive_payload = dict(archive)
    archive_payload.pop("archive_fingerprint", None)
    if _fp(archive_payload) != archive_fp:
        raise ValueError(f'{case["name"]}: invalid archive fingerprint')
    if archive_fp != report["source"]["adjusted_close_archive_fingerprint"]:
        raise ValueError(f'{case["name"]}: archive/report mismatch')

    trend_manifest = base._manifest(root / "data_trend_manifest.json", case["trend_universe"])
    cs_manifest = base._manifest(root / "data_cs_manifest.json", case["cs_universe"])
    data_dir = artifact_root / "data/market_data"
    trend = base._assets(data_dir, trend_manifest)
    cs = base._assets(data_dir, cs_manifest)
    if set(trend) & set(cs):
        raise ValueError(f'{case["name"]}: overlapping universes')

    adjusted = {
        symbol: {datetime.fromisoformat(ts): value for ts, value in values}
        for symbol, values in archive["datasets"].items()
    }
    trend_weights = base._build_weight_path(trend, base.TREND_STRATEGY)
    cs_weights = base._cs_weights(cs)
    trend_rows = {
        row["timestamp"]: row
        for row in base._return_rows(
            trend, trend_weights,
            {symbol: adjusted[symbol] for symbol in trend},
        )
    }
    cs_rows = {
        row["timestamp"]: row
        for row in base._return_rows(
            cs, cs_weights,
            {symbol: adjusted[symbol] for symbol in cs},
        )
    }
    common = sorted(set(trend_rows) & set(cs_rows))
    if len(common) != base.RESEARCH_COUNT + base.HOLDOUT_COUNT:
        raise ValueError(f'{case["name"]}: unexpected common return count')

    portfolio_rows = tuple(
        {
            "timestamp": ts,
            "gross_open": 0.5 * trend_rows[ts]["gross_open"] + 0.5 * cs_rows[ts]["gross_open"],
            "gross_close": 0.5 * trend_rows[ts]["gross_close"] + 0.5 * cs_rows[ts]["gross_close"],
            "gross_adjusted_close": 0.5 * trend_rows[ts]["gross_adjusted_close"] + 0.5 * cs_rows[ts]["gross_adjusted_close"],
            "turnover": 0.5 * trend_rows[ts]["turnover"] + 0.5 * cs_rows[ts]["turnover"],
        }
        for ts in common
    )
    return case, tuple(trend_rows[ts] for ts in common), tuple(cs_rows[ts] for ts in common), portfolio_rows

def _bucket_timing(scale_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]], start: int, end: int) -> dict[str, Any]:
    scaled = scale_rows[start:end]
    target = target_rows[start:end]
    if not scaled:
        return {"day_count": 0}
    worst_count = max(1, math.ceil(len(target) * 0.05))
    worst_idx = sorted(range(len(target)), key=lambda i: target[i]["gross_open"])[:worst_count]
    all_de_risk = sum(x["scale"] < 1.0 for x in scaled) / len(scaled)
    worst_de_risk = sum(scaled[i]["scale"] < 1.0 for i in worst_idx) / len(worst_idx)
    target_mean = sum(x["gross_open"] for x in target) / len(target)
    worst_mean = sum(target[i]["gross_open"] for i in worst_idx) / len(worst_idx)
    return {
        "day_count": len(target),
        "worst_5pct_count": worst_count,
        "all_day_de_risk_fraction": all_de_risk,
        "worst_5pct_de_risk_fraction": worst_de_risk,
        "concentration_ratio_worst5_vs_all": worst_de_risk / all_de_risk if all_de_risk else 0.0,
        "all_day_mean_return": target_mean,
        "worst_5pct_mean_return": worst_mean,
        "de_risk_on_worst5_excess_fraction": worst_de_risk - all_de_risk,
    }

def _corr(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or len(a) < 2:
        return 0.0
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((x - mb) ** 2 for x in b)
    if va <= 0.0 or vb <= 0.0:
        return 0.0
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return cov / math.sqrt(va * vb)

def analyze_case(trend_rows: tuple[dict[str, Any], ...], cs_rows: tuple[dict[str, Any], ...], portfolio_rows: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    simulated = base._simulate(portfolio_rows, 1.0, True, False)
    scale = simulated
    n = len(scale)
    result = {}
    for label, start, end in (("research", 0, base.RESEARCH_COUNT), ("holdout", base.RESEARCH_COUNT, n)):
        scale_seg = scale[start:end]
        trend_seg = list(trend_rows[start:end])
        cs_seg = list(cs_rows[start:end])
        port_seg = list(portfolio_rows[start:end])
        result[label] = {
            "trend": _bucket_timing(scale_seg, trend_seg, 0, len(scale_seg)),
            "cross_sectional": _bucket_timing(scale_seg, cs_seg, 0, len(scale_seg)),
            "de_risk_scale_return_correlation_trend": _corr(
                [x["scale"] for x in scale_seg], [x["gross_open"] for x in trend_seg]
            ),
            "de_risk_scale_return_correlation_cross_sectional": _corr(
                [x["scale"] for x in scale_seg], [x["gross_open"] for x in cs_seg]
            ),
            "portfolio_worst5_concentration": _bucket_timing(scale_seg, port_seg, 0, len(scale_seg)),
        }
    return result

def analyze(artifact_root: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-Only safety contract violated.")
    cases = {}
    for case in CASES:
        _, trend_rows, cs_rows, portfolio_rows = _load_rows(artifact_root, case)
        cases[case["name"]] = {
            "source": {"validation_run_id": case["run_id"], "artifact_id": case["artifact_id"]},
            "timing": analyze_case(trend_rows, cs_rows, portfolio_rows),
        }
    result = {
        "schema_version": 1,
        "diagnostic_type": "risk_layer_sleeve_timing_2026_09_23",
        "status": "COMPLETED",
        "question": "Is fixed 63-session portfolio de-risking more concentrated around Trend or Cross-Sectional sleeve stress?",
        "methodology": {
            "vol_window_sessions": 63,
            "target_annualized_volatility": base.TARGET_VOL,
            "worst_day_bucket_percent": 5,
            "fixed_portfolio_risk_layer": True,
            "same_data_and_split": True,
            "no_parameter_search": True,
            "no_selection": True,
            "no_gate_changes": True,
            "no_new_data_downloads": True,
            "descriptive_not_causal": True,
        },
        "cases": cases,
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False},
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
    print("RISK_LAYER_SLEEVE_TIMING_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    for name, case in result["cases"].items():
        for segment, values in case["timing"].items():
            if isinstance(values, dict):
                for sleeve in ("trend", "cross_sectional"):
                    v=values.get(sleeve)
                    if v:
                        print(f"{name.upper()}_{segment.upper()}_{sleeve.upper()}_CONCENTRATION:", v["concentration_ratio_worst5_vs_all"])
                print(f"{name.upper()}_{segment.upper()}_TREND_SCALE_CORR:", values["de_risk_scale_return_correlation_trend"])
                print(f"{name.upper()}_{segment.upper()}_CS_SCALE_CORR:", values["de_risk_scale_return_correlation_cross_sectional"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
