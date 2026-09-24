"""Descriptive failure diagnosis for Trial 022 portfolio risk parity.

No optimization, selection, gate changes, or new market-data research.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPORT_FINGERPRINT = "feeb659b4c0ac59082e333200327e1b44407902c6f69e5fd72f75dd9c16c4313"
TRIAL_ID = "T-2026-09-24-022"
BASE_COST_RATE = 0.0015


def _canon(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _period(dynamic: dict, fixed: dict, *, cost_multiplier: float) -> dict:
    rate = BASE_COST_RATE * cost_multiplier
    return {
        "dynamic_return_percent": 100.0 * dynamic["period_return"],
        "fixed_50_50_return_percent": 100.0 * fixed["period_return"],
        "return_gap_percentage_points": 100.0 * (
            dynamic["period_return"] - fixed["period_return"]
        ),
        "dynamic_turnover": dynamic["turnover"],
        "fixed_turnover": fixed["turnover"],
        "additional_turnover": dynamic["turnover"] - fixed["turnover"],
        "mechanical_additional_cost_drag_percentage_points": (
            (dynamic["turnover"] - fixed["turnover"]) * rate * 100.0
        ),
        "residual_return_gap_after_additional_cost_percentage_points": (
            100.0 * (dynamic["period_return"] - fixed["period_return"])
            + (dynamic["turnover"] - fixed["turnover"]) * rate * 100.0
        ),
        "dynamic_drawdown_percent": dynamic["max_drawdown_percent"],
        "fixed_drawdown_percent": fixed["max_drawdown_percent"],
        "drawdown_delta_percentage_points": (
            dynamic["max_drawdown_percent"] - fixed["max_drawdown_percent"]
        ),
        "dynamic_profit_factor": dynamic["profit_factor"],
        "fixed_profit_factor": fixed["profit_factor"],
        "profit_factor_delta": float(dynamic["profit_factor"]) - float(fixed["profit_factor"]),
        "dynamic_average_trend_weight": dynamic["average_trend_weight"],
        "dynamic_average_cross_sectional_weight": dynamic["average_cross_sectional_weight"],
    }


def diagnose(snapshot_path: Path, output_path: Path) -> dict:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if snapshot["trial_id"] != TRIAL_ID:
        raise ValueError("Unexpected trial ID.")
    if snapshot["report_fingerprint"] != REPORT_FINGERPRINT:
        raise ValueError("Report fingerprint mismatch.")
    if snapshot["selection_used"] or snapshot["parameter_search_used"]:
        raise ValueError("Diagnostic input violates the no-selection contract.")

    scenarios = snapshot["scenarios"]
    result = {
        "schema_version": 1,
        "diagnostic_id": "DIAG-2026-09-24-022-001",
        "trial_id": TRIAL_ID,
        "report_fingerprint": REPORT_FINGERPRINT,
        "method": "mechanical transaction-cost decomposition plus descriptive relative-metric comparison",
        "selection_used": False,
        "parameter_search_used": False,
        "periods": {},
    }
    for scenario_name, multiplier in (("base", 1.0), ("stress_1_5x_cost", 1.5), ("stress_2x_cost", 2.0)):
        scenario = scenarios[scenario_name]
        result["periods"][scenario_name] = {
            "research": _period(
                scenario["dynamic_inverse_vol_63"]["research"],
                scenario["fixed_50_50"]["research"],
                cost_multiplier=multiplier,
            ),
            "holdout": _period(
                scenario["dynamic_inverse_vol_63"]["holdout"],
                scenario["fixed_50_50"]["holdout"],
                cost_multiplier=multiplier,
            ),
        }

    base_holdout = result["periods"]["base"]["holdout"]
    result["diagnostic_summary"] = {
        "holdout_drawdown_improvement_percentage_points": -base_holdout["drawdown_delta_percentage_points"],
        "holdout_return_shortfall_percentage_points": -base_holdout["return_gap_percentage_points"],
        "holdout_extra_turnover_percent_vs_fixed": (
            base_holdout["additional_turnover"] / base_holdout["fixed_turnover"] * 100.0
        ),
        "holdout_fraction_of_return_shortfall_explained_by_mechanical_extra_cost": (
            base_holdout["mechanical_additional_cost_drag_percentage_points"]
            / -base_holdout["return_gap_percentage_points"]
        ),
        "average_holdout_trend_overweight_percentage_points_vs_50_50": (
            (base_holdout["dynamic_average_trend_weight"] - 0.5) * 100.0
        ),
        "average_holdout_cross_sectional_underweight_percentage_points_vs_50_50": (
            (base_holdout["dynamic_average_cross_sectional_weight"] - 0.5) * 100.0
        ),
        "interpretation": (
            "Dynamic allocation reduced holdout drawdown modestly but also reduced "
            "return and profit factor. The mechanical extra-turnover cost explains "
            "only part of the return gap; the remainder is a residual from different "
            "sleeve exposure over the sample and is not treated as causal evidence."
        ),
    }
    result["derived_fingerprint"] = _fp(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = diagnose(Path(args.snapshot), Path(args.output))
    print("PORTFOLIO_RISK_PARITY_DIAGNOSTIC_STATUS: COMPLETED")
    print("PORTFOLIO_RISK_PARITY_DIAGNOSTIC_SUMMARY:", json.dumps(report["diagnostic_summary"], sort_keys=True))
    print("PORTFOLIO_RISK_PARITY_DIAGNOSTIC_FINGERPRINT:", report["derived_fingerprint"])


if __name__ == "__main__":
    main()
