from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import statistics
from pathlib import Path

ARMS = ("CONTROL", "RISK-A", "RISK-B", "RISK-C", "RISK-D")
SYMBOLS = ("BSV", "FAN", "JNK", "UDN", "VCLT", "VGIT", "SCHR")
SOURCE_SHA = "23e09d478ef4d7c9f866b8fc123b1842c9953ad8"
SOURCE_REPORT_FP = "56feed52b6c8321e3b4cfcf7914b87d2d54ad4cf7d1cf66b095a62db0453943f"

def fp(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()

def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("q035_exact_runner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load exact T056 runner")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def load_report(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    assert d["trial_id"] == "T-2026-09-27-056"
    assert d["code_version"] == SOURCE_SHA
    assert d["report_fingerprint"] == SOURCE_REPORT_FP
    assert d["selection_used"] is False
    assert d["holdout_used_for_selection"] is False
    return d

def find_manifest(artifact_root: Path) -> Path:
    paths = sorted(artifact_root.rglob("coverage_preflight_*.json"))
    if not paths:
        raise FileNotFoundError("coverage manifest not found")
    return paths[-1]

def mean(xs):
    return statistics.fmean(xs) if xs else 0.0

def gross(row):
    return sum(abs(float(v)) for v in row.values())

def risk_a_scales(runner, assets):
    trend, cs, control = runner._baseline(assets)
    tr = runner._sleeve_rows(assets, trend)
    cr = runner._sleeve_rows(assets, cs)
    tg = [x["gross_return"] for x in tr]
    cg = [x["gross_return"] for x in cr]
    return [{"trend": runner.sleeve_volatility_scale(tg[:i]), "cs": runner.sleeve_volatility_scale(cg[:i])} for i in range(len(control))]

def risk_b_scales(runner, assets):
    _, _, control = runner._baseline(assets)
    rows = runner._rows_for_weights(assets, control)
    values = [x["gross_return"] for x in rows]
    return [runner.drawdown_throttle_scale(values[:i]) for i in range(len(control))]

def risk_c_scales(runner, assets):
    _, _, control = runner._baseline(assets)
    cr = {s: [b[i].close / b[i-1].close - 1.0 for i in range(1, len(b))] for s, b in assets.items()}
    return [runner.common_mode_exposure_scale({s: cr[s][:i] for s in SYMBOLS}, control[i], window=63, trigger=0.60, triggered_scale=0.50) for i in range(len(control))]

def risk_d_activity(runner, assets):
    trend, _, _ = runner._baseline(assets)
    lifecycle = runner._atr20_weight_path(assets, trend)
    stop_asset_days = 0
    starts = 0
    reentries = 0
    prev = False
    by_symbol = {s: 0 for s in SYMBOLS}
    for i in range(len(trend)):
        active_stop = False
        for s in SYMBOLS:
            if float(trend[i].get(s, 0.0)) > 0 and float(lifecycle[i].get(s, 0.0)) == 0:
                stop_asset_days += 1
                by_symbol[s] += 1
                active_stop = True
        starts += int(active_stop and not prev)
        reentries += int(prev and not active_stop)
        prev = active_stop
    return {"stop_asset_days": stop_asset_days, "stop_activity_starts": starts, "reentry_activity_starts": reentries, "stop_asset_days_by_symbol": by_symbol}

def run(report_path: Path, exact_runner_path: Path, output: Path) -> dict:
    report = load_report(report_path)
    runner = load_module(exact_runner_path)
    artifact_root = report_path.parents[2]
    manifest = find_manifest(artifact_root)
    assets = runner._load_assets(manifest)
    weights = runner._arm_weights(assets)
    baseline = weights["CONTROL"]

    exposure = {}
    for arm in ARMS:
        vals = [gross(row) for row in weights[arm]]
        ratios = [gross(weights[arm][i]) / gross(baseline[i]) if gross(baseline[i]) > 0 else 1.0 for i in range(len(baseline))]
        exposure[arm] = {
            "mean_gross_exposure": mean(vals),
            "min_gross_exposure": min(vals),
            "max_gross_exposure": max(vals),
            "days_below_1x": sum(v < 0.999999999 for v in vals),
            "share_days_below_1x": sum(v < 0.999999999 for v in vals) / len(vals),
            "share_days_below_0_5x": sum(v < 0.499999999 for v in vals) / len(vals),
            "mean_scale_vs_control": mean(ratios),
        }

    ra = risk_a_scales(runner, assets)
    rb = risk_b_scales(runner, assets)
    rc = risk_c_scales(runner, assets)
    exposure["RISK-A"].update({
        "trend_scale_mean": mean([x["trend"] for x in ra]),
        "trend_scale_below_1x_share": sum(x["trend"] < 0.999999999 for x in ra) / len(ra),
        "cs_scale_mean": mean([x["cs"] for x in ra]),
        "cs_scale_below_1x_share": sum(x["cs"] < 0.999999999 for x in ra) / len(ra),
    })
    exposure["RISK-B"].update({
        "state_1x_share": sum(x == 1.0 for x in rb) / len(rb),
        "state_0_5x_share": sum(x == 0.5 for x in rb) / len(rb),
        "state_0_25x_share": sum(x == 0.25 for x in rb) / len(rb),
    })
    exposure["RISK-C"].update({
        "trigger_0_5x_share": sum(x == 0.5 for x in rc) / len(rc),
        "full_1x_share": sum(x == 1.0 for x in rc) / len(rc),
    })
    exposure["RISK-D"].update(risk_d_activity(runner, assets))

    control = report["arms"]["CONTROL"]["base"]
    tradeoffs = {}
    for arm in ("RISK-A", "RISK-B", "RISK-C", "RISK-D"):
        a = report["arms"][arm]["base"]
        tradeoffs[arm] = {
            "research_return_delta_vs_control": a["research"]["period_return"] - control["research"]["period_return"],
            "research_drawdown_delta_pp_vs_control": a["research"]["max_drawdown_percent"] - control["research"]["max_drawdown_percent"],
            "research_pf_delta_vs_control": float(a["research"]["profit_factor"]) - float(control["research"]["profit_factor"]),
            "holdout_return_delta_vs_control": a["holdout"]["period_return"] - control["holdout"]["period_return"],
            "holdout_drawdown_delta_pp_vs_control": a["holdout"]["max_drawdown_percent"] - control["holdout"]["max_drawdown_percent"],
            "holdout_pf_delta_vs_control": float(a["holdout"]["profit_factor"]) - float(control["holdout"]["profit_factor"]),
            "rolling_profit_factor_delta_vs_control": a["rolling_profit_factor"] - control["rolling_profit_factor"],
            "rolling_average_drawdown_delta_pp_vs_control": a["rolling_average_drawdown_percent"] - control["rolling_average_drawdown_percent"],
            "oos_to_is_ratio_delta_vs_control": a["oos_to_is_return_ratio"] - control["oos_to_is_return_ratio"],
            "turnover_mean": report["arms"][arm]["turnover"]["mean"],
            "turnover_sum": report["arms"][arm]["turnover"]["sum"],
        }

    result = {
        "schema_version": "1.0",
        "trial_id": "T-2026-09-27-057",
        "status": "DIAGNOSTIC_COMPLETED",
        "source_trial_id": "T-2026-09-27-056",
        "source_workflow_run_id": 36342102919,
        "source_head_sha": SOURCE_SHA,
        "source_report_fingerprint": SOURCE_REPORT_FP,
        "source_snapshot_fingerprint": report["snapshot_fingerprint"],
        "source_coverage_fingerprint": report["coverage_fingerprint"],
        "arm_exposure_and_activation": exposure,
        "tradeoffs": tradeoffs,
        "rolling_phase_diagnostics": {a: report["arms"][a]["base"]["rolling_windows"] for a in ARMS},
        "cost_stress": {a: {
            "base_holdout_return": report["arms"][a]["base"]["holdout"]["period_return"],
            "stress_1_5x_holdout_return": report["arms"][a]["stress_1_5x_cost"]["holdout"]["period_return"],
            "stress_2x_holdout_return": report["arms"][a]["stress_2x_cost"]["holdout"]["period_return"],
            "total_return_sensitivity_holdout": report["arms"][a]["total_return_sensitivity"]["holdout"]["period_return"],
        } for a in ARMS},
        "report_arm_summary": {a: {"gates_passed": sum(bool(x) for x in report["arms"][a]["gates"].values()), "gates_total": len(report["arms"][a]["gates"]), "all_gates_passed": report["arms"][a]["all_gates_passed"]} for a in ARMS},
        "governance": {"performance_evaluation": False, "oos_evaluation": False, "holdout_evaluation": False, "selection_used": False, "holdout_used_for_selection": False, "parameter_search": False, "family_ranking": False, "automatic_promotion": False},
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    result["diagnostic_fingerprint"] = fp(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\\n", encoding="utf-8")
    print("Q036_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    return result

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--report", required=True)
    p.add_argument("--exact-runner", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    run(Path(a.report), Path(a.exact_runner), Path(a.output))
