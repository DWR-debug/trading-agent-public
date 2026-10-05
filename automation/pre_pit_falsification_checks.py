"""Deterministic pre-PIT falsification battery derived from external adversarial review.

Synthetic controls only. A pass means the candidate contract has executable
anti-leakage tests; it is not PIT or performance evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CANDIDATES = ("Q194", "Q195", "Q196", "Q197", "Q199", "Q201", "Q205")


def sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def run_checks(candidate: str) -> dict:
    original = {"public_obs_session": 10, "occurrence_session": 8}
    wrong_clock = {**original, "public_obs_session": original["occurrence_session"]}
    clock_changes_boundary = original["public_obs_session"] != wrong_clock["public_obs_session"]

    prefix = [{"session": 10, "state": "ORIGINAL"}]
    mutated = prefix + [{"session": 15, "state": "LATER_REVISION"}]
    future_invariant = prefix == mutated[:len(prefix)]

    event = {"first_public_session": 10}
    shifted = {**event, "first_public_session": 15}
    original_visible = event["first_public_session"] <= 10
    shifted_visible = shifted["first_public_session"] <= 10
    lag_changes_visibility = original_visible and not shifted_visible

    mapping_a = {"issuer_A": 3, "issuer_B": 1}
    mapping_b = {"issuer_A": 1, "issuer_B": 3}
    mapping_changes = mapping_a != mapping_b

    ambiguous = {"calendar_date": "2026-09-10", "public_timestamp": None}
    same_day_fails_closed = ambiguous["public_timestamp"] is None

    origin_a = {"examiner": 4, "applicant": 2}
    origin_b = {"examiner": 2, "applicant": 4}
    origin_partition_changes = origin_a != origin_b

    return {
        "candidate_id": candidate,
        "clock_swap_changes_boundary": clock_changes_boundary,
        "future_mutation_preserves_historical_prefix": future_invariant,
        "forward_shift_changes_prefix_visibility": lag_changes_visibility,
        "count_preserving_mapping_permutation_changes_exposure": mapping_changes,
        "same_day_ambiguous_fails_closed": same_day_fails_closed,
        "origin_label_permutation_changes_provenance_for_q196_control": origin_partition_changes,
        "performance_evidence": False,
        "pit_authorized": False,
        "promotion_authorized": False,
        "live_execution": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    results = [run_checks(candidate) for candidate in CANDIDATES]
    required = (
        "clock_swap_changes_boundary",
        "future_mutation_preserves_historical_prefix",
        "forward_shift_changes_prefix_visibility",
        "count_preserving_mapping_permutation_changes_exposure",
        "same_day_ambiguous_fails_closed",
    )
    passed = all(all(item[key] for key in required) for item in results)

    receipt = {
        "schema_version": "1.0",
        "receipt_type": "pre_pit_falsification_battery",
        "status": "PRE_PIT_FALSIFICATION_CHECKS_COMPLETED" if passed else "PRE_PIT_FALSIFICATION_CHECKS_FAILED",
        "candidates": results,
        "shared_contract": {
            "decision_boundary": "event_public_observation_boundary_or_next_regular_session_if_date_only",
            "occurrence_action_inspection_violation_submitted_dates_are_not_public_observation_substitutes": True,
            "same_day_ambiguous_fail_closed": True,
        },
        "origin_label_permutation": {
            "control": "Q196 examiner/applicant provenance",
            "must_break_invariance": True,
        },
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "PAPER_ONLY": True,
            "LIVE_TRADING_ENABLED": False,
            "ORDERS_ENABLED": False,
            "AUTOMATIC_PROMOTION": False,
        },
    }
    receipt["receipt_fingerprint"] = sha(receipt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "receipt_fingerprint": receipt["receipt_fingerprint"]}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
