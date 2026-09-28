"""Q079 fixed-rule performance evaluation for E1 and E2.

Execution is allowed only after the immutable Q079 coverage and PIT receipts pass.
The three arms are evaluated symmetrically: unmodified six-sleeve ensemble,
E1 alpha common-mode throttle, and E2 turnover hysteresis.

No parameter search, asset search, ranking, holdout selection, promotion or live
execution is performed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

from automation.q067_alpha_mechanisms import (
    Q067_SLEEVES,
    Q067_SYMBOLS,
    RETURN_COUNT,
    apply_common_mode_throttle,
    apply_turnover_hysteresis,
    build_alpha_sleeves,
    common_mode_multipliers,
    equal_weight_ensemble,
    sleeve_period_returns,
    validate_gross_exposure_cap,
)
from config import settings
from data.canonical_snapshot import load_frozen_snapshot
from execution.cost_contract import validate_research_cost_compatibility

Q079_SLEEVES = Q067_SLEEVES
INPUT_BUNDLE_TRIAL_ID = "T-2026-09-28-079-INPUT-FREEZE"

TRIAL_ID = "T-2026-09-28-079-PERFORMANCE"
COVERAGE_TRIAL_ID = "T-2026-09-28-079-COVERAGE"
PIT_TRIAL_ID = "T-2026-09-28-079-PIT"
Q079_SYMBOLS = (
    "HAL",
    "LRCX",
    "OXY",
    "COF",
    "FIS",
    "FISV",
    "GM",
    "LHX",
)
N = 3500
RESEARCH = 2798
HOLDOUT = 700
FEE = 0.001
SLIPPAGE = 0.0005
COSTS = (("base", 1.0), ("stress_1_5x_cost", 1.5), ("stress_2x_cost", 2.0))


def _fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_preflight(repo_root: Path) -> tuple[dict[str, tuple], dict, dict]:
    coverage_result = _load_json(repo_root / "research/evidence/q079_coverage_result.json")
    pit_result = _load_json(repo_root / "research/evidence/q079_pit_result.json")

    if coverage_result.get("trial_id") != COVERAGE_TRIAL_ID:
        raise RuntimeError("Q079 coverage trial identity mismatch")
    if coverage_result.get("status") != "COVERAGE_PASSED":
        raise RuntimeError("Q079 coverage prerequisite did not pass")
    if coverage_result.get("performance_trial_authorized") is not False:
        raise RuntimeError("Q079 coverage receipt unexpectedly authorizes performance")
    if coverage_result.get("selection_used") is not False:
        raise RuntimeError("Q079 coverage receipt indicates selection")

    if pit_result.get("trial_id") != PIT_TRIAL_ID:
        raise RuntimeError("Q079 PIT trial identity mismatch")
    if pit_result.get("status") != "PIT_PASSED":
        raise RuntimeError("Q079 PIT prerequisite did not pass")
    if pit_result.get("performance_trial_authorized") is not False:
        raise RuntimeError("Q079 PIT receipt unexpectedly authorizes performance")
    if pit_result.get("selection_used") is not False:
        raise RuntimeError("Q079 PIT receipt indicates selection")

    coverage_root = repo_root / "research/runs/q079_coverage" / COVERAGE_TRIAL_ID
    assets = load_frozen_snapshot(coverage_root / "snapshot_manifest.json")
    if tuple(assets) != Q079_SYMBOLS:
        raise RuntimeError("Q067 frozen snapshot symbols mismatch")
    if any(len(assets[symbol]) != N for symbol in Q079_SYMBOLS):
        raise RuntimeError("Q067 frozen snapshot geometry mismatch")

    return assets, coverage_result, pit_result


def _rows(assets, weights):
    previous = {symbol: 0.0 for symbol in Q079_SYMBOLS}
    rows = []
    for i in range(RETURN_COUNT):
        gross = 0.0
        turnover = 0.0
        for symbol in Q079_SYMBOLS:
            bars = assets[symbol]
            holding_return = bars[i + 2].open / bars[i + 1].open - 1.0
            weight = float(weights[i].get(symbol, 0.0))
            gross += weight * holding_return
            turnover += abs(weight - previous[symbol])
            previous[symbol] = weight
        rows.append({
            "timestamp": assets[Q079_SYMBOLS[0]][i + 2].timestamp,
            "gross": gross,
            "turnover": turnover,
        })
    return rows


def _stats(values, start, end):
    segment = values[start:end]
    equity = 1.0
    peak = 1.0
    gain = 0.0
    loss = 0.0
    positive = 0
    max_dd = 0.0

    for value in segment:
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
        "positive_day_ratio": positive / len(segment) if segment else 0.0,
        "day_count": len(segment),
    }


def _summary(values):
    research = _stats(values, 0, RESEARCH)
    holdout = _stats(values, RESEARCH, RETURN_COUNT)
    width = RESEARCH // 5
    rolling = [
        _stats(values, i * width, RESEARCH if i == 4 else (i + 1) * width)
        for i in range(5)
    ]
    positive_sum = sum(max(item["period_return"], 0.0) for item in rolling)
    negative_sum = -sum(min(item["period_return"], 0.0) for item in rolling)
    rolling_pf = positive_sum / negative_sum if negative_sum else ("inf" if positive_sum else 0.0)
    return {
        "research": research,
        "holdout": holdout,
        "rolling_windows": [
            {"window_index": index + 1, **item}
            for index, item in enumerate(rolling)
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
            if research["period_return"] > 0
            else 0.0
        ),
    }


def _load_adjusted_bundle(repo_root: Path) -> tuple[dict, dict]:
    bundle_root = repo_root / "research/runs/q079_input_bundle/T-2026-09-28-079-INPUT-FREEZE"
    manifest = _load_json(bundle_root / "input_bundle_manifest.json")
    if manifest.get("trial_id") != INPUT_BUNDLE_TRIAL_ID:
        raise RuntimeError("Q079 input bundle identity mismatch")
    if manifest.get("performance_network_access") is not False:
        raise RuntimeError("Q079 input bundle allows network access")
    adjusted = {}
    for dataset in manifest.get("datasets", []):
        symbol = dataset["symbol"]
        path = bundle_root / dataset["path"]
        if not path.exists():
            raise RuntimeError(f"{symbol}: adjusted-close file missing")
        values = {}
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            if list(reader.fieldnames or []) != ["timestamp", "adjusted_close"]:
                raise RuntimeError(f"{symbol}: adjusted-close schema mismatch")
            for row in reader:
                values[datetime.fromisoformat(row["timestamp"])] = float(row["adjusted_close"])
        if len(values) != int(dataset["row_count"]):
            raise RuntimeError(f"{symbol}: adjusted-close row count mismatch")
        digest = _fp([[ts.isoformat(), value] for ts, value in sorted(values.items())])
        if digest != dataset["fingerprint"]:
            raise RuntimeError(f"{symbol}: adjusted-close fingerprint mismatch")
        adjusted[symbol] = values
    if tuple(adjusted) != Q079_SYMBOLS:
        raise RuntimeError("Q079 adjusted-close symbol order mismatch")
    return manifest, adjusted

def _evaluate(assets, weights, adjusted):
    rows = _rows(assets, weights)
    gross = [row["gross"] for row in rows]
    turnover = [row["turnover"] for row in rows]

    stressed = {}
    for name, multiplier in COSTS:
        stressed[name] = _summary(
            [
                value - (FEE + SLIPPAGE) * multiplier * turn
                for value, turn in zip(gross, turnover)
            ]
        )

    total_return_sensitivity = []
    for index, row in enumerate(rows):
        current_timestamp = row["timestamp"]
        previous_timestamp = assets[Q079_SYMBOLS[0]][index + 1].timestamp
        sensitivity = 0.0
        for symbol in Q079_SYMBOLS:
            current_adj = adjusted[symbol].get(current_timestamp)
            previous_adj = adjusted[symbol].get(previous_timestamp)
            if current_adj is None or previous_adj is None:
                raise RuntimeError(f"{symbol}: adjusted close missing at {current_timestamp}")
            bars = assets[symbol]
            open_return = bars[index + 2].open / bars[index + 1].open - 1.0
            close_return = bars[index + 2].close / bars[index + 1].close - 1.0
            adjusted_return = current_adj / previous_adj - 1.0
            sensitivity += float(weights[index].get(symbol, 0.0)) * (
                open_return + adjusted_return - close_return
            )
        total_return_sensitivity.append(
            sensitivity - (FEE + SLIPPAGE) * turnover[index]
        )

    base = stressed["base"]
    sensitivity = _summary(total_return_sensitivity)
    pf = base["research"]["profit_factor"]
    rolling_pf = base["rolling_profit_factor"]
    holdout_pf = base["holdout"]["profit_factor"]

    gates = {
        "research_return_positive": base["research"]["period_return"] > 0.0,
        "research_drawdown_lte_10pct": base["research"]["max_drawdown_percent"] <= 10.0,
        "research_profit_factor_gte_1_10": (
            pf == "inf" or pf >= 1.10
        ),
        "rolling_profit_factor_gte_1_10": (
            rolling_pf == "inf" or rolling_pf >= 1.10
        ),
        "rolling_profitable_window_ratio_gte_0_50": (
            base["rolling_profitable_window_ratio"] >= 0.50
        ),
        "rolling_average_drawdown_lte_10pct": (
            base["rolling_average_drawdown_percent"] <= 10.0
        ),
        "oos_to_is_return_ratio_gte_0_25": (
            base["oos_to_is_return_ratio"] >= 0.25
        ),
        "holdout_return_positive": base["holdout"]["period_return"] > 0.0,
        "holdout_profit_factor_gte_1_10": (
            holdout_pf == "inf" or holdout_pf >= 1.10
        ),
        "holdout_drawdown_lte_10pct": base["holdout"]["max_drawdown_percent"] <= 10.0,
        "stress_1_5x_holdout_nonnegative": (
            stressed["stress_1_5x_cost"]["holdout"]["period_return"] >= 0.0
        ),
        "stress_2x_holdout_nonnegative": (
            stressed["stress_2x_cost"]["holdout"]["period_return"] >= 0.0
        ),
        "total_return_sensitivity_holdout_nonnegative": (
            sensitivity["holdout"]["period_return"] >= 0.0
        ),
    }
    return {
        "base": base,
        "stress_1_5x_cost": stressed["stress_1_5x_cost"],
        "stress_2x_cost": stressed["stress_2x_cost"],
        "total_return_sensitivity": sensitivity,
        "gates": gates,
        "gates_passed": sum(bool(value) for value in gates.values()),
        "gates_total": 13,
        "all_gates_passed": all(gates.values()),
        "turnover": {
            "mean": sum(turnover) / len(turnover),
            "sum": sum(turnover),
        },
    }


def run(preregistration: Path, repo_root: Path, output: Path) -> dict:
    prereg = _load_json(preregistration)
    if prereg.get("trial_id") != TRIAL_ID:
        raise ValueError("Q079 performance preregistration trial id mismatch")
    if prereg.get("status") != "PREREGISTERED_PERFORMANCE":
        raise ValueError("Q079 performance preregistration status mismatch")

    safety = {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    if prereg.get("safety") != safety:
        raise RuntimeError("Q079 performance safety mismatch")
    governance = prereg.get("governance", {})
    for key in (
        "parameter_search",
        "threshold_search",
        "asset_search",
        "horizon_search",
        "variant_search",
        "family_ranking",
        "selection",
        "holdout_used_for_selection",
        "promotion_decision",
        "automatic_promotion",
    ):
        if governance.get(key) is not False:
            raise RuntimeError(f"Q067 forbidden governance flag is true: {key}")

    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("runtime safety flags invalid")
    if settings.ORDERS_ENABLED is not False or settings.AUTOMATIC_PROMOTION is not False:
        raise RuntimeError("runtime order/promotion flags invalid")

    validate_research_cost_compatibility(fee_rate=FEE, slippage_rate=SLIPPAGE)
    assets, coverage_result, pit_result = _assert_preflight(repo_root)

    sleeves = build_alpha_sleeves(assets, symbols=Q079_SYMBOLS)
    aggregate = equal_weight_ensemble(sleeves, symbols=Q079_SYMBOLS)
    sleeve_returns = sleeve_period_returns(
        assets,
        sleeves,
        symbols=Q079_SYMBOLS,
    )
    e1 = apply_common_mode_throttle(
        aggregate,
        sleeve_returns,
        symbols=Q079_SYMBOLS,
    )
    e2 = apply_turnover_hysteresis(
        aggregate,
        symbols=Q079_SYMBOLS,
    )

    bundle_manifest, adjusted = _load_adjusted_bundle(repo_root)
    if bundle_manifest.get("bundle_fingerprint") is None:
        raise RuntimeError("Q079 input bundle fingerprint missing")

    arms = {
        "CONTROL_6SLEEVE_ENSEMBLE": aggregate,
        "E1_ALPHA_COMMON_MODE_THROTTLE": e1,
        "E2_TURNOVER_HYSTERESIS": e2,
    }

    for name, weights in arms.items():
        validate_gross_exposure_cap(weights, symbols=Q079_SYMBOLS)

    reports = {name: _evaluate(assets, weights, adjusted) for name, weights in arms.items()}
    result = {
        "schema_version": "1.0",
        "trial_id": TRIAL_ID,
        "status": "COMPLETED",
        "code_version": os.getenv("GITHUB_SHA", "UNVERIFIED"),
        "universe": prereg["universe"],
        "symbols": list(Q079_SYMBOLS),
        "requested_candles": prereg["requested_candles"],
        "target_common_candles": prereg["target_common_candles"],
        "research_periods": RESEARCH,
        "holdout_periods": HOLDOUT,
        "initial_capital_eur": 2000.0,
        "coverage_prerequisite": {
            "trial_id": COVERAGE_TRIAL_ID,
            "result_fingerprint": coverage_result["result_fingerprint"],
            "snapshot_fingerprint": coverage_result["snapshot_fingerprint"],
        },
        "pit_prerequisite": {
            "trial_id": PIT_TRIAL_ID,
            "result_fingerprint": pit_result["result_fingerprint"],
        },
        "input_bundle_prerequisite": {
            "trial_id": INPUT_BUNDLE_TRIAL_ID,
            "bundle_fingerprint": bundle_manifest["bundle_fingerprint"],
        },
        "arms": reports,
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
        "safety": safety,
    }
    result["report_fingerprint"] = _fp(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print("Q079_STATUS: COMPLETED")
    for name, report in reports.items():
        print(name, f"{report['gates_passed']}/{report['gates_total']}")
    print("Q079_REPORT_FINGERPRINT:", result["report_fingerprint"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(Path(args.preregistration), Path(args.repo_root), Path(args.output))
