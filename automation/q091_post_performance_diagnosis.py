"""Deterministic post-performance diagnosis for Q091.

This module consumes only the immutable Q091 performance result. It does not
search, rank, tune, select, promote, or create new performance evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TRIAL_ID = "T-2026-09-29-091"
RESULT_PATH = "research/evidence/q091_performance_result.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def diagnose(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("trial_id") != TRIAL_ID:
        raise ValueError("Unexpected Q091 trial id")
    if result.get("status") != "COMPLETED":
        raise ValueError("Q091 result is not completed")
    if result.get("performance_evaluation") is not True or result.get("holdout_evaluation") is not True:
        raise ValueError("Q091 result does not contain the required completed evaluations")
    if result.get("selection_used") is not False or result.get("holdout_used_for_selection") is not False:
        raise ValueError("Q091 result is not eligible for non-selective diagnosis")
    if result.get("promotion") is not False:
        raise ValueError("Q091 promotion state is invalid")

    arms = result["arms"]
    out_arms: dict[str, Any] = {}
    for name, arm in arms.items():
        base = arm["base"]
        research = base["research"]
        holdout = base["holdout"]
        gates = base["gates"]
        failures = [gate for gate, passed in gates.items() if not passed]
        rolling = base["rolling_windows"]
        rolling_positive = sum(w["period_return"] > 0.0 for w in rolling)

        stress15 = arm["stress_1_5x_cost"]
        stress2 = arm["stress_2x_cost"]
        sensitivity = arm["total_return_sensitivity"]

        out_arms[name] = {
            "research_to_holdout_transition": {
                "research_return": research["period_return"],
                "holdout_return": holdout["period_return"],
                "absolute_return_change": holdout["period_return"] - research["period_return"],
                "oos_to_is_return_ratio": base["oos_to_is_return_ratio"],
                "research_max_drawdown_percent": research["max_drawdown_percent"],
                "holdout_max_drawdown_percent": holdout["max_drawdown_percent"],
                "holdout_profit_factor": holdout["profit_factor"],
            },
            "rolling_stability": {
                "positive_window_count": rolling_positive,
                "window_count": len(rolling),
                "positive_window_ratio": base["rolling_profitable_window_ratio"],
                "rolling_average_drawdown_percent": base["rolling_average_drawdown_percent"],
                "rolling_profit_factor": base["rolling_profit_factor"],
            },
            "cost_and_turnover": {
                "mean_turnover": arm["turnover"]["mean"],
                "sum_turnover": arm["turnover"]["sum"],
                "holdout_return_base": holdout["period_return"],
                "holdout_return_stress_1_5x": stress15["holdout"]["period_return"],
                "holdout_return_stress_2x": stress2["holdout"]["period_return"],
                "holdout_return_total_return_sensitivity": sensitivity["holdout"]["period_return"],
            },
            "gate_failures": failures,
            "gates_passed": arm["gates_passed"],
            "gates_total": arm["gates_total"],
            "all_gates_passed": arm["all_gates_passed"],
        }

    names = list(out_arms)
    comparative: dict[str, Any] = {}
    if len(names) == 2:
        a, b = names
        comparative = {
            "two_arm_diagnostic_only": True,
            "mean_turnover_ratio_b_over_a": (
                out_arms[b]["cost_and_turnover"]["mean_turnover"]
                / out_arms[a]["cost_and_turnover"]["mean_turnover"]
                if out_arms[a]["cost_and_turnover"]["mean_turnover"] else None
            ),
            "interpretation_flags": {
                "a_research_positive_b_research_negative": (
                    out_arms[a]["research_to_holdout_transition"]["research_return"] > 0
                    and out_arms[b]["research_to_holdout_transition"]["research_return"] < 0
                ),
                "a_holdout_nonpositive": (
                    out_arms[a]["research_to_holdout_transition"]["holdout_return"] <= 0
                ),
                "b_holdout_negative": (
                    out_arms[b]["research_to_holdout_transition"]["holdout_return"] < 0
                ),
                "b_has_zero_positive_rolling_windows": (
                    out_arms[b]["rolling_stability"]["positive_window_count"] == 0
                ),
                "a_has_all_positive_rolling_windows": (
                    out_arms[a]["rolling_stability"]["positive_window_count"]
                    == out_arms[a]["rolling_stability"]["window_count"]
                ),
            },
        }

    return {
        "schema_version": "1.0",
        "trial_id": TRIAL_ID,
        "diagnosis_type": "post_performance_failure_diagnosis",
        "scientific_status": "descriptive_only_no_selection_or_promotion",
        "input_report_fingerprint": result.get("report_fingerprint"),
        "method": {
            "uses_only_persisted_q091_result": True,
            "uses_holdout_for_selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "asset_search": False,
            "horizon_search": False,
            "variant_search": False,
            "family_ranking": False,
            "promotion_decision": False,
            "creates_new_performance_evidence": False,
        },
        "arms": out_arms,
        "comparative_diagnostics": comparative,
        "next_diagnostic_questions": [
            "Decompose research-vs-holdout return loss by parent Q069 sleeve on the same frozen data.",
            "Measure common-mode versus idiosyncratic exposure through time without changing the Q091 rules.",
            "Attribute drawdown concentration and stress sensitivity to market phases and turnover/cost drag.",
            "Run any new validation only after these causes are isolated and preregistered.",
        ],
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("research/runs/q092_q091_failure_diagnosis.json"))
    args = parser.parse_args()

    result = _load(args.repo_root / RESULT_PATH)
    diagnosis = diagnose(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(diagnosis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q092_POST_PERFORMANCE_DIAGNOSIS_OK")
    print("INPUT_REPORT_FINGERPRINT:", diagnosis["input_report_fingerprint"])
    print("OUTPUT:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
