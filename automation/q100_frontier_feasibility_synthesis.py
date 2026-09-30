from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_Q096_STATUS = "SOURCE_AND_PIT_FEASIBILITY_ONLY"
EXPECTED_Q098_STATUS = "HISTORICAL_SOURCE_DEPTH_ONLY"


def load_object(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"NOT_AN_OBJECT:{path}")
    return data


def assert_non_authorizing(payload: dict, label: str) -> None:
    forbidden = (
        "performance_evaluation",
        "holdout_evaluation",
        "candidate_selection",
        "candidate_ranking",
        "parameter_search",
        "asset_search",
        "automatic_promotion",
        "performance_authorized",
    )
    for key in forbidden:
        if payload.get(key) is True:
            raise ValueError(f"{label}_AUTHORIZATION_GUARD_FAILED:{key}")


def probe_index(q096: dict, q098: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    return (
        {
            str(row["id"]): row
            for row in q096.get("live_source_probes", [])
            if isinstance(row, dict) and row.get("id")
        },
        {
            str(row["id"]): row
            for row in q098.get("probes", [])
            if isinstance(row, dict) and row.get("id")
        },
    )


def candidate_gate(next_row: dict, probes96: dict[str, dict], probes98: dict[str, dict]) -> dict:
    code = next_row["candidate"]
    source = next_row["source"]
    source_lower = source.lower()
    existing_state = next_row["existing_state"]

    required: list[str] = []
    readiness = "BLOCKED"
    reason = "PIT_OR_HISTORICAL_PROVENANCE_PENDING"

    if existing_state == "MACHINE_FEASIBILITY_IMPLEMENTED" and next_row["pit_state"] == "MACHINE_FEASIBILITY_PRESENT":
        required.append("FRESH_SYMBOL_DISJOINT_INPUT_FREEZE")

    if "sec item 1a" in source_lower:
        required.append("HISTORICAL_10K_ARCHIVE_COMPLETENESS_AND_ACCEPTANCE_PIT")
        reason = "SEC_RISK_TEXT_HISTORICAL_ARCHIVE_CONTENT_MAPPING_PENDING"
    elif "public news" in source_lower:
        required.append("HISTORICAL_NEWS_ENTITY_MAPPING_AND_PIT")
        reason = "PUBLIC_NEWS_HISTORICAL_ENTITY_MAPPING_PENDING"
    elif "scheduled benchmark" in source_lower:
        required.append("HISTORICAL_REBALANCE_ARCHIVE_AND_IDENTIFIER_MAPPING")
        reason = "BENCHMARK_REBALANCE_ARCHIVE_PENDING"
    elif "sec form 4" in source_lower:
        required.append("HISTORICAL_FORM4_ARCHIVE_COMPLETENESS_AND_TRANSACTION_MAPPING")
        reason = "FORM4_HISTORICAL_COMPLETENESS_PENDING"
    elif "sec 13f" in source_lower:
        required.append("HISTORICAL_13F_ARCHIVE_COMPLETENESS_AND_MANAGER_MAPPING")
        reason = "13F_HISTORICAL_COMPLETENESS_PENDING"
    elif "fails-to-deliver" in source_lower:
        required.append("HISTORICAL_FTD_SNAPSHOT_AND_REGIME_MAPPING")
        reason = "FTD_HISTORICAL_REGIME_MAPPING_PENDING"
    elif "short interest" in source_lower:
        required.append("HISTORICAL_FINRA_PUBLICATION_SCHEDULE_AND_SECURITY_MAPPING")
        reason = "FINRA_SHORT_INTEREST_HISTORY_MAPPING_PENDING"
    elif "schedule 13d" in source_lower or "schedule 13g" in source_lower or "beneficial ownership" in source_lower:
        required.append("HISTORICAL_13D13G_ARCHIVE_AND_AMENDMENT_MAPPING")
        reason = "13D13G_HISTORICAL_COMPLETENESS_PENDING"
    elif "form 144" in source_lower:
        required.append("ELECTRONIC_FORM144_WINDOW_AND_ARCHIVE_COMPLETENESS")
        reason = "FORM144_HISTORICAL_WINDOW_LIMITATION_REQUIRES_EXPLICIT_STUDY_BOUNDARY"

    # Archive probes are evidentiary support only; they never upgrade performance readiness.
    archive_evidence = []
    if "sec form 4" in source_lower:
        archive_evidence.append(probes96.get("SEC_SUBMISSIONS_FORM4_SAMPLE", {}).get("status"))
    if "sec 13f" in source_lower:
        archive_evidence.append(probes98.get("SEC_ARCHIVE_13F_MANAGER", {}).get("status"))
    if "form 144" in source_lower:
        archive_evidence.append(probes98.get("SEC_HISTORICAL_ANCHOR_FORM144", {}).get("status"))
    if "schedule 13d" in source_lower or "schedule 13g" in source_lower:
        archive_evidence.append(probes98.get("SEC_HISTORICAL_ANCHOR_13D_G", {}).get("status"))

    # C29 is purely canonical daily-close data and already machine-tested.
    if code == "frontier:C29" and next_row["archive_state"] == "NO_NEW_EXTERNAL_ARCHIVE_GATE":
        readiness = "READY_FOR_FRESH_INPUT_CONTRACT"
        reason = "MACHINE_FEASIBILITY_PRESENT_AND_CANONICAL_PRICE_DATA_PATH"
        required = ["FRESH_SYMBOL_DISJOINT_INPUT_FREEZE", "FORMAL_PIT_RECEIPT_REUSE_OR_REVALIDATION"]

    return {
        "candidate": code,
        "name": next_row["name"],
        "existing_state": existing_state,
        "source_state": next_row["source_state"],
        "pit_state": next_row["pit_state"],
        "archive_state": next_row["archive_state"],
        "feasibility_readiness": readiness,
        "reason": reason,
        "next_required_gates": required,
        "supporting_archive_probe_statuses": archive_evidence,
        "performance_authorized": False,
        "candidate_selection": False,
        "candidate_ranking": False,
    }


def synthesize(q096: dict, q098: dict) -> dict:
    if q096.get("status") != EXPECTED_Q096_STATUS:
        raise ValueError("Q096_STATUS_MISMATCH")
    if q098.get("status") != EXPECTED_Q098_STATUS:
        raise ValueError("Q098_STATUS_MISMATCH")
    assert_non_authorizing(q096.get("governance", {}), "Q096")
    assert_non_authorizing(q098, "Q098")

    probes96, probes98 = probe_index(q096, q098)
    matrix = q096.get("candidate_gate_matrix")
    if not isinstance(matrix, list) or len(matrix) != int(q096.get("inventory_count", 0)):
        raise ValueError("Q100_CANDIDATE_MATRIX_MISMATCH")

    rows = [candidate_gate(row, probes96, probes98) for row in matrix]
    ready = [r for r in rows if r["feasibility_readiness"] != "BLOCKED"]

    return {
        "schema_version": "1.0",
        "task_id": "Q-2026-09-30-100-FRONTIER-FEASIBILITY-SYNTHESIS",
        "status": "FEASIBILITY_SYNTHESIS_ONLY",
        "input_status": {
            "q096": EXPECTED_Q096_STATUS,
            "q098": EXPECTED_Q098_STATUS,
            "q096_inventory_count": q096["inventory_count"],
        },
        "summary": {
            "candidate_count": len(rows),
            "ready_for_next_gate_count": len(ready),
            "blocked_count": len(rows) - len(ready),
            "ready_candidates": [r["candidate"] for r in ready],
            "note": "Readiness is a gate-state classification, not a ranking or selection decision.",
        },
        "candidates": rows,
        "governance": {
            "performance_evaluation": False,
            "holdout_evaluation": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "horizon_search": False,
            "performance_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--q096", type=Path, default=Path("research/runs/q096_frontier_source_pit_audit/result.json"))
    parser.add_argument("--q098", type=Path, default=Path("research/runs/q098_historical_archive_depth/result.json"))
    parser.add_argument("--output", type=Path, default=Path("research/runs/q100_frontier_feasibility_synthesis/result.json"))
    args = parser.parse_args()
    receipt = synthesize(load_object(args.q096), load_object(args.q098))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q100_STATUS:", receipt["status"])
    print("Q100_READY_FOR_NEXT_GATE:", receipt["summary"]["ready_for_next_gate_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
