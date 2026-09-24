"""Descriptive failure diagnosis for Trial 023 MAX-effect control.

No optimization, selection, gate changes, or new market-data research.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

TRIAL_ID = "T-2026-09-24-023"
REPORT_FINGERPRINT = "bfaeb216996b2f32acd55fff06e217344f24de6aca373a661bedd873c06bb594"


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def diagnose(snapshot_path: Path, output_path: Path) -> dict:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if snapshot.get("trial_id") != TRIAL_ID:
        raise ValueError("Unexpected trial ID.")
    if snapshot.get("report_fingerprint") != REPORT_FINGERPRINT:
        raise ValueError("Report fingerprint mismatch.")
    if snapshot.get("selection_used") or snapshot.get("parameter_search_used"):
        raise ValueError("Diagnostic input violates no-selection contract.")

    research = snapshot["research"]
    holdout = snapshot["holdout"]
    research_dd_gate = 10.0
    holdout_dd_gate = 10.0
    oos_gate = 0.25

    result = {
        "schema_version": 1,
        "diagnostic_id": "DIAG-2026-09-24-023-001",
        "trial_id": TRIAL_ID,
        "report_fingerprint": REPORT_FINGERPRINT,
        "selection_used": False,
        "parameter_search_used": False,
        "findings": {
            "research_drawdown_excess_over_gate_pp": research["drawdown_percent"] - research_dd_gate,
            "holdout_drawdown_excess_over_gate_pp": holdout["drawdown_percent"] - holdout_dd_gate,
            "oos_ratio_shortfall_vs_gate": oos_gate - holdout["oos_to_research_return_ratio"],
            "research_to_holdout_return_decay_pp": research["return_percent"] - holdout["return_percent"],
            "research_edge_bps_per_day": research["max_edge_daily"] * 10000.0,
            "holdout_edge_bps_per_day": holdout["max_edge_daily"] * 10000.0,
            "edge_change_holdout_minus_research_bps_per_day": (holdout["max_edge_daily"] - research["max_edge_daily"]) * 10000.0,
            "research_rolling_profitable_ratio": research["rolling_profitable_window_ratio"],
            "selection_month_count": snapshot["selection_month_count"],
            "base_total_turnover": snapshot["base_total_turnover"],
        },
        "interpretation": (
            "The pre-registered Low-MAX hypothesis shows a positive research edge but a negative holdout edge. "
            "Absolute drawdown remains above the project gate in both splits and OOS/Research return retention "
            "is below the gate. Cost stress remains positive, so the primary failure is not simply cost exhaustion. "
            "This is descriptive evidence only and does not attribute causality."
        ),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }

    result["derived_fingerprint"] = _fingerprint(result)
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
    print("MAX_EFFECT_FAILURE_DIAGNOSTIC_STATUS: COMPLETED")
    print("MAX_EFFECT_FAILURE_DIAGNOSTIC_SUMMARY:", json.dumps(report["findings"], sort_keys=True))
    print("MAX_EFFECT_FAILURE_DIAGNOSTIC_FINGERPRINT:", report["derived_fingerprint"])


if __name__ == "__main__":
    main()