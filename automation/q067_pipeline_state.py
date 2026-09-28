"""Fail-closed operational state summary for the Q067 execution pipeline.

This module reads only repository evidence and authorization files. It never creates
scientific evidence, selects candidates, changes gates or performs performance work.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from automation.q067_alpha_mechanisms import Q067_SYMBOLS

ROOT = Path(__file__).resolve().parents[1]
COVERAGE_ID = "T-2026-09-28-067-COVERAGE"
PIT_ID = "T-2026-09-28-067-PIT"
PERFORMANCE_ID = "T-2026-09-28-067-PERFORMANCE"
PERFORMANCE_AUTH = ROOT / "research/authorizations/q067_performance_2026_09_28.json"
COVERAGE_RESULT = ROOT / "research/evidence/q067_coverage_result.json"
PIT_RESULT = ROOT / "research/evidence/q067_pit_result.json"
PERFORMANCE_RESULT = ROOT / "research/evidence/q067_performance_result.json"
LEDGER = ROOT / "research/evidence/trial_ledger.json"
PREREG = ROOT / "research/preregistrations/q067_performance_2026_09_28.json"


def _load(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def summarize(repo_root: Path = ROOT) -> dict[str, Any]:
    coverage = _load(repo_root / COVERAGE_RESULT.relative_to(ROOT))
    pit = _load(repo_root / PIT_RESULT.relative_to(ROOT))
    auth = _load(repo_root / PERFORMANCE_AUTH.relative_to(ROOT))
    result = _load(repo_root / PERFORMANCE_RESULT.relative_to(ROOT))
    prereg = _load(repo_root / PREREG.relative_to(ROOT))
    ledger = _load(repo_root / LEDGER.relative_to(ROOT)) or {}
    trials = ledger.get("trials", [])
    trial_ids = {row.get("trial_id") for row in trials if isinstance(row, dict)}

    blockers: list[str] = []
    state = "DESIGN_FROZEN"

    if prereg is None:
        blockers.append("Q067 performance preregistration missing")
        return _state(state, blockers, coverage, pit, auth, result, trial_ids)

    if prereg.get("symbols") != list(Q067_SYMBOLS):
        blockers.append("Q067 preregistration symbols do not match frozen alpha universe")
    if prereg.get("status") != "PREREGISTERED_PERFORMANCE":
        blockers.append("Q067 performance preregistration status is invalid")
    if prereg.get("safety") != {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }:
        blockers.append("Q067 performance preregistration safety contract is invalid")

    for label, payload, expected_id, expected_status in (
        ("coverage", coverage, COVERAGE_ID, "COVERAGE_PASSED"),
        ("pit", pit, PIT_ID, "PIT_PASSED"),
    ):
        if payload is None:
            blockers.append(f"{label} receipt missing")
        else:
            if payload.get("trial_id") != expected_id:
                blockers.append(f"{label} receipt trial identity mismatch")
            if payload.get("status") != expected_status:
                blockers.append(f"{label} receipt status is not {expected_status}")
            if payload.get("performance_trial_authorized") is not False:
                blockers.append(f"{label} receipt unexpectedly authorizes performance")
            if payload.get("selection_used") is not False:
                blockers.append(f"{label} receipt records selection")
            safety = payload.get("safety")
            if safety != {
                "paper_only": True,
                "live_trading_enabled": False,
                "orders_enabled": False,
                "automatic_promotion": False,
            }:
                blockers.append(f"{label} receipt safety contract is invalid")

    if blockers:
        state = "PREFLIGHT_BLOCKED"

    preflight_pass = coverage is not None and pit is not None and not any(
        item.startswith(("coverage receipt", "pit receipt", "coverage receipt unexpectedly",
                         "pit receipt unexpectedly", "coverage receipt records",
                         "pit receipt records", "coverage receipt safety",
                         "pit receipt safety"))
        for item in blockers
    )
    # Re-evaluate directly so a malformed preregistration can never make the pipeline appear ready.
    preflight_pass = (
        not blockers
        and coverage is not None
        and pit is not None
        and coverage.get("trial_id") == COVERAGE_ID
        and coverage.get("status") == "COVERAGE_PASSED"
        and pit.get("trial_id") == PIT_ID
        and pit.get("status") == "PIT_PASSED"
        and coverage.get("performance_trial_authorized") is False
        and pit.get("performance_trial_authorized") is False
    )
    if preflight_pass:
        if auth is None:
            state = "PREFLIGHT_PASSED_WAITING_FOR_AUTO_AUTH"
        elif auth.get("authorized") is True and auth.get("performance_execution_authorized") is True:
            state = "PERFORMANCE_AUTHORIZED"
        else:
            blockers.append("Q067 performance authorization exists but is invalid")
            state = "PREFLIGHT_BLOCKED"
    
    if result is not None:
        if result.get("trial_id") != PERFORMANCE_ID:
            blockers.append("Q067 performance result trial identity mismatch")
            state = "PERFORMANCE_EVIDENCE_INVALID"
        elif result.get("status") != "COMPLETED":
            blockers.append("Q067 performance result is not completed")
            state = "PERFORMANCE_EVIDENCE_INVALID"
        elif result.get("selection_used") is not False or result.get("holdout_used_for_selection") is not False:
            blockers.append("Q067 performance result records selection")
            state = "PERFORMANCE_EVIDENCE_INVALID"
        elif PERFORMANCE_ID in trial_ids:
            state = "PERFORMANCE_RECONCILED"
        else:
            state = "PERFORMANCE_COMPLETED_PENDING_LEDGER"

    return _state(state, blockers, coverage, pit, auth, result, trial_ids)


def _state(state: str, blockers: list[str], coverage, pit, auth, result, trial_ids) -> dict[str, Any]:
    return {
        "family": "Q067",
        "state": state,
        "blocking_reasons": sorted(set(blockers)),
        "coverage_receipt": {
            "present": coverage is not None,
            "status": coverage.get("status") if coverage else None,
            "trial_id": coverage.get("trial_id") if coverage else None,
        },
        "pit_receipt": {
            "present": pit is not None,
            "status": pit.get("status") if pit else None,
            "trial_id": pit.get("trial_id") if pit else None,
        },
        "performance_authorization": {
            "present": auth is not None,
            "authorized": auth.get("authorized") if auth else None,
            "execution_scope": auth.get("execution_scope") if auth else None,
        },
        "performance_result": {
            "present": result is not None,
            "status": result.get("status") if result else None,
            "trial_id": result.get("trial_id") if result else None,
        },
        "ledger_reconciled": PERFORMANCE_ID in trial_ids,
        "no_selection_or_promotion": True,
        "paper_only": True,
    }


def main() -> int:
    summary = summarize()
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not summary["blocking_reasons"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
