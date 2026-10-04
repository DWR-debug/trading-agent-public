from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from automation.q121r6_sec_acceptance_time_compiler import (
    DISSEMINATION_CUTOFF,
    FORMS,
    R5_ROW_COUNT,
    R5_ROW_MULTICHET,
    STANDARD_CUTOFF,
    TARGET_BY_CIK,
    WINDOW_END,
    WINDOW_START,
    classify_acceptance,
    sha256_json,
)


SHARD_COUNT = 4
EXPECTED_RECEIPT_STATUS = "Q121R6_SEC_ACCEPTANCE_TIME_COMPILATION_COMPLETED"


def stable_event_key(event: dict[str, object]) -> tuple[str, str, str, str]:
    key = event["canonical_key"]
    assert isinstance(key, dict)
    return (
        str(key["cik"]),
        str(key["form"]),
        str(key["filed_date"]),
        str(key["accession_number"]),
    )


def aggregate(shard_paths: list[Path], output: Path) -> dict[str, object]:
    if len(shard_paths) != SHARD_COUNT:
        raise RuntimeError(f"SHARD_COUNT_MISMATCH:{len(shard_paths)}")

    shards = []
    for path in sorted(shard_paths):
        payload = json.loads(path.read_text(encoding="utf-8"))
        shards.append(payload)

    indices = sorted(int(x["shard_index"]) for x in shards)
    if indices != list(range(SHARD_COUNT)):
        raise RuntimeError(f"SHARD_INDEX_SET_MISMATCH:{indices}")

    identities = [x.get("execution_identity") for x in shards]
    if any(not isinstance(item, dict) for item in identities):
        raise RuntimeError("SHARD_EXECUTION_IDENTITY_MISSING")
    run_ids = {str(item.get("workflow_run_id")) for item in identities}
    attempts = {str(item.get("run_attempt")) for item in identities}
    shard_ids = {(str(item.get("workflow_run_id")), str(item.get("run_attempt")), int(item.get("shard_index"))) for item in identities}
    if None in run_ids or None in attempts or len(run_ids) != 1 or len(attempts) != 1:
        raise RuntimeError(f"SHARD_EXECUTION_IDENTITY_MIXED:{sorted(run_ids)}:{sorted(attempts)}")
    if len(shard_ids) != SHARD_COUNT:
        raise RuntimeError("SHARD_EXECUTION_IDENTITY_DUPLICATE")

    total_population_counts = {int(x["population_count"]) for x in shards}
    total_fingerprints = {str(x["population_fingerprint"]) for x in shards}
    if total_population_counts != {R5_ROW_COUNT}:
        raise RuntimeError(f"R5_POPULATION_COUNT_MISMATCH:{sorted(total_population_counts)}")
    if total_fingerprints != {R5_ROW_MULTICHET}:
        raise RuntimeError("R5_POPULATION_FINGERPRINT_MISMATCH")
    if any(x.get("status") != "COMPLETED" for x in shards):
        raise RuntimeError("Q121R6_INCOMPLETE_SHARD")
    if any(not isinstance(x.get("records"), list) for x in shards):
        raise RuntimeError("Q121R6_RECORDS_MISSING")

    expected_ranges = []
    for i in range(SHARD_COUNT):
        start = (R5_ROW_COUNT * i) // SHARD_COUNT
        end = (R5_ROW_COUNT * (i + 1)) // SHARD_COUNT
        expected_ranges.append((start, end))
    actual_ranges = [(int(x["slice_start"]), int(x["slice_end_exclusive"])) for x in sorted(shards, key=lambda v: int(v["shard_index"]))]
    if actual_ranges != expected_ranges:
        raise RuntimeError(f"SHARD_RANGE_MISMATCH:{actual_ranges}")

    records = []
    for shard in shards:
        records.extend(shard["records"])
    if len(records) != R5_ROW_COUNT:
        raise RuntimeError(f"HEADER_RECORD_COUNT_MISMATCH:{len(records)}")

    canonical_keys = [stable_event_key(r["header"]) for r in records]
    if len(canonical_keys) != len(set(canonical_keys)):
        counts = Counter(canonical_keys)
        duplicates = [list(k) for k, v in counts.items() if v > 1][:10]
        raise RuntimeError(f"DUPLICATE_CANONICAL_KEYS:{duplicates}")

    records.sort(key=lambda item: tuple(item["canonical_key"]))
    target_events = [
        item["header"]
        for item in records
        if bool(item["header"].get("target_issuer_match"))
    ]

    if any(event.get("subject_cik") not in TARGET_BY_CIK for event in target_events):
        raise RuntimeError("TARGET_EVENT_SUBJECT_MAPPING_FAILURE")
    if any(str(event.get("submission_type") or "").upper() not in {x.upper() for x in FORMS} for event in target_events):
        raise RuntimeError("UNEXPECTED_FORM")

    invalid_timing = [
        event for event in target_events
        if event.get("filing_date_matches_acceptance_date") is not True
        or event.get("event_class") == "OUT_OF_CONTRACT"
    ]
    if invalid_timing:
        raise RuntimeError(f"TARGET_ACCEPTANCE_TIME_CONTRACT_FAILURE:{len(invalid_timing)}")

    subject_counts = Counter(str(event["subject_cik"]) for event in target_events)
    class_counts = Counter(str(event["event_class"]) for event in target_events)
    revision_change_count = sum(
        1 for event in target_events
        if event.get("date_as_of_change")
        and str(event.get("date_as_of_change")).replace("-", "") != str(event["canonical_key"]["filed_date"]).replace("-", "")
    )

    header_hash_fingerprint = sha256_json([
        [list(r["canonical_key"]), r["header_sha256"]]
        for r in records
    ])
    target_event_fingerprint = sha256_json([
        {
            "canonical_key": r["canonical_key"],
            "subject_cik": r["subject_cik"],
            "filed_by_cik": r["filed_by_cik"],
            "accepted_datetime": r["accepted_datetime"],
            "event_class": r["event_class"],
            "date_as_of_change": r.get("date_as_of_change"),
        }
        for r in target_events
    ])

    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-121R6-SEC-ACCEPTANCE-TIME-COMPILATION",
        "status": EXPECTED_RECEIPT_STATUS,
        "window": {"start": WINDOW_START, "end": WINDOW_END},
        "forms": list(FORMS),
        "target_issuers": TARGET_BY_CIK,
        "population": {
            "source": "Q121-R5 form.idx population",
            "row_count": R5_ROW_COUNT,
            "row_multiset_fingerprint": R5_ROW_MULTICHET,
            "all_header_rows_fetched": len(records),
            "all_header_rows_validated": True,
            "header_hash_fingerprint": header_hash_fingerprint,
        },
        "target_subject_population": {
            "matched_event_count": len(target_events),
            "subject_counts_by_cik": dict(sorted(subject_counts.items())),
            "event_class_counts": dict(sorted(class_counts.items())),
            "target_event_fingerprint": target_event_fingerprint,
            "form_index_cik_equals_filed_by_for_all_rows": True,
            "filing_date_equals_acceptance_date_for_all_target_events": True,
            "acceptance_timestamp_compiled": True,
            "revision_change_date_nonmatching_file_date_count": revision_change_count,
        },
        "interpretation": {
            "full_subject_issuer_population_compiled": True,
            "acceptance_timestamps_compiled": True,
            "revision_lineage_established": False,
            "same_day_pit_safe": False,
            "first_public_availability_timestamp_available": False,
        },
        "governance": {
            "performance": False,
            "holdout": False,
            "selection": False,
            "ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "performance_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "receipt_basis": {
            "shard_count": SHARD_COUNT,
            "standard_cutoff_local": STANDARD_CUTOFF.isoformat(),
            "dissemination_cutoff_local": DISSEMINATION_CUTOFF.isoformat(),
            "timezone": "America/New_York",
            "note": "Acceptance datetime is an EDGAR acceptance clock. This receipt does not infer first public availability or same-day PIT safety.",
        },
    }
    result["receipt_fingerprint"] = sha256_json(result)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--shards", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = sorted(args.shards.glob("shard-*.json"))
    result = aggregate(paths, args.output)
    if result["status"] != EXPECTED_RECEIPT_STATUS:
        raise SystemExit("Q121R6_AGGREGATION_FAILED")


if __name__ == "__main__":
    main()
