from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_TRIAL_ID = "T-2026-09-30-081R4-PERFORMANCE"
EXPECTED_REPORT_FINGERPRINT = "b57f93d2ebd1076f191076ea77ad37ca5dfd7cf4f8da5fdb0f4047b4217ea30a"
EXPECTED_COMMON_FAILED_GATES = {
    "research_drawdown_lte_10pct",
    "rolling_average_drawdown_lte_10pct",
    "oos_to_is_return_ratio_gte_0_25",
    "holdout_drawdown_lte_10pct",
}
EXPECTED_COMMON_PASSED_GATES = {
    "research_return_positive",
    "research_profit_factor_gte_1_10",
    "rolling_profit_factor_gte_1_10",
    "rolling_profitable_window_ratio_gte_0_50",
    "holdout_return_positive",
    "holdout_profit_factor_gte_1_10",
    "stress_1_5x_holdout_nonnegative",
    "stress_2x_holdout_nonnegative",
    "total_return_sensitivity_holdout_nonnegative",
}


def load_result(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError("Q099_SOURCE_RESULT_MUST_BE_OBJECT")
    return result


def diagnose(result: dict) -> dict:
    if result.get("trial_id") != EXPECTED_TRIAL_ID:
        raise ValueError("Q099_UNEXPECTED_TRIAL_ID")
    if result.get("report_fingerprint") != EXPECTED_REPORT_FINGERPRINT:
        raise ValueError("Q099_RESULT_FINGERPRINT_MISMATCH")
    if result.get("status") != "COMPLETED":
        raise ValueError("Q099_SOURCE_RESULT_NOT_COMPLETED")
    if result.get("selection_used") is not False:
        raise ValueError("Q099_SELECTION_GUARD_FAILED")
    if result.get("holdout_used_for_selection") is not False:
        raise ValueError("Q099_HOLDOUT_SELECTION_GUARD_FAILED")
    if result.get("parameter_search") is not False:
        raise ValueError("Q099_PARAMETER_SEARCH_GUARD_FAILED")
    if result.get("threshold_search") is not False:
        raise ValueError("Q099_THRESHOLD_SEARCH_GUARD_FAILED")
    if result.get("asset_search") is not False:
        raise ValueError("Q099_ASSET_SEARCH_GUARD_FAILED")
    if result.get("horizon_search") is not False:
        raise ValueError("Q099_HORIZON_SEARCH_GUARD_FAILED")
    if result.get("variant_search") is not False:
        raise ValueError("Q099_VARIANT_SEARCH_GUARD_FAILED")
    if result.get("family_ranking") is not False:
        raise ValueError("Q099_FAMILY_RANKING_GUARD_FAILED")

    arms = result.get("arms")
    if not isinstance(arms, dict) or len(arms) != 3:
        raise ValueError("Q099_EXPECTED_EXACTLY_THREE_ARMS")

    arm_rows = {}
    failed_sets = []
    passed_sets = []
    worst_window_indices = []

    for arm_name, arm in arms.items():
        gates = arm.get("gates")
        rolling = arm.get("base", {}).get("rolling_windows")
        if not isinstance(gates, dict) or not isinstance(rolling, list) or not rolling:
            raise ValueError(f"Q099_INCOMPLETE_ARM_DATA:{arm_name}")

        failed = {name for name, value in gates.items() if value is False}
        passed = {name for name, value in gates.items() if value is True}
        failed_sets.append(failed)
        passed_sets.append(passed)

        worst = max(
            rolling,
            key=lambda row: float(row["max_drawdown_percent"]),
        )
        worst_window_indices.append(int(worst["window_index"]))

        arm_rows[arm_name] = {
            "research_max_drawdown_percent": arm["base"]["research"]["max_drawdown_percent"],
            "holdout_max_drawdown_percent": arm["base"]["holdout"]["max_drawdown_percent"],
            "holdout_return": arm["base"]["holdout"]["period_return"],
            "holdout_profit_factor": arm["base"]["holdout"]["profit_factor"],
            "oos_to_is_return_ratio": arm["base"]["oos_to_is_return_ratio"],
            "worst_rolling_window": {
                "window_index": int(worst["window_index"]),
                "period_return": worst["period_return"],
                "max_drawdown_percent": worst["max_drawdown_percent"],
                "profit_factor": worst["profit_factor"],
            },
            "stress_holdout_returns": {
                "1_5x_cost": arm["stress_1_5x_cost"]["holdout"]["period_return"],
                "2x_cost": arm["stress_2x_cost"]["holdout"]["period_return"],
                "total_return_sensitivity": arm["total_return_sensitivity"]["holdout"]["period_return"],
            },
            "gates_failed": sorted(failed),
            "gates_passed": sorted(passed),
        }

    common_failed = set.intersection(*failed_sets)
    common_passed = set.intersection(*passed_sets)
    if common_failed != EXPECTED_COMMON_FAILED_GATES:
        raise ValueError(f"Q099_COMMON_FAILED_GATE_MISMATCH:{sorted(common_failed)}")
    if common_passed != EXPECTED_COMMON_PASSED_GATES:
        raise ValueError(f"Q099_COMMON_PASSED_GATE_MISMATCH:{sorted(common_passed)}")

    all_share_worst_window = len(set(worst_window_indices)) == 1
    worst_window = worst_window_indices[0] if all_share_worst_window else None
    if not all_share_worst_window:
        raise ValueError("Q099_WORST_WINDOW_NOT_COMMON_ACROSS_ARMS")

    return {
        "schema_version": "1.0",
        "task_id": "Q-2026-09-30-099-Q081R4-FAILURE-DIAGNOSIS",
        "status": "DIAGNOSTIC_ONLY",
        "source": {
            "trial_id": EXPECTED_TRIAL_ID,
            "report_fingerprint": EXPECTED_REPORT_FINGERPRINT,
            "research_periods": result["research_periods"],
            "holdout_periods": result["holdout_periods"],
            "symbols": result["symbols"],
        },
        "common_failure_signature": {
            "gates_failed_by_all_arms": sorted(common_failed),
            "gates_passed_by_all_arms": sorted(common_passed),
            "failed_gate_count": len(common_failed),
            "passed_gate_count": len(common_passed),
            "dimensions": ["drawdown_and_risk", "research_to_holdout_transfer_ratio"],
        },
        "rolling_window_diagnosis": {
            "all_arms_share_worst_rolling_window": all_share_worst_window,
            "shared_worst_window_index": worst_window,
            "basis": "descriptive maximum rolling-window drawdown; no arm selection",
        },
        "arms": arm_rows,
        "stress_diagnosis": {
            "all_arms_positive_holdout_return_at_1_5x_cost": all(
                row["stress_holdout_returns"]["1_5x_cost"] >= 0 for row in arm_rows.values()
            ),
            "all_arms_positive_holdout_return_at_2x_cost": all(
                row["stress_holdout_returns"]["2x_cost"] >= 0 for row in arm_rows.values()
            ),
            "all_arms_positive_holdout_return_under_total_return_sensitivity": all(
                row["stress_holdout_returns"]["total_return_sensitivity"] >= 0
                for row in arm_rows.values()
            ),
        },
        "governance": {
            "performance_evaluation": False,
            "holdout_evaluation": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "horizon_search": False,
            "variant_search": False,
            "performance_authorized": False,
            "automatic_promotion": False,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "paper_only": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--result",
        type=Path,
        default=Path("research/evidence/q081r4_performance_result.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("research/runs/q099_q081r4_failure_diagnosis/result.json"),
    )
    args = parser.parse_args()

    receipt = diagnose(load_result(args.result))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Q099_STATUS:", receipt["status"])
    print("Q099_COMMON_FAILED_GATES:", len(receipt["common_failure_signature"]["gates_failed_by_all_arms"]))
    print("Q099_SHARED_WORST_ROLLING_WINDOW:", receipt["rolling_window_diagnosis"]["shared_worst_window_index"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
