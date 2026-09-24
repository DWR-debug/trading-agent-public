"""Deterministic, non-selective failure diagnosis for archived formal evidence.

This module derives diagnostics from a completed evidence record only. It never
re-runs a strategy, changes parameters, selects a candidate, or reads holdout
data for selection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EVIDENCE_PATH = (
    ROOT
    / "research"
    / "evidence"
    / "trial_040_network_momentum_repair_2026_09_24.json"
)

THRESHOLDS = {
    "research_return_min": 0.0,
    "research_max_drawdown_max": 0.10,
    "research_profit_factor_min": 1.10,
    "rolling_profit_factor_min": 1.10,
    "rolling_profitable_ratio_min": 0.50,
    "rolling_average_drawdown_max": 0.10,
    "holdout_return_min": 0.0,
    "holdout_profit_factor_min": 1.10,
    "holdout_max_drawdown_max": 0.10,
    "stress_holdout_return_min": 0.0,
}


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(
        _canonical(value).encode("utf-8")
    ).hexdigest()


def _gap(actual: float, threshold: float, direction: str) -> float:
    if direction == "higher":
        return threshold - actual
    return actual - threshold


def diagnose(evidence_path: str | Path = EVIDENCE_PATH) -> dict:
    path = Path(evidence_path)
    if not path.is_absolute():
        path = ROOT / path

    evidence = json.loads(path.read_text(encoding="utf-8"))
    if evidence.get("trial_id") != "T-2026-09-24-040":
        raise ValueError("Failure diagnosis is bound to T040 evidence.")
    if evidence.get("status") != "BLOCKED":
        raise ValueError(
            "Failure diagnosis requires the completed BLOCKED T040 evidence."
        )
    if evidence.get("scientific_outcome") != "NO_PROMOTION_EVIDENCE":
        raise ValueError(
            "Failure diagnosis requires NO_PROMOTION_EVIDENCE."
        )
    if evidence.get("safety", {}).get("paper_only") is not True:
        raise RuntimeError("Diagnostic path requires paper-only safety.")
    if evidence.get("safety", {}).get("live_trading_enabled") is not False:
        raise RuntimeError("Diagnostic path requires live trading disabled.")
    if evidence.get("safety", {}).get("automatic_promotion") is not False:
        raise RuntimeError("Diagnostic path requires automatic promotion disabled.")

    challenger = evidence["challenger"]
    control = evidence["fixed_sma_control"]

    gate_status = {
        "research": {
            "return": challenger["research_return"] > THRESHOLDS["research_return_min"],
            "max_drawdown": challenger["research_max_drawdown"] <= THRESHOLDS["research_max_drawdown_max"],
            "profit_factor": challenger["research_profit_factor"] >= THRESHOLDS["research_profit_factor_min"],
            "rolling_profit_factor": challenger["rolling_min_profit_factor"] >= THRESHOLDS["rolling_profit_factor_min"],
            "rolling_profitable_ratio": challenger["rolling_profitable_ratio"] >= THRESHOLDS["rolling_profitable_ratio_min"],
            "rolling_average_drawdown": challenger["rolling_average_drawdown"] <= THRESHOLDS["rolling_average_drawdown_max"],
        },
        "holdout": {
            "return": challenger["holdout_return"] > THRESHOLDS["holdout_return_min"],
            "profit_factor": challenger["holdout_profit_factor"] >= THRESHOLDS["holdout_profit_factor_min"],
            "max_drawdown": challenger["holdout_max_drawdown"] <= THRESHOLDS["holdout_max_drawdown_max"],
            "stress_1_5x_return": challenger["stress_1_5x_holdout_return"] >= THRESHOLDS["stress_holdout_return_min"],
            "stress_2x_return": challenger["stress_2x_holdout_return"] >= THRESHOLDS["stress_holdout_return_min"],
        },
    }

    baseline_delta = {
        "research_return_vs_control": (
            challenger["research_return"] - control["research_return"]
        ),
        "research_max_drawdown_vs_control": (
            challenger["research_max_drawdown"]
            - control["research_max_drawdown"]
        ),
        "research_profit_factor_vs_control": (
            challenger["research_profit_factor"]
            - control["research_profit_factor"]
        ),
        "holdout_return_vs_control": (
            challenger["holdout_return"]
            - control["holdout_return"]
        ),
        "holdout_max_drawdown_vs_control": (
            challenger["holdout_max_drawdown"]
            - control["holdout_max_drawdown"]
        ),
        "holdout_profit_factor_vs_control": (
            challenger["holdout_profit_factor"]
            - control["holdout_profit_factor"]
        ),
    }

    stress_delta = {
        "research_return_base_to_1_5x": (
            None
        ),
        "research_return_base_to_2x": (
            None
        ),
        "holdout_return_base_to_1_5x": (
            challenger["stress_1_5x_holdout_return"]
            - challenger["holdout_return"]
        ),
        "holdout_return_base_to_2x": (
            challenger["stress_2x_holdout_return"]
            - challenger["holdout_return"]
        ),
    }

    failed_gate_count = sum(
        not passed
        for category in gate_status.values()
        for passed in category.values()
    )

    diagnosis_class = (
        "broad_negative_with_control_deterioration"
        if (
            challenger["research_return"] < 0.0
            and challenger["holdout_return"] < 0.0
            and challenger["research_profit_factor"] < 1.0
            and challenger["holdout_profit_factor"] < 1.0
            and baseline_delta["research_return_vs_control"] < 0.0
            and baseline_delta["holdout_return_vs_control"] < 0.0
        )
        else "mixed_or_partial_failure"
    )

    report = {
        "schema_version": "1.0",
        "diagnosis_id": "T040-FAILURE-DIAGNOSIS-2026-09-24",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "evidence_path": str(path.relative_to(ROOT)),
            "trial_id": evidence["trial_id"],
            "report_fingerprint": evidence["report_fingerprint"],
        },
        "status": "DIAGNOSTIC_ONLY",
        "diagnosis_class": diagnosis_class,
        "failed_gate_count": failed_gate_count,
        "gate_status": gate_status,
        "baseline_delta": baseline_delta,
        "stress_delta": stress_delta,
        "key_observations": [
            "The challenger is negative on both research and holdout return.",
            "Both research and holdout profit factors are below 1.0.",
            "Research drawdown exceeds the 10% gate by a wide margin.",
            "All five research rolling windows are non-profitable.",
            "Cost stress further reduces holdout return.",
            "The challenger is worse than the fixed SMA control on research return, research drawdown, research profit factor, holdout return, and holdout profit factor.",
            "The result does not establish a universal statement about Cross-Asset Momentum; it diagnoses only this fixed T040 mechanism and dataset.",
        ],
        "non_actions": [
            "no_parameter_change",
            "no_lookback_search",
            "no_lag_search",
            "no_blend_search",
            "no_asset_reselection",
            "no_holdout_selection",
            "no_gate_relaxation",
            "no_production_promotion",
        ],
        "next_research_action": (
            "Do not tune T040. Move the queue to adversarial and orthogonal "
            "research questions using a new preregistration before any new "
            "performance experiment."
        ),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "paid_agent_api_budget_usd": 0.0,
        },
    }
    fingerprint_input = dict(report)
    fingerprint_input.pop("recorded_at", None)
    report["fingerprint"] = _fingerprint(fingerprint_input)
    return report


def write_report(
    evidence_path: str | Path = EVIDENCE_PATH,
    output_path: str | Path = "research/evidence/t040_failure_diagnosis_2026_09_24.json",
) -> dict:
    report = diagnose(evidence_path)
    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--evidence",
        default=str(EVIDENCE_PATH),
    )
    parser.add_argument(
        "--output",
        default="research/evidence/t040_failure_diagnosis_2026_09_24.json",
    )
    args = parser.parse_args()
    report = write_report(args.evidence, args.output)
    print("DIAGNOSIS_STATUS:", report["status"])
    print("DIAGNOSIS_CLASS:", report["diagnosis_class"])
    print("FAILED_GATES:", report["failed_gate_count"])
    print("DIAGNOSIS_FINGERPRINT:", report["fingerprint"])


if __name__ == "__main__":
    main()
