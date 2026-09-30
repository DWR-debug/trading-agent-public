"""C29 fixed-rule performance evaluation.

The C29 mechanism is evaluated on the frozen C29R1 input bundle after the
coverage, PIT and input-freeze receipts have passed. Two directions are
predeclared and evaluated symmetrically: long the four highest C29-gap assets
and long the four lowest C29-gap assets. There is no post-result selection.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from automation.frontier_feasibility import illusion_momentum_gap_at
from config import settings
from execution.cost_contract import validate_research_cost_compatibility

TRIAL_ID = "T-2026-09-30-C29-PERFORMANCE-01"
INPUT_FREEZE_TRIAL_ID = "T-2026-09-30-C29R1-INPUT-FREEZE"
INPUT_FREEZE_ARTIFACT_ID = 11109809098
INPUT_FREEZE_WORKFLOW_RUN_ID = 36742254954
COVERAGE_TRIAL_ID = "T-2026-09-30-C29R1-COVERAGE-PIT"
COVERAGE_FINGERPRINT = "6b3acf5fb179bc93c6fac8eaaef59d71aa909326d5f171d9718a7cfbc71e22a6"
SNAPSHOT_FINGERPRINT = "ca54223f855f3f11cff3868ff1287ec7a544e61036b35b6f0f3f29cab4a12e50"
PIT_TRIAL_ID = "T-2026-09-30-C29R1-COVERAGE-PIT"
PIT_FINGERPRINT = "d88c24271fec55186b5e3aad478d91acc7ebe3b6412193724170365f5b6729c6"
REPAIR_DISCOVERY_FINGERPRINT = "b7541fee48f01105d47ca0e89b05e1c20d14d73c5dad18dc1d2e876a21c4b05d"

SYMBOLS = ("PPG", "GWW", "PGR", "TT", "ICE", "KLAC", "SNA", "SWK")
TARGET_CANDLES = 3500
LOOKBACK = 21
EVALUATION_PERIODS = TARGET_CANDLES - LOOKBACK - 1
RESEARCH_PERIODS = EVALUATION_PERIODS - 700
HOLDOUT_PERIODS = 700
TOP_K = 4
INITIAL_CAPITAL_EUR = 2000.0
FEE = 0.001
SLIPPAGE = 0.0005
COST_SCENARIOS = (("base", 1.0), ("stress_1_5x_cost", 1.5), ("stress_2x_cost", 2.0))
ARMS = ("C29_HIGH_GAP_LONG_TOP4", "C29_LOW_GAP_LONG_BOTTOM4")
SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


def _fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_bundle(bundle_root: Path) -> dict[str, list[dict[str, float | str]]]:
    manifest = _load_json(bundle_root / "input_bundle_manifest.json")
    if manifest.get("trial_id") != INPUT_FREEZE_TRIAL_ID:
        raise RuntimeError("C29 input bundle trial identity mismatch")
    if manifest.get("bundle_fingerprint") is None:
        raise RuntimeError("C29 input bundle fingerprint missing")
    copy = dict(manifest)
    recorded = copy.pop("bundle_fingerprint")
    if _fp(copy) != recorded:
        raise RuntimeError("C29 input bundle self-fingerprint mismatch")
    if tuple(manifest.get("symbols", ())) != SYMBOLS:
        raise RuntimeError("C29 input bundle symbols mismatch")
    if manifest.get("target_common_candles") != TARGET_CANDLES:
        raise RuntimeError("C29 input bundle geometry mismatch")
    assets = {}
    for symbol in SYMBOLS:
        path = bundle_root / symbol / "1d.csv"
        if not path.is_file():
            raise FileNotFoundError(f"missing input bundle dataset: {symbol}")
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != TARGET_CANDLES:
            raise ValueError(f"{symbol}: expected {TARGET_CANDLES} rows, got {len(rows)}")
        normalized = []
        for row in rows:
            normalized.append(
                {
                    "timestamp": row["timestamp"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                }
            )
        assets[symbol] = normalized
    timestamps = [row["timestamp"] for row in assets[SYMBOLS[0]]]
    if any([row["timestamp"] for row in assets[symbol]] != timestamps for symbol in SYMBOLS[1:]):
        raise RuntimeError("C29 input bundle timestamps are not aligned")
    return assets


def _weight_map(assets: dict[str, list[dict[str, float | str]]], decision_index: int) -> tuple[dict[str, float], dict[str, float]]:
    scores = {
        symbol: illusion_momentum_gap_at(
            [float(row["close"]) for row in assets[symbol]],
            decision_index,
            lookback_sessions=LOOKBACK,
        )
        for symbol in SYMBOLS
    }
    order = sorted(SYMBOLS, key=lambda symbol: (-scores[symbol], symbol))
    high = {symbol: (1.0 / TOP_K if symbol in order[:TOP_K] else 0.0) for symbol in SYMBOLS}
    low = {symbol: (1.0 / TOP_K if symbol in order[-TOP_K:] else 0.0) for symbol in SYMBOLS}
    return high, low


def _stats(values: list[float]) -> dict:
    equity = 1.0
    peak = 1.0
    gain = 0.0
    loss = 0.0
    max_dd = 0.0
    positive = 0
    for value in values:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak if equity > 0 else 1.0)
        if value > 0.0:
            gain += value
            positive += 1
        elif value < 0.0:
            loss -= value
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": gain / loss if loss else ("inf" if gain else 0.0),
        "positive_day_ratio": positive / len(values) if values else 0.0,
        "day_count": len(values),
    }


def _summary(values: list[float]) -> dict:
    research = _stats(values[:RESEARCH_PERIODS])
    holdout = _stats(values[RESEARCH_PERIODS:RESEARCH_PERIODS + HOLDOUT_PERIODS])
    width = RESEARCH_PERIODS // 5
    windows = []
    start = 0
    for idx in range(5):
        end = RESEARCH_PERIODS if idx == 4 else start + width
        windows.append(_stats(values[start:end]))
        start = end
    gains = sum(max(x["period_return"], 0.0) for x in windows)
    losses = -sum(min(x["period_return"], 0.0) for x in windows)
    rolling_pf = gains / losses if losses else ("inf" if gains else 0.0)
    return {
        "research": research,
        "holdout": holdout,
        "rolling_windows": [{"window_index": i + 1, **item} for i, item in enumerate(windows)],
        "rolling_profit_factor": rolling_pf,
        "rolling_profitable_window_ratio": sum(x["period_return"] > 0.0 for x in windows) / 5.0,
        "rolling_average_drawdown_percent": sum(x["max_drawdown_percent"] for x in windows) / 5.0,
        "oos_to_is_return_ratio": (
            holdout["period_return"] / research["period_return"]
            if research["period_return"] > 0.0 else 0.0
        ),
    }


def _evaluate(assets: dict[str, list[dict[str, float | str]]], arm: str, multiplier: float) -> dict:
    net_returns = []
    sensitivity_returns = []
    scores_fingerprint_rows = []
    previous_weights = {symbol: 0.0 for symbol in SYMBOLS}
    for decision_index in range(LOOKBACK, TARGET_CANDLES - 1):
        high, low = _weight_map(assets, decision_index)
        weights = high if arm == "C29_HIGH_GAP_LONG_TOP4" else low
        next_row_index = decision_index + 1
        gross = sum(
            weights[symbol] * (
                float(assets[symbol][next_row_index]["close"])
                / float(assets[symbol][next_row_index]["open"]) - 1.0
            )
            for symbol in SYMBOLS
        )
        sensitivity = sum(
            weights[symbol] * (
                float(assets[symbol][next_row_index]["close"])
                / float(assets[symbol][decision_index]["close"]) - 1.0
            )
            for symbol in SYMBOLS
        )
        turnover = sum(abs(weights[symbol] - previous_weights[symbol]) for symbol in SYMBOLS)
        cost = (FEE + SLIPPAGE) * multiplier * turnover
        previous_weights = dict(weights)
        net_returns.append(gross - cost)
        sensitivity_returns.append(sensitivity - cost)
        scores_fingerprint_rows.append(
            {
                "decision_index": decision_index,
                "weights": {symbol: weights[symbol] for symbol in SYMBOLS},
            }
        )
    reports = _summary(net_returns)
    sensitivity = _summary(sensitivity_returns)
    reports["total_return_sensitivity"] = sensitivity
    return reports | {
        "turnover": {
            "model": "absolute_target_weight_change",
            "total": sum(
                abs(
                    scores_fingerprint_rows[i]["weights"][symbol]
                    - (scores_fingerprint_rows[i - 1]["weights"][symbol] if i else 0.0)
                )
                for i in range(len(scores_fingerprint_rows))
                for symbol in SYMBOLS
            ),
        },
        "score_assignment_fingerprint": _fp(scores_fingerprint_rows),
    }


def _scenario_gates(scenarios: dict[str, dict]) -> dict[str, bool]:
    base = scenarios["base"]
    research = base["research"]
    holdout = base["holdout"]
    pf = lambda value: float("inf") if value == "inf" else float(value)
    gates = {
        "research_return_positive": research["period_return"] > 0.0,
        "research_drawdown_lte_10pct": research["max_drawdown_percent"] <= 10.0,
        "research_profit_factor_gte_1_10": pf(research["profit_factor"]) >= 1.10,
        "rolling_profit_factor_gte_1_10": pf(base["rolling_profit_factor"]) >= 1.10,
        "rolling_profitable_window_ratio_gte_0_50": base["rolling_profitable_window_ratio"] >= 0.50,
        "rolling_average_drawdown_lte_10pct": base["rolling_average_drawdown_percent"] <= 10.0,
        "oos_to_is_return_ratio_gte_0_25": base["oos_to_is_return_ratio"] >= 0.25,
        "holdout_return_positive": holdout["period_return"] > 0.0,
        "holdout_profit_factor_gte_1_10": pf(holdout["profit_factor"]) >= 1.10,
        "holdout_drawdown_lte_10pct": holdout["max_drawdown_percent"] <= 10.0,
        "stress_1_5x_holdout_nonnegative": scenarios["stress_1_5x_cost"]["holdout"]["period_return"] >= 0.0,
        "stress_2x_holdout_nonnegative": scenarios["stress_2x_cost"]["holdout"]["period_return"] >= 0.0,
        "total_return_sensitivity_holdout_nonnegative": base["total_return_sensitivity"]["holdout"]["period_return"] >= 0.0,
    }
    return gates


def _assert_source_contract(repo_root: Path, prereg: dict) -> None:
    contract = prereg.get("source_contract", {})
    paths = {
        "performance_runner_git_blob_sha": repo_root / "automation/c29_performance.py",
        "frontier_feasibility_git_blob_sha": repo_root / "automation/frontier_feasibility.py",
        "cost_contract_git_blob_sha": repo_root / "execution/cost_contract.py",
        "settings_git_blob_sha": repo_root / "config/settings.py",
        "input_freeze_git_blob_sha": repo_root / "automation/c29r1_input_freeze.py",
    }
    import subprocess
    for key, path in paths.items():
        expected = contract.get(key)
        if not expected:
            raise RuntimeError(f"C29 source contract incomplete: {key}")
        actual = subprocess.check_output(
            ["git", "hash-object", str(path)],
            text=True,
        ).strip()
        if actual != expected:
            raise RuntimeError(f"C29 source contract mismatch: {key}")


def _assert_authorization(repo_root: Path, prereg: dict) -> dict:
    auth_path = repo_root / "research/authorizations/c29_performance_2026_09_30.json"
    if not auth_path.is_file():
        raise RuntimeError("C29 performance authorization missing")
    auth = _load_json(auth_path)
    if auth.get("trial_id") != TRIAL_ID or auth.get("authorized") is not True:
        raise RuntimeError("C29 authorization identity invalid")
    if auth.get("performance_execution_authorized") is not True or auth.get("one_shot") is not True:
        raise RuntimeError("C29 performance authorization flags invalid")
    if auth.get("preregistration_fingerprint") != _fp(prereg):
        raise RuntimeError("C29 authorization/preregistration fingerprint mismatch")
    if auth.get("input_bundle_fingerprint") != prereg["data_contract"]["input_bundle_fingerprint"]:
        raise RuntimeError("C29 authorization/input bundle fingerprint mismatch")
    return auth


def _assert_registry(repo_root: Path) -> None:
    registry = _load_json(repo_root / "research/governance/active_research_registry.json")
    entry = next((x for x in registry.get("active_trials", []) if x.get("code") == "C29P1"), None)
    if entry is None or entry.get("trial_id") != TRIAL_ID:
        raise RuntimeError("C29P1 registry identity missing")
    if entry.get("performance_authorization_allowed") is not True or entry.get("state") != "PERFORMANCE_AUTHORIZED":
        raise RuntimeError("C29P1 registry is not authorized")


def run(preregistration: Path, repo_root: Path, bundle_root: Path, output: Path) -> dict:
    prereg = _load_json(preregistration)
    if prereg.get("trial_id") != TRIAL_ID or prereg.get("status") != "PREREGISTERED_PERFORMANCE":
        raise RuntimeError("C29 performance preregistration invalid")
    if prereg.get("governance", {}).get("performance_trial_authorized") is not True:
        raise RuntimeError("C29 performance preregistration not authorized")
    if prereg.get("safety") != SAFETY:
        raise RuntimeError("C29 safety mismatch")
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False or settings.ORDERS_ENABLED is not False or settings.AUTOMATIC_PROMOTION is not False:
        raise RuntimeError("runtime safety invariants violated")
    _assert_authorization(repo_root, prereg)
    _assert_source_contract(repo_root, prereg)
    _assert_registry(repo_root)
    validate_research_cost_compatibility(fee_rate=FEE, slippage_rate=SLIPPAGE)
    bundle = _load_json(bundle_root / "input_bundle_manifest.json")
    if bundle.get("bundle_fingerprint") != prereg["data_contract"]["input_bundle_fingerprint"]:
        raise RuntimeError("C29 input bundle fingerprint mismatch")
    if bundle.get("source_coverage_fingerprint") != COVERAGE_FINGERPRINT or bundle.get("source_snapshot_fingerprint") != SNAPSHOT_FINGERPRINT:
        raise RuntimeError("C29 input bundle source receipt mismatch")
    assets = _read_bundle(bundle_root)

    arms = {}
    for arm in ARMS:
        scenarios = {}
        for name, multiplier in COST_SCENARIOS:
            scenarios[name] = _evaluate(assets, arm, multiplier)
        gates = _scenario_gates(scenarios)
        arms[arm] = {
            "scenarios": scenarios,
            "gates": gates,
            "gates_passed": sum(gates.values()),
            "gates_total": 13,
            "all_gates_passed": all(gates.values()),
        }

    result = {
        "schema_version": "1.0",
        "trial_id": TRIAL_ID,
        "status": "PERFORMANCE_COMPLETED_ARM_PASSED_ALL_13_GATES" if any(x["all_gates_passed"] for x in arms.values()) else "PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES",
        "universe": prereg["universe"],
        "symbols": list(SYMBOLS),
        "requested_candles": TARGET_CANDLES,
        "target_common_candles": TARGET_CANDLES,
        "lookback_sessions": LOOKBACK,
        "evaluation_periods": EVALUATION_PERIODS,
        "research_periods": RESEARCH_PERIODS,
        "holdout_periods": HOLDOUT_PERIODS,
        "initial_capital_eur": INITIAL_CAPITAL_EUR,
        "execution_model": "open_to_close_same_session_after_previous_close_signal",
        "arms": arms,
        "coverage_prerequisite": {
            "trial_id": COVERAGE_TRIAL_ID,
            "coverage_fingerprint": COVERAGE_FINGERPRINT,
            "snapshot_fingerprint": SNAPSHOT_FINGERPRINT,
        },
        "pit_prerequisite": {
            "trial_id": PIT_TRIAL_ID,
            "result_fingerprint": PIT_FINGERPRINT,
        },
        "repair_discovery_prerequisite": {
            "fingerprint": REPAIR_DISCOVERY_FINGERPRINT,
            "replacement": "IR -> ICE",
        },
        "input_bundle_prerequisite": {
            "trial_id": INPUT_FREEZE_TRIAL_ID,
            "workflow_run_id": INPUT_FREEZE_WORKFLOW_RUN_ID,
            "artifact_id": INPUT_FREEZE_ARTIFACT_ID,
            "bundle_fingerprint": bundle["bundle_fingerprint"],
        },
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
    }
    result["report_fingerprint"] = _fp(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print("C29_PERFORMANCE_STATUS:", result["status"])
    for arm, report in arms.items():
        print(arm, f"{report['gates_passed']}/{report['gates_total']}")
    print("C29_PERFORMANCE_REPORT_FINGERPRINT:", result["report_fingerprint"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.preregistration, args.repo_root, args.bundle_root, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
