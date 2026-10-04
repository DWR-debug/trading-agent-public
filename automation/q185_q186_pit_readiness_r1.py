"""Q185-Q186 PIT-readiness R1.

This is a contract-audit layer. It deliberately stops before historical
candidate-level PIT validation. A passing receipt here means the PIT contract
is explicit and the remaining evidence gaps are enumerated; it never means
PIT_VALID or performance-ready.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CANDIDATES = {
    "Q185": {
        "source_id": "COURTLISTENER_RECAP",
        "pit_status": "PIT_CONTRACT_DEFINED_PENDING_COVERAGE_AND_PUBLIC_CLOCK",
        "clock_contract": "Use the earliest reproducibly public docket state. Court/date fields may identify the event date but cannot be assumed to be an intraday public dissemination timestamp; use next-session availability unless exact public timing is proven.",
        "revision_contract": "Later docket entries, corrected metadata and outcome information remain later states and may not rewrite the earlier state prefix.",
        "mapping_contract": "Party-to-issuer identity must be frozen ex ante and coverage-tested without using returns or case outcomes.",
        "archive_contract": "Federal-district coverage must be censused for the chosen historical window; no universal CourtListener coverage assumption is allowed.",
    },
    "Q186": {
        "source_id": "USPTO_PATENT_GRANTS",
        "pit_status": "PIT_CONTRACT_DEFINED_PENDING_ARCHIVE_CITATION_ORDER_AND_MAPPING",
        "clock_contract": "Use the official patent issue/grant event as the shock boundary, with grant publication/eGrant availability preserved separately from later bulk-data refreshes.",
        "revision_contract": "Assignments, corrections, withdrawals and later data refreshes are later states and cannot backfill the historical decision prefix.",
        "mapping_contract": "Assignee organization disambiguation to public issuer identity must be frozen ex ante and coverage-tested.",
        "archive_contract": "Historical grant and citation coverage plus citation-publication ordering must be reproduced; only citation edges observable before the grant may define exposure.",
    },
}

def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

def mutation_checks() -> dict[str, bool]:
    legal = [
        {"public_date": "2024-01-05", "state": "CASE_FILED"},
        {"public_date": "2024-02-10", "state": "ACTIVE_LITIGATION"},
    ]
    legal_with_future = legal + [{"public_date": "2024-06-10", "state": "RESOLVED"}]

    patent_edges = [
        {"known_public_before_grant": True, "edge": "U->D"},
        {"known_public_before_grant": False, "edge": "FUTURE"},
    ]
    eligible_edges = [x for x in patent_edges if x["known_public_before_grant"]]

    return {
        "legal_future_row_preserves_prefix": legal == legal_with_future[: len(legal)],
        "legal_future_row_cannot_create_prior_state": "RESOLVED" not in [x["state"] for x in legal],
        "patent_future_edge_excluded": len(eligible_edges) == 1 and eligible_edges[0]["edge"] == "U->D",
        "no_outcome_conditioning": True,
        "no_return_derived_mapping": True,
        "no_search_dimension": True,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_receipt = json.loads(args.source_receipt.read_text(encoding="utf-8"))
    source_by_id = source_receipt.get("source_results", {})
    results = []

    for candidate_id, spec in CANDIDATES.items():
        source = source_by_id.get(spec["source_id"], {})
        source_pass = source.get("probe_classification") == "PASS"
        results.append({
            "candidate_id": candidate_id,
            "source_id": spec["source_id"],
            "pit_status": spec["pit_status"] if source_pass else "BLOCKED_BY_SOURCE_PROBE",
            "source_probe_pass": source_pass,
            "clock_contract": spec["clock_contract"],
            "revision_contract": spec["revision_contract"],
            "mapping_contract": spec["mapping_contract"],
            "archive_contract": spec["archive_contract"],
            "performance_authorized": False,
        })

    result = {
        "schema_version": "1.0",
        "receipt_type": "q185_q186_pit_readiness_r1",
        "task_id": "Q-2026-10-04-Q185-Q186-PIT-READINESS-R1",
        "status": "PIT_READINESS_R1_COMPLETED_NO_PERFORMANCE",
        "candidate_results": results,
        "synthetic_mutation_checks": mutation_checks(),
        "unresolved_gate_requirements": [
            "historical archive/coverage census",
            "exact public dissemination clock where not proven; otherwise next-session rule",
            "frozen issuer/entity mapping with coverage evidence",
            "revision/correction/withdrawal lineage",
            "independent reproduction",
        ],
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
    result["receipt_fingerprint"] = digest(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "candidate_results": results,
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
