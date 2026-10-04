"""Q187-Q192 PIT-readiness compiler.

Consumes only the immutable/latest source-feasibility receipt and emits a
candidate-specific PIT contract checklist. No returns, rankings, selection,
parameter search or performance authorization are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CANDIDATE_REQUIREMENTS: dict[str, list[str]] = {
    "Q187": [
        "historical_transaction_archive_reconstructed",
        "public_observation_boundary_proven",
        "recipient_to_issuer_mapping_frozen",
        "modification_lineage_reconstructed",
        "revision_history_immutable_prefix_proven",
        "same_day_use_proven",
    ],
    "Q188": [
        "historical_srlc_archive_reconstructed",
        "first_public_update_boundary_proven",
        "application_to_issuer_mapping_frozen",
        "supplement_correction_lineage_reconstructed",
        "revision_history_immutable_prefix_proven",
        "same_day_use_proven",
    ],
    "Q189": [
        "historical_recall_archive_reconstructed",
        "recall_publication_boundary_proven",
        "product_to_manufacturer_issuer_mapping_frozen",
        "revision_withdrawal_lineage_reconstructed",
        "revision_history_immutable_prefix_proven",
        "same_day_use_proven",
    ],
    "Q190": [
        "historical_echo_refresh_archive_reconstructed",
        "public_refresh_boundary_proven",
        "facility_to_issuer_mapping_frozen",
        "enforcement_revision_lineage_reconstructed",
        "revision_history_immutable_prefix_proven",
        "same_day_use_proven",
    ],
    "Q191": [
        "historical_patent_publication_archive_reconstructed",
        "historical_science_publication_archive_reconstructed",
        "science_publication_boundary_proven",
        "patent_publication_boundary_proven",
        "patent_paper_linkage_frozen",
        "issuer_mapping_frozen",
        "same_day_ordering_proven",
    ],
    "Q192": [
        "historical_shortage_archive_reconstructed",
        "first_public_observation_boundary_proven",
        "manufacturer_product_mapping_frozen",
        "resolution_discontinuation_lineage_reconstructed",
        "revision_history_immutable_prefix_proven",
        "same_day_use_proven",
    ],
}


def sha(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compile_pit(source_receipt: dict[str, Any]) -> dict[str, Any]:
    results = []
    for candidate_id, requirements in CANDIDATE_REQUIREMENTS.items():
        src = next(
            (x for x in source_receipt.get("candidate_results", []) if x.get("candidate_id") == candidate_id),
            None,
        )
        source_status = src.get("status") if src else "MISSING_SOURCE_RESULT"
        status = (
            "PIT_READINESS_BLOCKED_BY_SOURCE"
            if source_status != "SOURCE_PROBES_PASSED"
            else "PIT_CONTRACT_DEFINED_PENDING_HISTORICAL_PROOF"
        )
        results.append(
            {
                "candidate_id": candidate_id,
                "source_status": source_status,
                "pit_status": status,
                "required_proofs": {key: False for key in requirements},
                "next_gate": (
                    "Repair/source-probe gate before PIT work"
                    if source_status != "SOURCE_PROBES_PASSED"
                    else "Run fixed historical archive/clock/mapping/revision census; no performance access"
                ),
                "performance_authorized": False,
                "selection_allowed": False,
                "ranking_allowed": False,
                "parameter_search_allowed": False,
                "holdout_selection_allowed": False,
            }
        )

    return {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-04-Q187-Q192-PIT-READINESS-R1",
        "status": "PIT_READINESS_COMPILATION_COMPLETED",
        "source_receipt_fingerprint": source_receipt.get("receipt_fingerprint"),
        "candidate_results": results,
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "selection": False,
            "ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "promotion": False,
            "live_execution": False,
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
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = json.loads(args.source_receipt.read_text(encoding="utf-8"))
    result = compile_pit(source)
    result["receipt_fingerprint"] = sha(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
