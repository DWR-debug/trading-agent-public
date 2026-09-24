"""Pre-declared deterministic capital-income stress matrix.

Research only. The return paths are scenario controls, not forecasts and not
representations of any live strategy. No optimization or policy selection occurs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from portfolio.income_stress import CapitalIncomePolicy, simulate_capital_withdrawals, sequence_sensitivity

SCENARIOS = {
    "flat": (0.0,) * 252,
    "steady_growth": (0.0004,) * 252,
    "volatile_growth": tuple([0.006, -0.0055] * 126),
    "early_drawdown": (-0.005,) * 42 + (0.0015,) * 210,
    "late_drawdown": (0.0015,) * 210 + (-0.005,) * 42,
    "whipsaw": tuple([0.004, -0.004] * 126),
}

POLICIES = {
    "full_payout": CapitalIncomePolicy(
        payout_fraction=1.0,
        capitalization_fraction=0.0,
        reserve_eur=0.0,
        payout_interval_periods=21,
    ),
    "balanced_capitalization": CapitalIncomePolicy(
        payout_fraction=0.50,
        capitalization_fraction=0.25,
        reserve_eur=0.0,
        payout_interval_periods=21,
    ),
    "protected_income": CapitalIncomePolicy(
        payout_fraction=0.50,
        capitalization_fraction=0.0,
        reserve_eur=25.0,
        payout_interval_periods=21,
    ),
}


def fingerprint(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run(output: Path) -> dict:
    results: dict[str, dict[str, object]] = {}
    for scenario_name, returns in SCENARIOS.items():
        scenario_result: dict[str, object] = {}
        for policy_name, policy in POLICIES.items():
            result = simulate_capital_withdrawals(returns, policy)
            sensitivity = sequence_sensitivity(returns, policy)
            scenario_result[policy_name] = {
                "final_equity_eur": result.final_equity_eur,
                "total_payout_eur": result.total_payout_eur,
                "total_capitalized_eur": result.total_capitalized_eur,
                "payout_count": result.payout_count,
                "capitalization_count": result.capitalization_count,
                "ending_protected_capital_eur": result.ending_protected_capital_eur,
                "minimum_equity_eur": result.minimum_equity_eur,
                "maximum_drawdown_percent": result.maximum_drawdown_percent,
                "reversed_sequence_total_payout_eur": sensitivity.reversed.total_payout_eur,
                "sequence_payout_difference_eur": sensitivity.payout_difference_eur,
                "reversed_sequence_final_equity_eur": sensitivity.reversed.final_equity_eur,
                "sequence_final_equity_difference_eur": sensitivity.final_equity_difference_eur,
            }
        results[scenario_name] = scenario_result

    report = {
        "schema_version": 1,
        "study_id": "CAPITAL-INCOME-STRESS-2026-09-24",
        "status": "COMPLETED",
        "design": {
            "scenario_count": len(SCENARIOS),
            "policy_count": len(POLICIES),
            "periods_per_scenario": 252,
            "period_definition": "synthetic daily return control",
            "optimization_used": False,
            "selection_used": False,
            "forecasts_used": False,
        },
        "scenarios": {
            name: {
                "period_count": len(returns),
                "description": {
                    "flat": "0% every period",
                    "steady_growth": "+0.04% every period",
                    "volatile_growth": "alternating +0.60% / -0.55%",
                    "early_drawdown": "-0.50% for 42 periods, then +0.15% for 210",
                    "late_drawdown": "+0.15% for 210 periods, then -0.50% for 42",
                    "whipsaw": "alternating +0.40% / -0.40%",
                }[name],
            }
            for name, returns in SCENARIOS.items()
        },
        "policies": {
            name: {
                "protected_capital_eur": policy.protected_capital_eur,
                "reserve_eur": policy.reserve_eur,
                "payout_fraction": policy.payout_fraction,
                "capitalization_fraction": policy.capitalization_fraction,
                "payout_interval_periods": policy.payout_interval_periods,
            }
            for name, policy in POLICIES.items()
        },
        "results": results,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    report["report_fingerprint"] = fingerprint(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run(Path(args.output))
    print("CAPITAL_INCOME_STRESS_STATUS:", report["status"])
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])
    for scenario, policies in report["results"].items():
        for policy, result in policies.items():
            print(
                scenario,
                policy,
                "TOTAL_PAYOUT=", result["total_payout_eur"],
                "FINAL_EQUITY=", result["final_equity_eur"],
                "MAX_DD=", result["maximum_drawdown_percent"],
                "SEQ_PAYOUT_DIFF=", result["sequence_payout_difference_eur"],
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
