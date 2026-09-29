"""Q091 fixed portfolio-architecture performance evaluation.

The runner is deliberately network-free. It consumes only:
* the persisted Q091 OHLCV common-calendar snapshot,
* the persisted Q091 adjusted-close input bundle, and
* the frozen Q091 rules/preregistration.

No search, ranking, tuning, selection, promotion, or live execution occurs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from automation.q069_candidate_bank import CANDIDATES
from config import settings
from data.canonical_snapshot import load_frozen_snapshot
from execution.cost_contract import validate_research_cost_compatibility
from portfolio.q091_fixed_ensemble import ENSEMBLE_ID, RESIDUAL_ID, q091_targets_at

TRIAL_ID = "T-2026-09-29-091"
COVERAGE_ID = "T-2026-09-29-091-COVERAGE"
PIT_ID = "T-2026-09-29-091-PIT"
INPUT_ID = "T-2026-09-29-091-INPUT-FREEZE"
REQUESTED_CANDLES = 5000
N = 3500
RESEARCH = 2798
HOLDOUT = 700
INITIAL_CAPITAL_EUR = 2000.0
FEE = 0.001
SLIPPAGE = 0.0005
COSTS = (("base", 1.0), ("stress_1_5x_cost", 1.5), ("stress_2x_cost", 2.0))
VARIANTS = (ENSEMBLE_ID, RESIDUAL_ID)
GATE_NAMES = (
    "research_return_positive",
    "research_drawdown_lte_10pct",
    "research_profit_factor_gte_1_10",
    "rolling_profit_factor_gte_1_10",
    "rolling_profitable_window_ratio_gte_0_50",
    "rolling_average_drawdown_lte_10pct",
    "oos_to_is_return_ratio_gte_0_25",
    "holdout_return_positive",
    "holdout_profit_factor_gte_1_10",
    "holdout_drawdown_lte_10pct",
    "stress_1_5x_holdout_nonnegative",
    "stress_2x_holdout_nonnegative",
    "total_return_sensitivity_holdout_nonnegative",
)
SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


def _canonical(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _preflight(root: Path):
    coverage = _load(root / "research/evidence/q091_coverage_result.json")
    pit = _load(root / "research/evidence/q091_pit_result.json")
    freeze = _load(root / "research/evidence/q091_asset_freeze.json")
    input_receipt = _load(root / "research/evidence/q091_input_freeze_result.json")
    input_manifest = _load(
        root / "research/runs/q091_input_bundle/T-2026-09-29-091-INPUT-FREEZE/input_bundle_manifest.json"
    )
    prereg = _load(
        root / "research/preregistrations/q091_fixed_portfolio_architecture_2026_09_29.json"
    )

    if coverage.get("trial_id") != COVERAGE_ID or coverage.get("status") != "COVERAGE_PASSED":
        raise RuntimeError("Q091 coverage receipt invalid")
    if pit.get("trial_id") != PIT_ID or pit.get("status") != "PIT_PASSED":
        raise RuntimeError("Q091 PIT receipt invalid")
    if input_receipt.get("trial_id") != INPUT_ID or input_receipt.get("status") != "INPUT_BUNDLE_FROZEN":
        raise RuntimeError("Q091 input-freeze receipt invalid")
    if input_receipt.get("bundle_fingerprint") != input_manifest.get("bundle_fingerprint"):
        raise RuntimeError("Q091 input bundle receipt/manifest mismatch")
    if input_receipt.get("performance_evaluation") is not False:
        raise RuntimeError("Q091 input bundle is contaminated by performance evaluation")

    if prereg.get("trial_id") != TRIAL_ID or prereg.get("status") != "PREREGISTERED_PERFORMANCE":
        raise RuntimeError("Q091 performance preregistration invalid")
    if prereg.get("requested_candles") != REQUESTED_CANDLES:
        raise RuntimeError("Q091 requested candle geometry mismatch")
    if prereg.get("target_common_candles") != N or prereg.get("research_periods") != RESEARCH or prereg.get("holdout_periods") != HOLDOUT:
        raise RuntimeError("Q091 performance geometry mismatch")
    if prereg.get("safety") != SAFETY:
        raise RuntimeError("Q091 safety contract mismatch")
    if prereg.get("governance", {}).get("holdout_used_for_selection") is not False:
        raise RuntimeError("Q091 holdout selection state invalid")

    symbols = tuple(freeze["symbols"])
    if tuple(prereg.get("data_contract", {}).get("symbols", symbols)) != symbols:
        raise RuntimeError("Q091 preregistration symbol contract mismatch")
    snapshot_manifest = root / "research/runs/q091_coverage" / COVERAGE_ID / "snapshot_manifest.json"
    assets = load_frozen_snapshot(snapshot_manifest)
    if tuple(assets) != symbols or any(len(assets[s]) != N for s in symbols):
        raise RuntimeError("Q091 snapshot geometry mismatch")
    if coverage.get("snapshot_fingerprint") != freeze.get("snapshot_fingerprint"):
        raise RuntimeError("Q091 coverage/freeze snapshot fingerprint mismatch")
    if prereg.get("data_contract", {}).get("snapshot_fingerprint") != coverage.get("snapshot_fingerprint"):
        raise RuntimeError("Q091 preregistration/snapshot fingerprint mismatch")

    expected_bundle_fp = prereg.get("data_contract", {}).get("input_bundle_fingerprint")
    if expected_bundle_fp != input_receipt.get("bundle_fingerprint"):
        raise RuntimeError("Q091 preregistration/input bundle fingerprint mismatch")
    if tuple(input_manifest.get("symbols", ())) != symbols:
        raise RuntimeError("Q091 input bundle symbol mismatch")

    return assets, symbols, coverage, pit, freeze, input_receipt, input_manifest, prereg


def _assert_authorization(root: Path, prereg: dict) -> None:
    if prereg.get("governance", {}).get("performance_trial_authorized") is not True:
        raise RuntimeError("Q091 performance preregistration is not authorized")

    registry = _load(root / "research/governance/active_research_registry.json")
    entry = next((x for x in registry.get("active_trials", []) if x.get("code") == "091"), None)
    if entry is None or entry.get("trial_id") != TRIAL_ID or entry.get("performance_authorization_allowed") is not True:
        raise RuntimeError("Q091 active research registry does not authorize performance")

    auth_path = root / "research/authorizations/q091_performance_2026_09_29.json"
    if not auth_path.exists():
        raise RuntimeError("Q091 one-shot performance authorization missing")
    auth = _load(auth_path)
    if auth.get("trial_id") != TRIAL_ID:
        raise RuntimeError("Q091 authorization trial identity mismatch")
    if auth.get("authorized") is not True or auth.get("performance_execution_authorized") is not True or auth.get("one_shot") is not True:
        raise RuntimeError("Q091 authorization flags invalid")
    if auth.get("preregistration_fingerprint") != _fp(prereg):
        raise RuntimeError("Q091 authorization/preregistration fingerprint mismatch")
    if auth.get("input_bundle_fingerprint") != prereg["data_contract"]["input_bundle_fingerprint"]:
        raise RuntimeError("Q091 authorization/input bundle fingerprint mismatch")


def _assert_source_contract(root: Path, prereg: dict) -> None:
    contract = prereg.get("source_contract", {})
    expected_paths = {
        "performance_runner_sha256": root / "automation/q091_performance.py",
        "portfolio_architecture_sha256": root / "portfolio/q091_fixed_ensemble.py",
        "candidate_bank_sha256": root / "automation/q069_candidate_bank.py",
        "cost_contract_sha256": root / "execution/cost_contract.py",
        "settings_sha256": root / "config/settings.py",
        "input_freeze_sha256": root / "automation/q091_input_freeze.py",
    }
    for key, path in expected_paths.items():
        if not path.is_file():
            raise RuntimeError(f"Q091 source contract file missing: {path}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if contract.get(key) != digest:
            raise RuntimeError(f"Q091 source contract mismatch: {key}")


def _load_adjusted_bundle(root: Path, prereg: dict, symbols: tuple[str, ...]) -> dict[str, dict[datetime, float]]:
    bundle_root = root / "research/runs/q091_input_bundle" / INPUT_ID
    manifest = _load(bundle_root / "input_bundle_manifest.json")
    if manifest.get("bundle_fingerprint") != prereg["data_contract"]["input_bundle_fingerprint"]:
        raise RuntimeError("Q091 input bundle fingerprint mismatch")
    canonical = dict(manifest)
    actual = canonical.pop("bundle_fingerprint", None)
    if _fp(canonical) != actual:
        raise RuntimeError("Q091 input bundle self-fingerprint mismatch")

    adjusted: dict[str, dict[datetime, float]] = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        if symbol not in symbols:
            raise RuntimeError(f"Q091 input bundle contains unexpected symbol: {symbol}")
        rows = []
        with (bundle_root / item["path"]).open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                rows.append((str(row["timestamp"]), float(row["adjusted_close"])))
        if len(rows) != int(item["row_count"]):
            raise RuntimeError(f"{symbol}: adjusted-close row count mismatch")
        if _fp(rows) != item["fingerprint"]:
            raise RuntimeError(f"{symbol}: adjusted-close dataset fingerprint mismatch")
        adjusted[symbol] = {datetime.fromisoformat(ts): value for ts, value in rows}

    if set(adjusted) != set(symbols):
        raise RuntimeError("Q091 adjusted-close symbol set mismatch")
    return adjusted


def _rows(assets, weights: list[dict[str, float]], symbols: tuple[str, ...]) -> list[dict]:
    previous = {symbol: 0.0 for symbol in symbols}
    rows = []
    count = N - 2
    for i in range(count):
        gross = 0.0
        turnover = 0.0
        for symbol in symbols:
            bars = assets[symbol]
            realized = bars[i + 2].open / bars[i + 1].open - 1.0
            weight = float(weights[i].get(symbol, 0.0))
            gross += weight * realized
            turnover += abs(weight - previous[symbol])
            previous[symbol] = weight
        rows.append({
            "timestamp": assets[symbols[0]][i + 2].timestamp,
            "gross": gross,
            "turnover": turnover,
        })
    return rows


def _stats(values: list[float], start: int, end: int) -> dict:
    segment = values[start:end]
    equity = 1.0
    peak = 1.0
    gain = 0.0
    loss = 0.0
    positive = 0
    drawdown = 0.0
    for value in segment:
        equity *= 1.0 + value
        peak = max(peak, equity)
        drawdown = max(drawdown, 1.0 - equity / peak if equity > 0 else 1.0)
        if value > 0:
            gain += value
            positive += 1
        elif value < 0:
            loss -= value
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": drawdown * 100.0,
        "profit_factor": gain / loss if loss else ("inf" if gain else 0.0),
        "positive_day_ratio": positive / len(segment) if segment else 0.0,
        "day_count": len(segment),
    }


def _summary(values: list[float]) -> dict:
    research = _stats(values, 0, RESEARCH)
    holdout = _stats(values, RESEARCH, RESEARCH + HOLDOUT)
    width = RESEARCH // 5
    rolling = [
        _stats(values, i * width, RESEARCH if i == 4 else (i + 1) * width)
        for i in range(5)
    ]
    positive = sum(max(item["period_return"], 0.0) for item in rolling)
    negative = -sum(min(item["period_return"], 0.0) for item in rolling)
    rolling_pf = positive / negative if negative else ("inf" if positive else 0.0)
    return {
        "research": research,
        "holdout": holdout,
        "rolling_windows": [
            {"window_index": i + 1, **item} for i, item in enumerate(rolling)
        ],
        "rolling_profit_factor": rolling_pf,
        "rolling_profitable_window_ratio": sum(
            item["period_return"] > 0 for item in rolling
        ) / 5.0,
        "rolling_average_drawdown_percent": sum(
            item["max_drawdown_percent"] for item in rolling
        ) / 5.0,
        "oos_to_is_return_ratio": (
            holdout["period_return"] / research["period_return"]
            if research["period_return"] > 0 else 0.0
        ),
    }


def _evaluate(assets, weights: list[dict[str, float]], adjusted, symbols):
    rows = _rows(assets, weights, symbols)
    gross = [item["gross"] for item in rows]
    turnover = [item["turnover"] for item in rows]

    summaries = {}
    for cost_name, multiplier in COSTS:
        net = [
            value - (FEE + SLIPPAGE) * multiplier * t
            for value, t in zip(gross, turnover)
        ]
        summaries[cost_name] = _summary(net)

    sensitivity = []
    for i, row in enumerate(rows):
        current = row["timestamp"]
        previous = assets[symbols[0]][i + 1].timestamp
        value = 0.0
        for symbol in symbols:
            current_adj = adjusted[symbol].get(current)
            previous_adj = adjusted[symbol].get(previous)
            if current_adj is None or previous_adj is None:
                raise RuntimeError(f"{symbol}: adjusted close missing at {current}")
            bars = assets[symbol]
            open_return = bars[i + 2].open / bars[i + 1].open - 1.0
            close_return = bars[i + 2].close / bars[i + 1].close - 1.0
            adj_return = current_adj / previous_adj - 1.0
            value += float(weights[i].get(symbol, 0.0)) * (
                open_return + adj_return - close_return
            )
        sensitivity.append(value - (FEE + SLIPPAGE) * row["turnover"])

    sensitivity_summary = _summary(sensitivity)
    base = summaries["base"]
    stress15 = summaries["stress_1_5x_cost"]
    stress2 = summaries["stress_2x_cost"]
    research_pf = base["research"]["profit_factor"]
    rolling_pf = base["rolling_profit_factor"]
    holdout_pf = base["holdout"]["profit_factor"]

    gates = {
        "research_return_positive": base["research"]["period_return"] > 0.0,
        "research_drawdown_lte_10pct": base["research"]["max_drawdown_percent"] <= 10.0,
        "research_profit_factor_gte_1_10": research_pf == "inf" or research_pf >= 1.10,
        "rolling_profit_factor_gte_1_10": rolling_pf == "inf" or rolling_pf >= 1.10,
        "rolling_profitable_window_ratio_gte_0_50": base["rolling_profitable_window_ratio"] >= 0.50,
        "rolling_average_drawdown_lte_10pct": base["rolling_average_drawdown_percent"] <= 10.0,
        "oos_to_is_return_ratio_gte_0_25": base["oos_to_is_return_ratio"] >= 0.25,
        "holdout_return_positive": base["holdout"]["period_return"] > 0.0,
        "holdout_profit_factor_gte_1_10": holdout_pf == "inf" or holdout_pf >= 1.10,
        "holdout_drawdown_lte_10pct": base["holdout"]["max_drawdown_percent"] <= 10.0,
        "stress_1_5x_holdout_nonnegative": stress15["holdout"]["period_return"] >= 0.0,
        "stress_2x_holdout_nonnegative": stress2["holdout"]["period_return"] >= 0.0,
        "total_return_sensitivity_holdout_nonnegative": sensitivity_summary["holdout"]["period_return"] >= 0.0,
    }
    if tuple(gates) != GATE_NAMES:
        raise RuntimeError("Q091 gate definition drift")
    return {
        **summaries,
        "total_return_sensitivity": sensitivity_summary,
        "gates": gates,
        "gates_passed": sum(bool(value) for value in gates.values()),
        "gates_total": len(GATE_NAMES),
        "all_gates_passed": all(gates.values()),
        "turnover": {
            "mean": sum(turnover) / len(turnover) if turnover else 0.0,
            "sum": sum(turnover),
        },
    }


def run(root: Path, output: Path) -> dict:
    assets, symbols, coverage, pit, freeze, input_receipt, input_manifest, prereg = _preflight(root)
    _assert_authorization(root, prereg)
    _assert_source_contract(root, prereg)

    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False or settings.ORDERS_ENABLED is not False or settings.AUTOMATIC_PROMOTION is not False:
        raise RuntimeError("Q091 runtime safety invariants invalid")
    validate_research_cost_compatibility(fee_rate=FEE, slippage_rate=SLIPPAGE)

    weights = {variant: [] for variant in VARIANTS}
    for index in range(N):
        targets = q091_targets_at(assets, index, symbols=symbols)
        for variant in VARIANTS:
            weights[variant].append(targets[variant])

    adjusted = _load_adjusted_bundle(root, prereg, symbols)
    arms = {variant: _evaluate(assets, weights[variant], adjusted, symbols) for variant in VARIANTS}

    result = {
        "schema_version": "1.0",
        "trial_id": TRIAL_ID,
        "status": "COMPLETED",
        "code_version": os.getenv("GITHUB_SHA", "UNVERIFIED"),
        "universe": freeze["universe"],
        "symbols": list(symbols),
        "requested_candles": REQUESTED_CANDLES,
        "target_common_candles": N,
        "research_periods": RESEARCH,
        "holdout_periods": HOLDOUT,
        "initial_capital_eur": INITIAL_CAPITAL_EUR,
        "variants": list(VARIANTS),
        "parent_sleeves": list(CANDIDATES),
        "coverage_prerequisite": {
            "trial_id": COVERAGE_ID,
            "result_fingerprint": coverage["result_fingerprint"],
            "snapshot_fingerprint": coverage["snapshot_fingerprint"],
        },
        "pit_prerequisite": {
            "trial_id": PIT_ID,
            "result_fingerprint": pit["result_fingerprint"],
        },
        "input_bundle_prerequisite": {
            "trial_id": INPUT_ID,
            "bundle_fingerprint": input_receipt["bundle_fingerprint"],
        },
        "asset_freeze_fingerprint": _fp(freeze),
        "performance_evaluation": True,
        "oos_evaluation": True,
        "holdout_evaluation": True,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "parameter_search": False,
        "threshold_search": False,
        "asset_search": False,
        "horizon_search": False,
        "variant_search": False,
        "family_ranking": False,
        "governance": {
            "performance_trial_authorized": True,
            "selection": False,
            "holdout_used_for_selection": False,
            "promotion_decision": False,
            "automatic_promotion": False,
        },
        "safety": SAFETY,
        "arms": arms,
    }
    result["report_fingerprint"] = _fp(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    for variant in VARIANTS:
        report = arms[variant]
        print(f"{variant} {report['gates_passed']}/{report['gates_total']}")
    print("Q091_REPORT_FINGERPRINT:", result["report_fingerprint"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="research/evidence/q091_performance_result.json")
    args = parser.parse_args()
    run(Path(args.repo_root), Path(args.output))
