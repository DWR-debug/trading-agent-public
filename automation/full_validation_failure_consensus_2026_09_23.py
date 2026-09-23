"""Consensus control across the two fully independent full candidate validations.

Uses only immutable archived validation reports. No tuning or holdout selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_SHARED_FAILURES = {
    "research_drawdown",
    "rolling_profit_factor",
    "rolling_average_drawdown",
    "holdout_drawdown",
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


def _load_report(root: Path, relative_path: str) -> dict:
    path = root / relative_path
    report = json.loads(path.read_text(encoding="utf-8"))
    stored = report.pop("report_fingerprint")
    actual = _fingerprint(report)
    if stored != actual:
        raise ValueError(f"Report-Fingerprint ungültig: {path}")
    report["report_fingerprint"] = stored
    return report


def _base_snapshot(report: dict) -> dict:
    base = report["scenarios"]["base"]["vol_budget_10pct"]["price_only"]
    checks = report["gate_contract"]["checks"]
    failed = {name for name, passed in checks.items() if passed is False}

    return {
        "report_fingerprint": report["report_fingerprint"],
        "candidate_status": report["candidate_status"],
        "research": {
            "period_return": base["research"]["period_return"],
            "max_drawdown_percent": base["research"]["max_drawdown_percent"],
            "profit_factor": base["research"]["profit_factor"],
        },
        "holdout": {
            "period_return": base["holdout"]["period_return"],
            "max_drawdown_percent": base["holdout"]["max_drawdown_percent"],
            "profit_factor": base["holdout"]["profit_factor"],
        },
        "rolling": {
            "profitable_windows": base["rolling_summary"]["profitable_windows"],
            "window_count": base["rolling_summary"]["window_count"],
            "profitable_window_ratio": base["rolling_summary"]["profitable_window_ratio"],
            "overall_profit_factor": base["rolling_summary"]["overall_profit_factor"],
            "average_drawdown_percent": base["rolling_summary"]["average_drawdown_percent"],
        },
        "oos_to_is_return_ratio": base["oos_to_is_return_ratio"],
        "failed_gate_checks": sorted(failed),
    }


def run_control(
    second_root: Path,
    third_root: Path,
    output_path: Path,
) -> dict:
    second = _load_report(
        second_root,
        "research/independent_validation_2026_09_23/report.json",
    )
    third = _load_report(
        third_root,
        "research/third_independent_validation_2026_09_23/report.json",
    )

    for label, report in (("second_validation", second), ("third_validation", third)):
        if report["candidate_status"] != "BLOCKED":
            raise ValueError(f"{label}: Candidate ist nicht BLOCKED.")
        safety = report["safety"]
        if safety != {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        }:
            raise ValueError(f"{label}: Paper-only Sicherheitsvertrag verletzt.")

    second_snapshot = _base_snapshot(second)
    third_snapshot = _base_snapshot(third)
    second_failed = set(second_snapshot["failed_gate_checks"])
    third_failed = set(third_snapshot["failed_gate_checks"])
    shared_failures = sorted(second_failed & third_failed)
    union_failures = sorted(second_failed | third_failed)

    result = {
        "schema_version": 1,
        "diagnostic_type": "full_validation_failure_consensus_2026_09_23",
        "status": "COMPLETED",
        "validations": {
            "second_full_validation": second_snapshot,
            "third_full_validation": third_snapshot,
        },
        "consensus": {
            "shared_failed_gate_checks": shared_failures,
            "shared_failure_count": len(shared_failures),
            "expected_shared_risk_signature": sorted(EXPECTED_SHARED_FAILURES),
            "expected_shared_risk_signature_reproduced": (
                set(shared_failures) == EXPECTED_SHARED_FAILURES
            ),
            "failure_union": union_failures,
            "both_candidate_status_blocked": True,
            "both_holdout_returns_positive": (
                second_snapshot["holdout"]["period_return"] > 0.0
                and third_snapshot["holdout"]["period_return"] > 0.0
            ),
            "both_holdout_profit_factor_positive": (
                second_snapshot["holdout"]["profit_factor"] > 1.0
                and third_snapshot["holdout"]["profit_factor"] > 1.0
            ),
            "both_research_drawdown_above_threshold": (
                second_snapshot["research"]["max_drawdown_percent"] > 10.0
                and third_snapshot["research"]["max_drawdown_percent"] > 10.0
            ),
            "both_holdout_drawdown_above_threshold": (
                second_snapshot["holdout"]["max_drawdown_percent"] > 10.0
                and third_snapshot["holdout"]["max_drawdown_percent"] > 10.0
            ),
        },
        "interpretation": {
            "primary_finding": (
                "Über zwei vollständig disjunkte vollständige Candidate-Validierungen "
                "wiederholt sich derselbe vierteilige Risiko-/Robustheits-Failure-Fingerabdruck."
            ),
            "important_non_finding": (
                "Der Control zeigt keinen universellen Rendite-Failure: beide Holdouts "
                "sind positiv und die Holdout-PF-Werte liegen über 1.0."
            ),
            "research_consequence": (
                "Der nächste Schritt ist Ursachenanalyse der gemeinsamen Risiko-/Rolling-"
                "Instabilität, nicht Parameter-Tuning und nicht Lockerung der Gates."
            ),
        },
        "constraints": [
            "diagnostic only",
            "reports from immutable archived artifacts only",
            "holdout is observed only as a final validation result",
            "no parameter selection",
            "no asset replacement",
            "no signal change",
            "no sleeve-weight change",
            "no gate change",
            "no production change",
        ],
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    result["consensus_fingerprint"] = _fingerprint(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--second-root", required=True)
    parser.add_argument("--third-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run_control(
        Path(args.second_root),
        Path(args.third_root),
        Path(args.output),
    )
    print("FULL_VALIDATION_FAILURE_CONSENSUS_STATUS:", result["status"])
    print(
        "SHARED_FAILURES:",
        result["consensus"]["shared_failed_gate_checks"],
    )
    print(
        "SHARED_RISK_SIGNATURE_REPRODUCED:",
        result["consensus"]["expected_shared_risk_signature_reproduced"],
    )
    print("CONSENSUS_FINGERPRINT:", result["consensus_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
