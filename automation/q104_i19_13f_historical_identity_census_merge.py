"""Fail-closed deterministic merge for Q104:I19 historical 13F census shards."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from automation.q104_i19_13f_historical_identity_census import SHARDS as CENSUS_SHARDS

EXPECTED_SHARDS = {
    "2013-2016",
    "2017-2018",
    "2019-2020",
    "2021-2022",
    "2023",
    "2024-2025-09",
}
EXPECTED_SYMBOLS = {"SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN"}
OFFICIAL_SOURCE = "https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets"
EXPECTED_SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}
EXPECTED_BOUNDARY_FALSE = (
    "performance_authorized",
    "holdout_selection_allowed",
    "ranking_allowed",
    "parameter_search_allowed",
    "threshold_search_allowed",
    "horizon_search_allowed",
    "promotion_allowed",
    "live_execution_allowed",
)


def canonical_fingerprint(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("receipt_fingerprint", None)
    encoded = json.dumps(
        unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def seal(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload)
    payload.pop("receipt_fingerprint", None)
    payload["receipt_fingerprint"] = canonical_fingerprint(payload)
    return payload


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _acceptance_record(accession: str, record: dict[str, Any]) -> None:
    if record.get("accession") != accession:
        raise ValueError("Q104_I19_ACCEPTANCE_ACCESSION_MISMATCH:" + accession)
    if (
        record.get("acceptance_timezone") != "America/New_York"
        or record.get("acceptance_clock_basis") != "SEC_EDGAR_SGML_ACCEPTANCE_DATETIME"
    ):
        raise ValueError("Q104_I19_ACCEPTANCE_CLOCK_BASIS_UNVERIFIED:" + accession)
    if not re.fullmatch(r"\d{10}", str(record.get("filer_cik", ""))):
        raise ValueError("Q104_I19_ACCEPTANCE_FILER_CIK_INVALID:" + accession)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", str(record.get("acceptance_datetime", ""))):
        raise ValueError("Q104_I19_ACCEPTANCE_CLOCK_INVALID:" + accession)
    for key in ("filing_date", "period", "submission_type", "source_url"):
        if not str(record.get(key, "")).strip():
            raise ValueError(f"Q104_I19_ACCEPTANCE_{key.upper()}_MISSING:" + accession)
    if not str(record["source_url"]).startswith("https://www.sec.gov/Archives/edgar/data/"):
        raise ValueError("Q104_I19_ACCEPTANCE_SOURCE_URL_INVALID:" + accession)
    if not _is_sha256(record.get("header_sha256")):
        raise ValueError("Q104_I19_ACCEPTANCE_HEADER_HASH_INVALID:" + accession)
    if int(record.get("header_bytes", 0)) <= 0:
        raise ValueError("Q104_I19_ACCEPTANCE_HEADER_SIZE_INVALID:" + accession)


def _validate_shard(payload: dict[str, Any]) -> None:
    shard = str(payload.get("shard", ""))
    if shard not in EXPECTED_SHARDS:
        raise ValueError("Q104_I19_UNKNOWN_SHARD:" + shard)
    if payload.get("candidate_id") != "Q104:I19":
        raise ValueError("Q104_I19_SHARD_CANDIDATE_MISMATCH:" + shard)
    if payload.get("status") != "13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_SOURCE_ONLY":
        raise ValueError("Q104_I19_SHARD_STATUS_INVALID:" + shard)
    if not _is_sha256(payload.get("source_page_sha256")):
        raise ValueError("Q104_I19_SOURCE_PAGE_HASH_INVALID:" + shard)
    expected_start, expected_end = CENSUS_SHARDS[shard]
    expected_boundary = {
        "start_inclusive": expected_start.isoformat(),
        "end_exclusive": expected_end.isoformat(),
    }
    if payload.get("shard_boundary") != expected_boundary:
        raise ValueError("Q104_I19_SHARD_BOUNDARY_MISMATCH:" + shard)
    if not isinstance(payload.get("frozen_cusips"), dict) or set(payload["frozen_cusips"]) != EXPECTED_SYMBOLS:
        raise ValueError("Q104_I19_FROZEN_CUSIP_UNIVERSE_INVALID:" + shard)
    if not payload.get("archives") or int(payload.get("selected_archive_count", -1)) != len(payload["archives"]):
        raise ValueError("Q104_I19_SHARD_ARCHIVE_CLOSURE_FAILED:" + shard)
    for archive in payload["archives"]:
        try:
            period_start = date.fromisoformat(str(archive["archive"]["period_start"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Q104_I19_ARCHIVE_PERIOD_INVALID:" + shard) from exc
        if not expected_start <= period_start < expected_end:
            raise ValueError("Q104_I19_ARCHIVE_OUTSIDE_SHARD_BOUNDARY:" + shard)
    if payload.get("archive_completeness_for_shard") is not True:
        raise ValueError("Q104_I19_SHARD_ARCHIVE_COMPLETENESS_FAILED:" + shard)
    if not payload.get("synthetic") or any(value is not True for value in payload["synthetic"].values()):
        raise ValueError("Q104_I19_SHARD_SYNTHETIC_GATE_FAILED:" + shard)
    if payload.get("identity_conflicts"):
        raise ValueError("Q104_I19_SHARD_IDENTITY_CONFLICTS:" + shard)
    if payload.get("acceptance_failures"):
        raise ValueError("Q104_I19_SHARD_ACCEPTANCE_FAILURES:" + shard)
    join = payload.get("acceptance_time_join", {})
    records_checked = int(join.get("records_checked", -1))
    targets = int(join.get("target_unique_accessions", -1))
    if (
        join.get("complete") is not True
        or int(join.get("failures", -1)) != 0
        or records_checked <= 0
        or records_checked != targets
        or join.get("timezone_inference") is not False
    ):
        raise ValueError("Q104_I19_SHARD_ACCEPTANCE_JOIN_INCOMPLETE:" + shard)
    safety = payload.get("safety", {})
    if safety != EXPECTED_SAFETY:
        raise ValueError("Q104_I19_SHARD_SAFETY_BOUNDARY_INVALID:" + shard)
    boundary = payload.get("scientific_boundary", {})
    if any(boundary.get(key) is not False for key in EXPECTED_BOUNDARY_FALSE):
        raise ValueError("Q104_I19_SHARD_SCIENTIFIC_BOUNDARY_INVALID:" + shard)
    if payload.get("receipt_fingerprint") != canonical_fingerprint(payload):
        raise ValueError("Q104_I19_SHARD_FINGERPRINT_INVALID:" + shard)


def _archive_accession_records(archive: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not _is_sha256(archive.get("archive_sha256")):
        raise ValueError("Q104_I19_ARCHIVE_HASH_INVALID:" + str(archive.get("archive", {}).get("url", "")))
    if int(archive.get("archive_bytes", 0)) <= 0:
        raise ValueError("Q104_I19_ARCHIVE_SIZE_INVALID:" + str(archive.get("archive", {}).get("url", "")))
    if archive.get("acceptance_failures"):
        raise ValueError("Q104_I19_ARCHIVE_ACCEPTANCE_FAILURES:" + str(archive.get("archive", {}).get("url", "")))
    hits = archive.get("target_hits", {})
    if set(hits) != EXPECTED_SYMBOLS:
        raise ValueError("Q104_I19_ARCHIVE_TARGET_UNIVERSE_INVALID:" + str(archive.get("archive", {}).get("url", "")))
    out: dict[str, dict[str, Any]] = {}
    for symbol, hit in hits.items():
        accessions = set(str(x) for x in hit.get("accessions", []))
        records = hit.get("acceptance_records", {})
        if not isinstance(records, dict) or set(records) != accessions:
            raise ValueError("Q104_I19_ARCHIVE_ACCEPTANCE_ACCESSION_CLOSURE_FAILED:" + symbol)
        if hit.get("acceptance_complete") is not True:
            raise ValueError("Q104_I19_TARGET_ACCEPTANCE_INCOMPLETE:" + symbol)
        for accession, record in records.items():
            if not isinstance(record, dict):
                raise ValueError("Q104_I19_ACCEPTANCE_RECORD_INVALID:" + accession)
            _acceptance_record(str(accession), record)
            if accession in out and out[accession] != record:
                raise ValueError("Q104_I19_ARCHIVE_ACCEPTANCE_RECORD_CONFLICT:" + accession)
            out[str(accession)] = record
    expected_count = int(archive.get("target_unique_accession_count", -1))
    checked_count = int(archive.get("acceptance_record_count", -1))
    if expected_count <= 0 or len(out) != expected_count or checked_count != len(out):
        raise ValueError("Q104_I19_ARCHIVE_ACCEPTANCE_RECORD_COUNT_MISMATCH:" + str(archive.get("archive", {}).get("url", "")))
    return out


def build_receipt(payloads: list[dict[str, Any]], generated_at_utc: str | None = None) -> dict[str, Any]:
    """Validate all shards and build one compiler-ready clock-complete census receipt."""
    if len(payloads) != len(EXPECTED_SHARDS):
        raise ValueError("Q104_I19_MISSING_OR_DUPLICATE_SHARDS")
    seen_shards: set[str] = set()
    for payload in payloads:
        _validate_shard(payload)
        shard = str(payload["shard"])
        if shard in seen_shards:
            raise ValueError("Q104_I19_DUPLICATE_SHARD:" + shard)
        seen_shards.add(shard)
    if seen_shards != EXPECTED_SHARDS:
        raise ValueError("Q104_I19_MISSING_OR_DUPLICATE_SHARDS")

    source_hashes = {str(p["source_page_sha256"]) for p in payloads}
    if len(source_hashes) != 1:
        raise ValueError("Q104_I19_SOURCE_PAGE_HASH_MISMATCH")
    frozen = payloads[0]["frozen_cusips"]
    if any(p["frozen_cusips"] != frozen for p in payloads[1:]):
        raise ValueError("Q104_I19_FROZEN_CUSIP_MISMATCH")

    archives: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    seen_accessions: dict[str, dict[str, Any]] = {}
    identity_conflicts: set[str] = set()
    total_target_accessions = 0
    total_checked_records = 0
    for payload in payloads:
        for archive in payload["archives"]:
            metadata = archive.get("archive", {})
            url = str(metadata.get("url", ""))
            if not url.startswith("https://www.sec.gov/") or url in seen_urls:
                raise ValueError("Q104_I19_DUPLICATE_OR_INVALID_ARCHIVE_URL:" + url)
            seen_urls.add(url)
            if not str(metadata.get("period_start", "")):
                raise ValueError("Q104_I19_ARCHIVE_PERIOD_MISSING:" + url)
            archive_records = _archive_accession_records(archive)
            for accession, record in archive_records.items():
                if accession in seen_accessions:
                    if seen_accessions[accession] != record:
                        raise ValueError("Q104_I19_CROSS_ARCHIVE_ACCEPTANCE_RECORD_CONFLICT:" + accession)
                    raise ValueError("Q104_I19_DUPLICATE_ACCESSION_ACROSS_ARCHIVES:" + accession)
                seen_accessions[accession] = record
            total_target_accessions += int(archive["target_unique_accession_count"])
            total_checked_records += int(archive["acceptance_record_count"])
            identity_conflicts.update(archive.get("security_identity_conflicts", []))
            archives.append(archive)

    if identity_conflicts:
        raise ValueError("Q104_I19_SECURITY_IDENTITY_CONFLICTS:" + ",".join(sorted(identity_conflicts)))
    archives.sort(key=lambda x: (x["archive"]["period_start"], x["archive"]["url"]))
    if not archives or total_target_accessions <= 0 or total_checked_records != total_target_accessions:
        raise ValueError("Q104_I19_ACCEPTANCE_RECORD_COUNT_MISMATCH")
    if len(seen_accessions) != total_target_accessions:
        raise ValueError("Q104_I19_GLOBAL_ACCEPTANCE_JOIN_COUNT_MISMATCH")
    coverage = {}
    for symbol in sorted(frozen):
        matched = sum(1 for archive in archives if archive["target_hits"].get(symbol, {}).get("row_count", 0) > 0)
        coverage[symbol] = {
            "archives_with_match": matched,
            "archives_without_match": len(archives) - matched,
        }

    receipt: dict[str, Any] = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-06-104-I19-13F-HISTORICAL-ID-CENSUS",
        "candidate_id": "Q104:I19",
        "status": "13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_COMPLETED_SOURCE_PIT_CLOCK_ONLY",
        "generated_at_utc": generated_at_utc or datetime.now(timezone.utc).isoformat(),
        "official_source": OFFICIAL_SOURCE,
        "acceptance_timezone": "America/New_York",
        "acceptance_clock_basis": "SEC_EDGAR_SGML_ACCEPTANCE_DATETIME",
        "source_page_sha256": next(iter(source_hashes)),
        "completed_shards": sorted(seen_shards),
        "archive_count": len(archives),
        "frozen_cusips": frozen,
        "archives": archives,
        "coverage_summary": coverage,
        "identity_conflicts": [],
        "acceptance_time_join": {
            "target_unique_accessions": total_target_accessions,
            "records_checked": total_checked_records,
            "failures": 0,
            "complete": True,
            "timezone_inference": False,
        },
        "scientific_boundary": {key: False for key in EXPECTED_BOUNDARY_FALSE},
        "safety": dict(EXPECTED_SAFETY),
        "next_gate": "concept-specific PIT compiler + independent reproduction",
    }
    return seal(receipt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        payloads = [json.loads(path.read_text(encoding="utf-8")) for path in args.input_dir.rglob("shard_receipt.json")]
        receipt = build_receipt(payloads)
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit(str(exc)) from exc
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "archive_count": receipt["archive_count"],
        "completed_shards": receipt["completed_shards"],
        "acceptance_time_join": receipt["acceptance_time_join"],
        "receipt_fingerprint": receipt["receipt_fingerprint"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
