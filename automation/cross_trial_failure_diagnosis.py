"""Cross-trial diagnostic synthesis from immutable ledger evidence.

This module is descriptive only. It consumes a fixed list of historical trials,
does not select assets/parameters from outcomes, does not touch holdouts for
selection, and creates no promotion decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "research" / "evidence" / "trial_ledger.json"

TRIAL_IDS = (
    "T-2026-09-24-022",
    "T-2026-09-24-023",
    "T-2026-09-24-025",
    "T-2026-09-24-027",
    "T-2026-09-24-028",
)

THRESHOLDS = {
    "research_drawdown_percent": 10.0,
    "research_profit_factor": 1.10,
    "oos_to_is_ratio": 0.25,
    "holdout_drawdown_percent": 10.0,
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


def _metric(source: dict, *names: str):
    for name in names:
        if name in source:
            return source[name]
    return None


def _failure_modes(trial: dict) -> list[str]:
    outcome = trial.get("outcome", {})
    gates = outcome.get("gate_results", {})
    modes = []

    if (
        gates.get("research_drawdown") is False
        or gates.get("research_max_drawdown_lte_10pct") is False
    ):
        modes.append("research_risk_gate")

    if (
        gates.get("research_profit_factor") is False
        or gates.get("research_profit_factor_gte_1_10") is False
    ):
        modes.append("research_profit_factor_gate")

    if (
        gates.get("oos_to_is_return_ratio") is False
        or gates.get("oos_to_research_return_ratio_gte_25pct") is False
    ):
        modes.append("oos_stability_gate")

    if (
        gates.get("holdout_drawdown") is False
        or gates.get("holdout_max_drawdown_lte_10pct") is False
    ):
        modes.append("holdout_risk_gate")

    if any(
        key.endswith("_edge_positive")
        and value is False
        for key, value in gates.items()
    ):
        modes.append("mechanism_edge_gate")

    if any(
        key.startswith("research_") and key.endswith("_not_below_fixed")
        and value is False
        for key, value in gates.items()
    ) or any(
        key.startswith("holdout_") and key.endswith("_not_below_fixed")
        and value is False
        for key, value in gates.items()
    ):
        modes.append("control_relative_non_deterioration")

    return sorted(set(modes))


def _trial_summary(trial: dict) -> dict:
    outcome = trial.get("outcome", {})
    key = outcome.get("key_metrics", {})
    base = outcome.get("base", {})
    deltas = outcome.get("deltas_vs_fixed", {})

    summary = {
        "trial_id": trial["trial_id"],
        "research_family": trial["research_family"],
        "status": trial["status"],
        "failure_modes": _failure_modes(trial),
        "holdout_used_for_selection": (
            trial.get("data_scope", {}).get("holdout_used_for_selection")
        ),
        "parameter_search": trial.get("search_scope", {}).get("parameter_search"),
        "variant_search": trial.get("search_scope", {}).get("variant_search"),
        "key_metrics": {},
    }

    if key:
        summary["key_metrics"].update(key)
    if base:
        summary["key_metrics"].update({
            k: v
            for k, v in base.items()
            if k in {
                "research_return_percent",
                "research_max_drawdown_percent",
                "research_profit_factor",
                "holdout_return_percent",
                "holdout_max_drawdown_percent",
                "holdout_profit_factor",
                "oos_to_research_return_ratio",
                "research_mean_low_residual_vol_edge",
                "holdout_mean_low_residual_vol_edge",
            }
        })
    if deltas:
        summary["control_deltas"] = deltas

    return summary


def diagnose(ledger_path: str | Path = LEDGER_PATH) -> dict:
    path = Path(ledger_path)
    if not path.is_absolute():
        path = ROOT / path

    ledger = json.loads(path.read_text(encoding="utf-8"))
    trials_by_id = {
        trial["trial_id"]: trial
        for trial in ledger["trials"]
    }

    selected = []
    for trial_id in TRIAL_IDS:
        if trial_id not in trials_by_id:
            raise ValueError(f"Required trial missing from ledger: {trial_id}")
        trial = trials_by_id[trial_id]
        if trial.get("status") not in {"archived_rejected", "archived_diagnostic"}:
            raise ValueError(
                f"Historical diagnosis requires an archived trial: {trial_id}"
            )
        selected.append(_trial_summary(trial))

    t028 = trials_by_id["T-2026-09-24-028"]
    t028_outcome = t028.get("outcome", {})
    t028_delta = t028_outcome.get("deltas_vs_fixed", {})

    salvageable_t028 = (
        t028_delta.get("research_drawdown_delta_percentage_points", 0.0) < 0.0
        and t028_delta.get("research_profit_factor_delta", 0.0) > 0.0
        and t028_delta.get("holdout_drawdown_delta_percentage_points", 0.0) < 0.0
        and t028_delta.get("holdout_profit_factor_delta", 0.0) > 0.0
    )

    result = {
        "schema_version": "1.0",
        "diagnosis_id": "CROSS-TRIAL-FAILURE-DIAGNOSIS-2026-09-24",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "ledger": str(path.relative_to(ROOT)),
            "trial_ids": list(TRIAL_IDS),
        },
        "status": "DIAGNOSTIC_ONLY",
        "trial_summaries": selected,
        "cross_trial_patterns": [
            {
                "pattern_id": "P1",
                "name": "risk_gate_recurrence",
                "description": (
                    "Research drawdown or comparable risk gates remain a recurring "
                    "failure mode even when absolute return/profit-factor metrics look attractive."
                ),
                "evidence_trials": [
                    "T-2026-09-24-022",
                    "T-2026-09-24-023",
                    "T-2026-09-24-025",
                    "T-2026-09-24-027",
                    "T-2026-09-24-028",
                ],
            },
            {
                "pattern_id": "P2",
                "name": "mechanism_edge_can_fail_behind_good_aggregate_returns",
                "description": (
                    "T023/T025 show that high aggregate returns can coexist with a "
                    "failed mechanism-specific edge or insufficient OOS stability."
                ),
                "evidence_trials": [
                    "T-2026-09-24-023",
                    "T-2026-09-24-025",
                ],
            },
            {
                "pattern_id": "P3",
                "name": "holdout_is_not_a_rescue",
                "description": (
                    "Positive or comparatively attractive holdout metrics do not compensate "
                    "for earlier research, rolling, OOS, risk, or mechanism gates."
                ),
                "evidence_trials": [
                    "T-2026-09-24-022",
                    "T-2026-09-24-023",
                    "T-2026-09-24-025",
                    "T-2026-09-24-027",
                    "T-2026-09-24-028",
                ],
            },
            {
                "pattern_id": "P4",
                "name": "risk_control_can_be_useful_without_alpha_proof",
                "description": (
                    "T028 contains a control-relative risk observation: research and holdout "
                    "drawdown improved while profit factor improved slightly, but hard research "
                    "risk/PF gates still failed."
                ),
                "evidence_trials": [
                    "T-2026-09-24-028",
                ],
            },
        ],
        "salvageable_observations": {
            "t028_per_sleeve_volatility_budget": salvageable_t028,
            "interpretation": (
                "Risk-control hypothesis only; not an alpha/promotion candidate."
                if salvageable_t028
                else "Does not meet the fixed diagnostic conditions."
            ),
        },
        "non_actions": [
            "no_parameter_reselection",
            "no_asset_reselection",
            "no_holdout_selection",
            "no_gate_relaxation",
            "no_backtest_rerun",
            "no_production_promotion",
        ],
        "next_research_question": (
            "Before another return-generating strategy family is promoted, test a "
            "new, fully pre-registered risk-control/allocation hypothesis on a fresh "
            "symbol-disjoint universe, using T028 only as motivation and not as a "
            "selection mechanism."
        ),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "paid_agent_api_budget_usd": 0.0,
        },
    }

    fingerprint_input = dict(result)
    fingerprint_input.pop("recorded_at", None)
    result["fingerprint"] = _fingerprint(fingerprint_input)
    return result


CURRENT_TRIAL_IDS = (
    "T-2026-09-24-041",
    "T-2026-09-24-042",
    "T-2026-09-25-043",
    "T-2026-09-25-044",
    "T-2026-09-25-045",
)


def _current_metric(outcome: dict, *names: str):
    key = outcome.get("key_metrics", {})
    for name in names:
        if name in key:
            return key[name]
        if name in outcome:
            return outcome[name]
    return None


def _current_failure_modes(trial: dict) -> list[str]:
    outcome = trial.get("outcome", {})
    if trial.get("status") == "data_invalid":
        return ["data_validity_failure"]

    modes: set[str] = set()
    failed_absolute = outcome.get("failed_absolute", [])
    failed_absolute += outcome.get("gate_results", {}).get("failed_absolute", [])
    failed_non_deterioration = outcome.get("failed_non_deterioration", [])
    failed_non_deterioration += outcome.get("gate_results", {}).get(
        "failed_non_deterioration", []
    )

    research_dd = _current_metric(
        outcome,
        "research_drawdown_percent",
        "base_research_drawdown_percent",
        "fixed_research_drawdown_percent",
    )
    research_pf = _current_metric(
        outcome,
        "research_profit_factor",
        "base_research_profit_factor",
        "fixed_research_profit_factor",
    )
    oos_ratio = _current_metric(
        outcome,
        "oos_to_is_return_ratio",
        "base_oos_to_is_return_ratio",
        "fixed_oos_to_is_return_ratio",
    )
    holdout_dd = _current_metric(
        outcome,
        "holdout_drawdown_percent",
        "base_holdout_drawdown_percent",
        "fixed_holdout_drawdown_percent",
    )

    if research_dd is not None and research_dd > THRESHOLDS["research_drawdown_percent"]:
        modes.add("research_risk_gate")
    if any("research_drawdown" in str(item) for item in failed_absolute):
        modes.add("research_risk_gate")
    if research_pf is not None and research_pf < THRESHOLDS["research_profit_factor"]:
        modes.add("research_profit_factor_gate")
    if any("research_profit_factor" in str(item) for item in failed_absolute):
        modes.add("research_profit_factor_gate")
    if oos_ratio is not None and oos_ratio < THRESHOLDS["oos_to_is_ratio"]:
        modes.add("oos_stability_gate")
    if any("oos_to_is" in str(item) for item in failed_absolute):
        modes.add("oos_stability_gate")
    if holdout_dd is not None and holdout_dd > THRESHOLDS["holdout_drawdown_percent"]:
        modes.add("holdout_risk_gate")
    if any("holdout_drawdown" in str(item) for item in failed_absolute):
        modes.add("holdout_risk_gate")
    if failed_non_deterioration or outcome.get("non_deterioration_gates_passed") is False:
        modes.add("control_relative_non_deterioration")
    if not modes and outcome.get("all_checks_passed") is False:
        modes.add("gate_failure_unspecified")
    return sorted(modes)


def diagnose_current(ledger_path: str | Path = LEDGER_PATH) -> dict:
    path = Path(ledger_path)
    if not path.is_absolute():
        path = ROOT / path

    ledger = json.loads(path.read_text(encoding="utf-8"))
    trials_by_id = {trial["trial_id"]: trial for trial in ledger["trials"]}
    selected = []
    for trial_id in CURRENT_TRIAL_IDS:
        if trial_id not in trials_by_id:
            raise ValueError(f"Required current trial missing from ledger: {trial_id}")
        trial = trials_by_id[trial_id]
        if trial.get("status") not in {"archived_rejected", "data_invalid"}:
            raise ValueError(
                f"Current diagnosis requires archived/data-invalid trial: {trial_id}"
            )
        selected.append(
            {
                "trial_id": trial_id,
                "research_family": trial["research_family"],
                "status": trial["status"],
                "failure_modes": _current_failure_modes(trial),
                "holdout_used_for_selection": trial.get("data_scope", {}).get(
                    "holdout_used_for_selection"
                ),
                "parameter_search": trial.get("search_scope", {}).get("parameter_search"),
                "variant_search": trial.get("search_scope", {}).get("variant_search"),
            }
        )

    def evidence_for(mode: str) -> list[str]:
        return [
            item["trial_id"]
            for item in selected
            if mode in item["failure_modes"]
        ]

    patterns = {
        "risk_gate_recurrence": evidence_for("research_risk_gate")
        + [
            trial_id
            for trial_id in evidence_for("holdout_risk_gate")
            if trial_id not in evidence_for("research_risk_gate")
        ],
        "oos_stability_recurrence": evidence_for("oos_stability_gate"),
        "control_relative_non_deterioration_recurrence": evidence_for(
            "control_relative_non_deterioration"
        ),
        "data_validity_failure": evidence_for("data_validity_failure"),
        "gate_failure_unspecified": evidence_for("gate_failure_unspecified"),
    }

    return {
        "schema_version": "1.0",
        "diagnosis_id": "CROSS-TRIAL-FAILURE-DIAGNOSIS-2026-09-25",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "ledger": str(path.relative_to(ROOT)),
            "trial_ids": list(CURRENT_TRIAL_IDS),
        },
        "status": "DIAGNOSTIC_ONLY",
        "trial_summaries": selected,
        "cross_trial_patterns_by_id": patterns,
        "interpretation": {
            "risk_gate_recurrence_count": len(patterns["risk_gate_recurrence"]),
            "oos_stability_recurrence_count": len(patterns["oos_stability_recurrence"]),
            "control_relative_non_deterioration_count": len(
                patterns["control_relative_non_deterioration_recurrence"]
            ),
            "data_validity_failure_count": len(patterns["data_validity_failure"]),
            "key_observation": (
                "T044 and T045 each show a limited relative risk improvement in one "
                "rolling/research dimension, while absolute and holdout risk quality "
                "remain unresolved; recurring OOS/control-relative failures therefore "
                "remain the dominant diagnostic constraint."
            ),
        },
        "non_actions": [
            "no_parameter_reselection",
            "no_asset_reselection",
            "no_holdout_selection",
            "no_gate_relaxation",
            "no_backtest_rerun",
            "no_production_promotion",
        ],
        "next_research_question": (
            "Before reserving another performance trial, use the fixed failure taxonomy "
            "to define one orthogonal mechanism aimed at the recurring risk/OOS constraint, "
            "then preregister it without using these outcomes for parameter or asset selection."
        ),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "paid_agent_api_budget_usd": 0.0,
        },
    }


def write_current_report(
    ledger_path: str | Path = LEDGER_PATH,
    output_path: str | Path = (
        "research/evidence/cross_trial_failure_diagnosis_2026_09_25.json"
    ),
) -> dict:
    result = diagnose_current(ledger_path)
    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    fingerprint_input = dict(result)
    fingerprint_input.pop("recorded_at", None)
    result["fingerprint"] = _fingerprint(fingerprint_input)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result

def write_report(
    ledger_path: str | Path = LEDGER_PATH,
    output_path: str | Path = (
        "research/evidence/cross_trial_failure_diagnosis_2026_09_24.json"
    ),
) -> dict:
    result = diagnose(ledger_path)
    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(LEDGER_PATH))
    parser.add_argument(
        "--output",
        default="research/evidence/cross_trial_failure_diagnosis_2026_09_24.json",
    )
    args = parser.parse_args()
    result = write_report(args.ledger, args.output)
    print("DIAGNOSIS_STATUS:", result["status"])
    print("T028_SALVAGEABLE_RISK_CONTROL:", result["salvageable_observations"]["t028_per_sleeve_volatility_budget"])
    print("DIAGNOSIS_FINGERPRINT:", result["fingerprint"])


if __name__ == "__main__":
    main()
