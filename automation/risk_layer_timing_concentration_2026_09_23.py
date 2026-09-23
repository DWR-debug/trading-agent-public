"""Descriptive timing concentration of the fixed 63-session risk layer.

Question: does the existing de-risking layer activate disproportionately around
the portfolio's worst days, and how persistent are its de-risking runs?

No tuning, selection, new data, gate changes, or production mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
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

def _load_rows(artifact_root: Path, case: dict[str, Any]) -> tuple[dict[str, Any], ...]:
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
    trend = base._assets(artifact_root / "data/market_data", trend_manifest)
    cs = base._assets(artifact_root / "data/market_data", cs_manifest)
    if set(trend) & set(cs):
        raise ValueError(f'{case["name"]}: overlapping universes')
    adjusted = {
        symbol: {datetime.fromisoformat(ts): value for ts, value in values}
        for symbol, values in archive["datasets"].items()
    }
    weights_trend = base._build_weight_path(trend, base.TREND_STRATEGY)
    weights_cs = base._cs_weights(cs)
    return base._align(
        trend, weights_trend, {s: adjusted[s] for s in trend},
        cs, weights_cs, {s: adjusted[s] for s in cs},
    )

def _stats(rows: list[dict[str, Any]], start: int, end: int) -> dict[str, Any]:
    seg = rows[start:end]
    if not seg:
        return {"day_count": 0, "de_risk_fraction": 0.0, "mean_scale": 1.0, "median_scale": 1.0}
    scales = [r["scale"] for r in seg]
    ordered = sorted(scales)
    return {
        "day_count": len(seg),
        "de_risk_fraction": sum(x < 1.0 for x in scales) / len(scales),
        "mean_scale": sum(scales) / len(scales),
        "median_scale": ordered[len(ordered) // 2],
        "minimum_scale": min(scales),
    }

def _timing(rows: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    simulated = base._simulate(rows, 1.0, True, False)
    n = len(simulated)
    research_end = base.RESEARCH_COUNT
    out = {}
    for label, start, end in (
        ("research", 0, research_end),
        ("holdout", research_end, n),
    ):
        seg = simulated[start:end]
        ordered = sorted(seg, key=lambda r: r["net_return"])
        worst_count = max(1, (len(seg) * 5 + 99) // 100)
        worst = ordered[:worst_count]
        scale_stats = _stats(seg, 0, len(seg))
        worst_stats = _stats(worst, 0, len(worst))

        runs = []
        current = 0
        activation = 0
        recovery = 0
        for row in seg:
            if row["scale"] < 1.0:
                if current == 0:
                    activation += 1
                current += 1
            elif current:
                runs.append(current)
                recovery += 1
                current = 0
        if current:
            runs.append(current)
        worst_indices = sorted(
            seg.index(row) for row in worst
        )
        prior_day_overlap = 0
        for idx in worst_indices:
            if idx > 0 and seg[idx - 1]["scale"] < 1.0:
                prior_day_overlap += 1

        out[label] = {
            "all_days": scale_stats,
            "worst_5pct_days": {
                **worst_stats,
                "net_return_threshold_rank": worst_count,
                "de_risk_share_of_worst_5pct": worst_stats["de_risk_fraction"],
            },
            "concentration_ratio_worst5_vs_all": (
                worst_stats["de_risk_fraction"] / scale_stats["de_risk_fraction"]
                if scale_stats["de_risk_fraction"] > 0
                else 0.0
            ),
            "de_risk_run_count": len(runs),
            "de_risk_activation_count": activation,
            "de_risk_recovery_count": recovery,
            "mean_de_risk_run_length": sum(runs) / len(runs) if runs else 0.0,
            "max_de_risk_run_length": max(runs) if runs else 0,
            "worst_5pct_days_with_prior_de_risk_fraction": (
                prior_day_overlap / len(worst_indices) if worst_indices else 0.0
            ),
        }
    return out

def analyze(artifact_root: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-Only safety contract violated.")
    cases = {}
    for case in CASES:
        rows = _load_rows(artifact_root, case)
        cases[case["name"]] = {
            "source": {"validation_run_id": case["run_id"], "artifact_id": case["artifact_id"]},
            "timing": _timing(rows),
        }
    result = {
        "schema_version": 1,
        "diagnostic_type": "risk_layer_timing_concentration_2026_09_23",
        "status": "COMPLETED",
        "question": "Is fixed 63-session de-risking temporally concentrated around the worst portfolio days?",
        "methodology": {
            "vol_window_sessions": 63,
            "target_annualized_volatility": base.TARGET_VOL,
            "worst_day_bucket_percent": 5,
            "same_fixed_candidate": True,
            "same_data_and_split": True,
            "no_parameter_search": True,
            "no_selection": True,
            "no_gate_changes": True,
            "no_new_data_downloads": True,
            "descriptive_not_causal": True,
        },
        "cases": cases,
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
    print("RISK_LAYER_TIMING_CONCENTRATION_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    for name, case in result["cases"].items():
        for segment, values in case["timing"].items():
            if isinstance(values, dict) and "concentration_ratio_worst5_vs_all" in values:
                print(f"{name.upper()}_{segment.upper()}_CONCENTRATION_RATIO:", values["concentration_ratio_worst5_vs_all"])
                print(f"{name.upper()}_{segment.upper()}_DE_RISK_ALL:", values["all_days"]["de_risk_fraction"])
                print(f"{name.upper()}_{segment.upper()}_DE_RISK_WORST5:", values["worst_5pct_days"]["de_risk_fraction"])
                print(f"{name.upper()}_{segment.upper()}_PRIOR_DE_RISK_WORST5:", values["worst_5pct_days_with_prior_de_risk_fraction"])
                print(f"{name.upper()}_{segment.upper()}_MEAN_RUN:", values["mean_de_risk_run_length"])
                print(f"{name.upper()}_{segment.upper()}_MAX_RUN:", values["max_de_risk_run_length"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
