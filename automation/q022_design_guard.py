"""Deterministic governance guard for the Q022 design-only research contract.

This check validates the frozen design metadata only. It performs no data
collection, performance calculation, holdout access, ranking, selection, or
promotion.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
Q022_PATH = ROOT / "research" / "preregistrations" / "q022_treasury_failure_followup_design_2026_09_26.json"
QUEUE_PATH = ROOT / "research" / "research_queue.json"
LEDGER_PATH = ROOT / "research" / "evidence" / "trial_ledger.json"

EXPECTED_IDS = ["H1", "H2", "H3", "H4", "H5", "H6"]
EXPECTED_FALSE = (
    "selection_used",
    "performance_trial_authorized",
    "holdout_used_for_selection",
    "q020_retuning",
    "gate_changes",
    "live_execution",
)
EXPECTED_PROTOCOL_FALSE = (
    "parameter_search",
    "asset_search",
    "threshold_search",
    "variant_search",
    "horizon_search",
)
EXPECTED_SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


class Q022DesignGuardError(ValueError):
    """Raised when the Q022 design contract drifts."""


def _canonical(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def design_fingerprint(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def validate_q022_design(
    payload: dict[str, Any],
    queue_payload: dict[str, Any],
    ledger_payload: dict[str, Any],
) -> str:
    if payload.get("task_id") != "Q-022-TREASURY-FAILURE-FOLLOWUP-DESIGN":
        raise Q022DesignGuardError("Unexpected Q022 task_id.")
    if payload.get("status") != "DESIGN_ONLY":
        raise Q022DesignGuardError("Q022 must remain DESIGN_ONLY.")
    if payload.get("ranked") is not False:
        raise Q022DesignGuardError("Q022 candidates must remain unranked.")
    for field in EXPECTED_FALSE:
        if payload.get(field) is not False:
            raise Q022DesignGuardError(f"Q022 field must remain false: {field}")

    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or [item.get("id") for item in candidates] != EXPECTED_IDS:
        raise Q022DesignGuardError("Q022 candidate catalog drifted.")
    if any(item.get("status") != "UNRANKED" for item in candidates):
        raise Q022DesignGuardError("Q022 candidate status drifted.")
    if any("name" not in item or "study_type" not in item for item in candidates):
        raise Q022DesignGuardError("Q022 candidate metadata is incomplete.")

    protocol = payload.get("common_protocol") or {}
    if protocol.get("fresh_symbol_disjoint_validation") is not True:
        raise Q022DesignGuardError("Fresh symbol-disjoint validation is required.")
    if protocol.get("preregistration_required") is not True:
        raise Q022DesignGuardError("Preregistration must remain required.")
    if protocol.get("coverage_first") is not True:
        raise Q022DesignGuardError("Coverage-first must remain required.")
    if protocol.get("point_in_time_required") is not True:
        raise Q022DesignGuardError("Point-in-time validation must remain required.")
    if protocol.get("holdout_blind") is not True:
        raise Q022DesignGuardError("Holdout must remain blind.")
    for field in EXPECTED_PROTOCOL_FALSE:
        if protocol.get(field) is not False:
            raise Q022DesignGuardError(f"Protocol field must remain false: {field}")

    if payload.get("safety") != EXPECTED_SAFETY:
        raise Q022DesignGuardError("Q022 safety invariants drifted.")

    queue_tasks = queue_payload.get("tasks") or []
    q022_queue = next((item for item in queue_tasks if item.get("task_id") == payload["task_id"]), None)
    q021_queue = next((item for item in queue_tasks if item.get("task_id") == payload["parent_diagnosis"]), None)
    if q022_queue is None or q022_queue.get("status") != "PENDING":
        raise Q022DesignGuardError("Q022 queue status is not PENDING.")
    if q021_queue is None or q021_queue.get("status") != "COMPLETED":
        raise Q022DesignGuardError("Q021 parent task is not COMPLETED.")

    entries = ledger_payload if isinstance(ledger_payload, list) else ledger_payload.get("trials", [])
    source = next((item for item in entries if item.get("trial_id") == payload["source_trial"]), None)
    if source is None:
        raise Q022DesignGuardError("Q022 source trial is missing from the ledger.")
    if source.get("status") != "archived_rejected":
        raise Q022DesignGuardError("Q022 source trial must remain archived_rejected.")
    outcome = source.get("outcome") or {}
    if outcome.get("validation_status") != "NO_SUPPORT":
        raise Q022DesignGuardError("Q022 source trial must remain NO_SUPPORT.")
    if outcome.get("scientific_outcome") != "NO_PROMOTION_EVIDENCE":
        raise Q022DesignGuardError("Q022 source trial must remain NO_PROMOTION_EVIDENCE.")

    return design_fingerprint(payload)


def main() -> int:
    payload = json.loads(Q022_PATH.read_text(encoding="utf-8"))
    queue_payload = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    ledger_payload = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    fingerprint = validate_q022_design(payload, queue_payload, ledger_payload)
    print("Q022_DESIGN_GUARD=PASS")
    print(f"Q022_DESIGN_FINGERPRINT={fingerprint}")
    print("NO_PERFORMANCE_EXECUTION=True")
    print("NO_HOLDOUT_SELECTION=True")
    print("NO_RANKING=True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
