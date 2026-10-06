"""Deterministic candidate-gate compiler for Q218-Q221.

This module consumes only source/PIT-structure receipts and frozen candidate
contracts. It never reads market outcomes, ranks candidates, tunes parameters,
selects a holdout, or authorizes performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_IDS = ["Q218", "Q219", "Q220", "Q221"]
FORBIDDEN = (
    "performance_authorization",
    "promotion_authorization",
    "live_execution",
    "holdout_selection",
    "ranking",
    "tuning",
)


def sha256_json(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def load(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"missing input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def assert_safe(obj: dict, label: str) -> None:
    for key in FORBIDDEN:
        if obj.get(key) is True:
            raise SystemExit(f"{label}: unsafe boundary {key}=true")


def compile_gate(census: dict, specs: dict, q129_contract: dict | None = None) -> dict:
    assert census.get("candidate_ids") == CANDIDATE_IDS
    assert_safe(census, "census")
    assert specs.get("schema_version") == "1.0"
    spec_ids = [x.get("id") for x in specs.get("candidates", [])]
    for cid in CANDIDATE_IDS:
        if cid not in spec_ids:
            raise SystemExit(f"missing candidate contract: {cid}")

    q = {
        "Q218": {"sec_submission_census": census.get("q218_sec_pair_census", {})},
        "Q219": {"q129_contract_check": census.get("q219_q129_contract", {})},
        "Q220": {"sec_notes_census": census.get("q220_sec_notes_census", {})},
        "Q221": {"usa_rdtne_census": census.get("q221_usa_rdtne_census", {})},
    }

    out = {
        "schema_version": 1,
        "record_type": "q218_q221_candidate_gate_compiler",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_ids": CANDIDATE_IDS,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion_authorization": False,
        "live_execution": False,
        "results": {},
    }

    q218 = q.get("Q218", {})
    q218_issuers = q218.get("sec_submission_census", {}).get("issuer_results", {})
    pairable = [
        symbol for symbol, item in q218_issuers.items()
        if (
            item.get("pairability_observed") is True
            or int(item.get("pairable_report_period_count", 0) or 0) > 0
        )
    ]
    accepted_10k = sum(
        1 for item in q218_issuers.values()
        if isinstance(item.get("latest_10k"), dict)
        and item["latest_10k"].get("acceptance_datetime_found") is True
    )
    accepted_8k = sum(
        1 for item in q218_issuers.values()
        if isinstance(item.get("latest_8k_earnings_release"), dict)
        and item["latest_8k_earnings_release"].get("acceptance_datetime_found") is True
    )
    q218_ready = (
        len(q218_issuers) == 8
        and len(pairable) > 0
        and accepted_10k > 0
        and accepted_8k > 0
    )
    out["results"]["Q218"] = {
        "status": "SOURCE_STRUCTURE_READY_FOR_NEXT_PIT_GATE" if q218_ready else "SOURCE_STRUCTURE_INCOMPLETE",
        "issuer_count": len(q218_issuers),
        "pairable_issuer_count": len(pairable),
        "pairable_symbols": pairable,
        "accepted_latest_10k_count": accepted_10k,
        "accepted_latest_8k_earnings_release_count": accepted_8k,
        "pairing_contract": {
            "historical_pair_count_observed": sum(
                int(item.get("paired_10k_count", 0) or 0)
                for item in q218_issuers.values()
            ),
            "amendment_exclusion_frozen": all(
                item.get("pairing_excludes_amended_8k") is True
                for item in q218_issuers.values()
                if isinstance(item, dict)
            ),
        },
        "next_gate": "HISTORICAL_EVENT_PAIR_PIT_RECONSTRUCTION" if q218_ready else "REPAIR_SEC_MULTI_CHANNEL_SOURCE_COVERAGE",
    }

    q219_contract = q129_contract or q.get("Q219", {}).get("q129_contract_check", {})
    q219_ready = (
        q219_contract.get("contract_present") is True
        and q219_contract.get("independent_pit_receipt_present") is True
        and q219_contract.get("same_day_use_allowed") is False
    )
    out["results"]["Q219"] = {
        "status": "Q129_INPUT_CHAIN_READY_NO_SAME_DAY_USE" if q219_ready else "Q129_INPUT_CHAIN_INCOMPLETE",
        "contract_present": bool(q219_contract.get("contract_present")),
        "independent_pit_receipt_present": bool(q219_contract.get("independent_pit_receipt_present")),
        "same_day_use_allowed": q219_contract.get("same_day_use_allowed"),
        "next_gate": "POST_FILING_EVENT_JOIN_AND_LEAKAGE_AUDIT" if q219_ready else "REPAIR_Q129_INPUT_CHAIN",
    }

    q220_notes = q.get("Q220", {}).get("sec_notes_census", {})
    required = q220_notes.get("required_member_markers_present", {})
    canonical_required = ("sub", "tag", "dim", "num", "txt")
    legacy_required = ("sub.txt", "tag.txt", "dim.txt", "num.txt", "txt.txt")
    if all(marker in required for marker in canonical_required):
        q220_required_ok = all(required.get(marker) is True for marker in canonical_required)
    else:
        q220_required_ok = all(required.get(marker) is True for marker in legacy_required)
    q220_ready = q220_notes.get("zip_parse_ok") is True and q220_required_ok
    out["results"]["Q220"] = {
        "status": "XBRL_SOURCE_STRUCTURE_READY_FOR_DETERMINISTIC_MAPPING" if q220_ready else "XBRL_SOURCE_STRUCTURE_INCOMPLETE",
        "zip_parse_ok": bool(q220_notes.get("zip_parse_ok")),
        "required_member_markers_present": required,
        "next_gate": "AS_FILED_XBRL_TEXT_BLOCK_AND_PRESENTATION_MAPPING" if q220_ready else "REPAIR_SEC_NOTES_ARCHIVE_COMPONENT",
    }

    q221 = q.get("Q221", {}).get("usa_rdtne_census", {})
    # Consume the current Q221 census contract directly. Earlier compiler
    # revisions expected obsolete marker names that the live census never
    # emitted, creating a false-negative source-readiness result.
    q221_ready = (
        q221.get("source_clock_contract_ready") is True
        and q221.get("transactions_endpoint_documented") is True
        and q221.get("lookahead_used") is False
    )
    out["results"]["Q221"] = {
        "status": "USASPENDING_SOURCE_STRUCTURE_READY_FOR_PUBLIC_BOUNDARY_TEST" if q221_ready else "USASPENDING_SOURCE_STRUCTURE_INCOMPLETE",
        "source_clock_contract_ready": bool(q221.get("source_clock_contract_ready")),
        "contract_update_within_five_days": bool(q221.get("contract_update_within_five_days")),
        "publication_following_morning": bool(q221.get("publication_following_morning")),
        "transactions_endpoint_documented": bool(q221.get("transactions_endpoint_documented")),
        "dod_90_day_delay_exception_found": bool(q221.get("dod_90_day_delay_exception_found")),
        "fpds_three_business_days_found": bool(q221.get("fpds_three_business_days_found")),
        "lookahead_used": bool(q221.get("lookahead_used")),
        "next_gate": "HISTORICAL_PUBLIC_OBSERVATION_BOUNDARY_AND_ENTITY_MAPPING" if q221_ready else "REPAIR_USASPENDING_SOURCE_COMPONENT",
    }

    out["all_source_structure_components_ready"] = all(
        item["status"] in {
            "SOURCE_STRUCTURE_READY_FOR_NEXT_PIT_GATE",
            "Q129_INPUT_CHAIN_READY_NO_SAME_DAY_USE",
            "XBRL_SOURCE_STRUCTURE_READY_FOR_DETERMINISTIC_MAPPING",
            "USASPENDING_SOURCE_STRUCTURE_READY_FOR_PUBLIC_BOUNDARY_TEST",
        }
        for item in out["results"].values()
    )
    out["routing"] = {
        "Windows_A": "independent formal-readiness inheritance/PIT consistency audit; do not consume B output",
        "Windows_B": "Q218-Q221 source structure and next-gate execution",
        "Runner_C": "independent deterministic reproduction where explicitly routed",
        "performance_authorized": False,
        "promotion_authorized": False,
    }
    out["receipt_fingerprint"] = sha256_json(out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--specs", type=Path, default=ROOT / "research/candidates/orthogonal_candidate_specs_2026-10-05.json")
    parser.add_argument("--q129-contract", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    census = load(args.census)
    specs = load(args.specs)
    q129 = load(args.q129_contract) if args.q129_contract else None
    result = compile_gate(census, specs, q129)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
