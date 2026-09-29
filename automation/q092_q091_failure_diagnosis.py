"""Q092 deterministic diagnosis of the immutable Q091 performance result.

Diagnostic only. No new market data, performance evaluation, tuning, ranking,
selection, promotion, or live execution is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Iterable

from automation.q069_candidate_bank import CANDIDATES, candidate_targets_at
from data.canonical_snapshot import load_frozen_snapshot
from portfolio.q091_fixed_ensemble import demean_weights, gross_normalize

TRIAL_ID = "T-2026-09-29-092"
PARENT_TRIAL_ID = "T-2026-09-29-091"
RESULT_PATH = "research/evidence/q091_performance_result.json"
MANIFEST_PATH = "research/runs/q091_coverage/T-2026-09-29-091-COVERAGE/snapshot_manifest.json"
RESULT_FP = "0816e49774ff901438e046e162e428884f3f67b305cf26e0ebff2451ce38195d"
SNAPSHOT_FP = "4f89d5fa954139b0b88d916ce307b1b1a93b61b020dc8b1b4b4296d70df2f4e2"
Q069_BANK_SHA = "84e008a6152cbea128e5e5f2ac0dfdde0b0172310fe4c510241c60edfd3ff617"
Q091_PORTFOLIO_SHA = "4f53c46844d56ddc2469fbeaa539dc054e11af777f25b4c318c456b792251de0"
N = 3500
RESEARCH = 2798
HOLDOUT = 700
COST_RATE = 0.0015
SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def fingerprint(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def mean(values: Iterable[float]) -> float:
    data = list(values)
    return statistics.fmean(data) if data else 0.0


def pearson(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n < 2:
        return 0.0
    x, y = a[:n], b[:n]
    ax, ay = mean(x), mean(y)
    vx = sum((v - ax) ** 2 for v in x)
    vy = sum((v - ay) ** 2 for v in y)
    if vx <= 0 or vy <= 0:
        return 0.0
    return sum((xx - ax) * (yy - ay) for xx, yy in zip(x, y)) / math.sqrt(vx * vy)


def stats(values: list[float]) -> dict:
    equity = peak = 1.0
    gain = loss = 0.0
    positive = 0
    max_dd = 0.0
    for value in values:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak if equity > 0 else 1.0)
        if value > 0:
            gain += value
            positive += 1
        elif value < 0:
            loss -= value
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": gain / loss if loss else ("inf" if gain else 0.0),
        "positive_day_ratio": positive / len(values) if values else 0.0,
        "day_count": len(values),
    }


def rolling_stats(values: list[float]) -> list[dict]:
    width = RESEARCH // 5
    result = []
    for i in range(5):
        start = i * width
        end = RESEARCH if i == 4 else (i + 1) * width
        item = stats(values[start:end])
        item.update({"window_index": i + 1, "start_index": start, "end_index_exclusive": end})
        result.append(item)
    return result


def verify_parent(root: Path) -> dict:
    result = json.loads((root / RESULT_PATH).read_text(encoding="utf-8"))
    if result.get("trial_id") != PARENT_TRIAL_ID or result.get("status") != "COMPLETED":
        raise RuntimeError("Q091 result identity/status invalid")
    actual = result.get("report_fingerprint")
    payload = dict(result)
    payload.pop("report_fingerprint", None)
    if actual != RESULT_FP or fingerprint(payload) != RESULT_FP:
        raise RuntimeError("Q091 result fingerprint mismatch")
    if result.get("safety") != SAFETY:
        raise RuntimeError("Q091 safety contract mismatch")
    if result.get("selection_used") is not False or result.get("holdout_used_for_selection") is not False:
        raise RuntimeError("Q091 governance records selection")
    return result


def verify_snapshot(root: Path, parent: dict):
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    if manifest.get("status") != "COVERAGE_PASSED" or manifest.get("snapshot_fingerprint") != SNAPSHOT_FP:
        raise RuntimeError("Q091 snapshot manifest invalid")
    symbols = tuple(manifest["symbols"])
    if list(symbols) != parent["symbols"] or int(manifest["target_common_candles"]) != N:
        raise RuntimeError("Q091 snapshot geometry invalid")
    assets = load_frozen_snapshot(root / MANIFEST_PATH)
    if tuple(assets) != symbols or any(len(assets[s]) != N for s in symbols):
        raise RuntimeError("Q091 frozen snapshot invalid")
    return assets, symbols


def exact_parent_summary(parent_arm: dict, net: list[float]) -> None:
    reconstructed = {
        "research": stats(net[:RESEARCH]),
        "holdout": stats(net[RESEARCH:RESEARCH + HOLDOUT]),
    }
    for split in ("research", "holdout"):
        for key in reconstructed[split]:
            actual = parent_arm["base"][split][key]
            got = reconstructed[split][key]
            if isinstance(actual, str):
                if actual != got:
                    raise RuntimeError(f"Q092 exact reconstruction mismatch: {split}.{key}")
            elif not math.isclose(float(actual), float(got), rel_tol=1e-10, abs_tol=1e-12):
                raise RuntimeError(f"Q092 exact reconstruction mismatch: {split}.{key}")


def drawdown_interval(values: list[float]) -> dict:
    equity = peak = 1.0
    peak_index = -1
    best = 0.0
    start = end = 0
    for i, value in enumerate(values):
        equity *= 1.0 + value
        if equity > peak:
            peak = equity
            peak_index = i
        current = 1.0 - equity / peak if equity > 0 else 1.0
        if current > best:
            best = current
            start = peak_index + 1
            end = i
    return {"start_index": start, "end_index": end, "length": end - start + 1, "max_drawdown_percent": best * 100.0}


def regimes(market: list[float]) -> list[str]:
    labels = []
    vols = [None] * len(market)
    for i in range(len(market)):
        if i >= 21:
            vols[i] = statistics.pstdev(market[i - 21:i])
        if i < 273 or vols[i] is None:
            labels.append("UNDEFINED_EARLY")
            continue
        hist = [v for v in vols[i - 252:i] if v is not None]
        threshold = statistics.median(hist) if hist else 0.0
        trend = math.prod(1.0 + v for v in market[i - 63:i]) - 1.0
        labels.append(("UPTREND" if trend >= 0 else "DOWNTREND") + "_" + ("HIGHVOL" if vols[i] >= threshold else "LOWVOL"))
    return labels


def grouped(values: list[float], labels: list[str]) -> dict:
    buckets: dict[str, list[float]] = {}
    for label, value in zip(labels, values):
        buckets.setdefault(label, []).append(value)
    return {
        label: {
            "day_count": len(v),
            "compound_return": math.prod(1.0 + x for x in v) - 1.0,
            "simple_return_sum": sum(v),
            "mean_daily_return": mean(v),
            "negative_day_fraction": mean([1.0 if x < 0 else 0.0 for x in v]),
        }
        for label, v in buckets.items()
    }


def build_arm(paths: dict, assets, symbols: tuple[str, ...], parent_arm: dict) -> dict:
    weights = paths["weights"]
    gross = paths["gross"]
    turnover = paths["turnover"]
    net = paths["net"]
    parent_sleeves = {name: [] for name in CANDIDATES}
    parent_raw = {name: [] for name in CANDIDATES}

    for i, w in enumerate(weights):
        sleeves = paths["sleeves"][i]
        for name in CANDIDATES:
            if paths["variant"] == "E1_EQUAL_WEIGHT_Q069_5SLEEVE":
                contribution = {s: float(sleeves[name][s]) / 5.0 for s in symbols}
            else:
                residual = demean_weights(sleeves[name], symbols)
                combined = {}
                for s in symbols:
                    combined[s] = sum(
                        float(demean_weights(sleeves[n], symbols)[s]) for n in CANDIDATES
                    ) / len(CANDIDATES)
                normalized = gross_normalize(combined, symbols)
                contribution = {
                    s: (float(residual[s]) / len(CANDIDATES)) /
                    sum(abs(float(x)) for x in combined.values())
                    if sum(abs(float(x)) for x in combined.values()) > 0 else 0.0
                    for s in symbols
                }
                _ = normalized
            sleeve_return = sum(
                float(contribution[s]) * (
                    assets[s][i + 2].open / assets[s][i + 1].open - 1.0
                )
                for s in symbols
            )
            parent_sleeves[name].append(sleeve_return)
            parent_raw[name].append(sleeves[name])

    sleeve_summary = {}
    for name in CANDIDATES:
        values = parent_sleeves[name]
        sleeve_summary[name] = {
            "research_return_contribution_simple": sum(values[:RESEARCH]),
            "holdout_return_contribution_simple": sum(values[RESEARCH:RESEARCH + HOLDOUT]),
            "global_return_contribution_simple": sum(values),
            "research_mean_daily_contribution": mean(values[:RESEARCH]),
            "holdout_mean_daily_contribution": mean(values[RESEARCH:RESEARCH + HOLDOUT]),
        }

    exposure = []
    net_exposure = []
    long_exposure = []
    short_exposure = []
    for w in weights:
        vals = [float(w.get(s, 0.0)) for s in symbols]
        long_exposure.append(sum(max(x, 0.0) for x in vals))
        short_exposure.append(sum(min(x, 0.0) for x in vals))
        exposure.append(sum(abs(x) for x in vals))
        net_exposure.append(sum(vals))

    dd = drawdown_interval(net)
    market = [
        mean([
            assets[s][i + 2].open / assets[s][i + 1].open - 1.0
            for s in symbols
        ])
        for i in range(N - 2)
    ]
    label = regimes(market)
    exact_parent_summary(parent_arm, net)

    return {
        "variant": paths["variant"],
        "aggregate_reconstruction_exact": True,
        "parent_sleeve_contribution": sleeve_summary,
        "exposure": {
            "mean_gross": mean(exposure),
            "max_gross": max(exposure) if exposure else 0.0,
            "mean_net_exposure": mean(net_exposure),
            "mean_long_exposure": mean(long_exposure),
            "mean_short_exposure": mean(short_exposure),
            "max_abs_net_exposure": max(abs(x) for x in net_exposure) if net_exposure else 0.0,
        },
        "cost_turnover": {
            "mean_turnover": mean(turnover),
            "sum_turnover": sum(turnover),
            "base_cost_drag_simple": COST_RATE * sum(turnover),
            "research_turnover_sum": sum(turnover[:RESEARCH]),
            "holdout_turnover_sum": sum(turnover[RESEARCH:RESEARCH + HOLDOUT]),
        },
        "drawdown": {
            **dd,
            "start_timestamp": str(assets[symbols[0]][dd["start_index"] + 2].timestamp),
            "end_timestamp": str(assets[symbols[0]][dd["end_index"] + 2].timestamp),
            "research_window": next((x["window_index"] for x in rolling_stats(net) if x["start_index"] <= dd["start_index"] < x["end_index_exclusive"]), None),
            "negative_day_fraction": mean([1.0 if x < 0 else 0.0 for x in net]),
        },
        "market_relationship": {
            "net_return_market_correlation_all_days": pearson(net, market),
            "net_return_market_correlation_research": pearson(net[:RESEARCH], market[:RESEARCH]),
            "net_return_market_correlation_holdout": pearson(net[RESEARCH:], market[RESEARCH:]),
            "mean_market_return_research": mean(market[:RESEARCH]),
            "mean_market_return_holdout": mean(market[RESEARCH:]),
            "regime_decomposition": grouped(net, label),
        },
        "research_holdout_transition": {
            "research_return": parent_arm["base"]["research"]["period_return"],
            "holdout_return": parent_arm["base"]["holdout"]["period_return"],
            "return_change": parent_arm["base"]["holdout"]["period_return"] - parent_arm["base"]["research"]["period_return"],
            "oos_to_is_ratio": parent_arm["base"]["oos_to_is_return_ratio"],
        },
        "q091_gate_count": parent_arm["gates_passed"],
    }


def reconstruct(root: Path, output: Path, markdown: Path) -> dict:
    parent = verify_parent(root)
    assets, symbols = verify_snapshot(root, parent)
    prereg = json.loads(
        (root / "research/preregistrations/q091_fixed_portfolio_architecture_2026_09_29.json").read_text(encoding="utf-8")
    )
    if prereg.get("governance", {}).get("performance_trial_authorized") is not True:
        raise RuntimeError("Q091 preregistration governance unexpectedly changed")
    paths = {}
    for variant in ("E1_EQUAL_WEIGHT_Q069_5SLEEVE", "E2_CROSS_SECTIONAL_RESIDUALIZED_Q069_5SLEEVE"):
        weights = []
        sleeves = []
        gross = []
        turnover = []
        prev = {s: 0.0 for s in symbols}
        for i in range(N - 2):
            current_sleeves = candidate_targets_at(assets, i, symbols=symbols)
            if variant == "E1_EQUAL_WEIGHT_Q069_5SLEEVE":
                current = {
                    s: sum(float(current_sleeves[n][s]) for n in CANDIDATES) / len(CANDIDATES)
                    for s in symbols
                }
            else:
                residuals = {n: demean_weights(current_sleeves[n], symbols) for n in CANDIDATES}
                combined = {
                    s: sum(float(residuals[n][s]) for n in CANDIDATES) / len(CANDIDATES)
                    for s in symbols
                }
                current = gross_normalize(combined, symbols)
            weights.append(current)
            sleeves.append(current_sleeves)
            gross.append(sum(abs(float(current[s])) for s in symbols))
            turnover.append(sum(abs(float(current[s]) - prev[s]) for s in symbols))
            prev = {s: float(current[s]) for s in symbols}
        net = []
        for i, w in enumerate(weights):
            g = sum(
                float(w[s]) * (assets[s][i + 2].open / assets[s][i + 1].open - 1.0)
                for s in symbols
            )
            net.append(g - COST_RATE * turnover[i])
        paths[variant] = {
            "variant": variant,
            "weights": weights,
            "sleeves": sleeves,
            "gross": gross,
            "turnover": turnover,
            "net": net,
        }

    arms = {}
    for variant, path in paths.items():
        arms[variant] = build_arm(path, assets, symbols, parent["arms"][variant])

    result = {
        "schema_version": "1.0",
        "trial_id": TRIAL_ID,
        "status": "COMPLETED_DIAGNOSTIC_ONLY",
        "research_family": "q092_q091_failure_mechanism_diagnosis",
        "parent_trial_id": PARENT_TRIAL_ID,
        "source": {
            "parent_report_fingerprint": RESULT_FP,
            "snapshot_fingerprint": SNAPSHOT_FP,
            "candidate_bank_sha256": Q069_BANK_SHA,
            "portfolio_architecture_sha256": Q091_PORTFOLIO_SHA,
            "symbols": list(symbols),
            "requested_candles": 5000,
            "target_common_candles": N,
            "research_periods": RESEARCH,
            "holdout_periods": HOLDOUT,
        },
        "reconstruction": {
            "aggregate_reconstruction_exact": True,
            "no_new_market_data": True,
            "no_new_performance_trial": True,
            "parent_result_immutable": True,
        },
        "diagnostic_scope": {
            "parent_sleeve_contribution": True,
            "exposure_path": True,
            "common_mode_market_relationship": True,
            "long_short_balance": True,
            "turnover_and_cost_drag": True,
            "drawdown_interval": True,
            "market_regime_decomposition": True,
            "research_holdout_transition": True,
        },
        "arms": arms,
        "governance": {
            "diagnostic_evaluation": True,
            "new_performance_evaluation": False,
            "selection": False,
            "holdout_used_for_selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "asset_search": False,
            "horizon_search": False,
            "variant_search": False,
            "family_ranking": False,
            "promotion_decision": False,
            "automatic_promotion": False,
        },
        "next_questions": [
            "Determine whether Q091 failure is dominated by a common market component or by sleeve-specific signal decay.",
            "Determine whether concentration and long/short imbalance explain drawdown concentration without changing the fixed rules.",
            "Determine whether turnover/cost drag explains a material fraction of the research-to-holdout collapse.",
            "Only after these diagnoses, design fresh disjoint fixed-rule validation candidates."
        ],
        "safety": SAFETY,
    }
    result["diagnostic_fingerprint"] = fingerprint(result)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# Q092 — Q091 Failure-Mechanism Diagnosis",
        "",
        "Status: COMPLETED_DIAGNOSTIC_ONLY",
        "",
        "Immutable Q091 reconstruction only. No new market data, performance trial, tuning, selection, ranking or promotion.",
        "",
        "| Variant | Gates | Research→Holdout return | Mean gross | Mean net exposure | Mean turnover | Base cost drag | Market corr. (all) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant, arm in arms.items():
        lines.append(
            f"| {variant} | {arm['q091_gate_count']}/13 | "
            f"{100*arm['research_holdout_transition']['research_return']:.2f}% → "
            f"{100*arm['research_holdout_transition']['holdout_return']:.2f}% | "
            f"{arm['exposure']['mean_gross']:.4f} | "
            f"{arm['exposure']['mean_net_exposure']:.4f} | "
            f"{arm['cost_turnover']['mean_turnover']:.4f} | "
            f"{arm['cost_turnover']['base_cost_drag_simple']:.4f} | "
            f"{arm['market_relationship']['net_return_market_correlation_all_days']:.4f} |"
        )
    lines += [
        "",
        "## Governance",
        "",
        "- Exact aggregate reconstruction: true",
        "- New performance evaluation: false",
        "- Holdout selection: false",
        "- Promotion: false",
        f"- Parent result fingerprint: {RESULT_FP}",
        f"- Snapshot fingerprint: {SNAPSHOT_FP}",
        "",
    ]
    for variant, arm in arms.items():
        lines += [
            f"## {variant}",
            "",
            f"- Worst drawdown interval: {arm['drawdown']['start_timestamp']} → {arm['drawdown']['end_timestamp']}.",
            f"- Mean gross exposure: {arm['exposure']['mean_gross']:.4f}; mean net exposure: {arm['exposure']['mean_net_exposure']:.4f}.",
            f"- Turnover sum: {arm['cost_turnover']['sum_turnover']:.2f}; base cost drag (simple): {arm['cost_turnover']['base_cost_drag_simple']:.4f}.",
            f"- Market correlation of daily net return: {arm['market_relationship']['net_return_market_correlation_all_days']:.4f}.",
            "",
            "Parent-sleeve simple return contributions:",
        ]
        for sleeve, values in arm["parent_sleeve_contribution"].items():
            lines.append(
                f"- {sleeve}: research {values['research_return_contribution_simple']:.6f}, "
                f"holdout {values['holdout_return_contribution_simple']:.6f}."
            )
        lines.append("")
    markdown.parent.mkdir(parents=True, exist_ok=True)
    markdown.write_text("\n".join(lines), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    result = reconstruct(args.repo_root, args.output, args.markdown)
    print("Q092_DIAGNOSIS_OK")
    print("Q092_DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
