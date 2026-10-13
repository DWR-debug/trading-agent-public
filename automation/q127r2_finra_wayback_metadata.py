"""Q127-R2: cheap historical archive-metadata feasibility check for FINRA R1 files.

Only queries Internet Archive CDX metadata plus two fixed historical captures of
the official FINRA listing. It never downloads the four FINRA target data files.
This does not establish first-publication time or original-vs-updated lineage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from automation.wayback_cdx_metadata import (
    MetadataProbeError,
    build_cdx_url,
    canonical_fingerprint,
    fetch_bounded,
    parse_cdx_rows,
)

R1_FP = "2cbe22c49d885f527ac523ed74ab1e13a843c23999916c674282de6977e9c33c"
R1_TASK = "Q-2026-10-03-127R1-FINRA-REGSHO-HISTORICAL-PIT"
FIXED_DATES = ("2024-02-05", "2024-07-01", "2025-01-02", "2025-09-24")
SYMBOLS = ("SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN")
LISTING_URL = "https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files"
ARCHIVE_SNAPSHOTS = (("20240722180837", "20240701"), ("20250120103629", "20250102"))
MAX_REQUESTS = 7
MAX_RESPONSE_BYTES = 350_000
MAX_TOTAL_BYTES = 1_500_000
TARGET_URLS = {
    day: f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{day.replace('-', '')}.txt"
    for day in FIXED_DATES
}
FROZEN = {
    "RUN_Q127R2_FINRA_WAYBACK_METADATA": "true",
    "R1_SOURCE_RUN_ID": "38455702686",
    "R1_ARTIFACT_NAME": "q127r1-finra-regsho-historical-pit-38455702686",
    "R1_RECEIPT_FINGERPRINT": R1_FP,
    "R1_TASK_ID": R1_TASK,
    "FIXED_DATES": ",".join(FIXED_DATES),
    "FIXED_SYMBOLS": ",".join(SYMBOLS),
    "SOURCE_LISTING_URL": LISTING_URL,
    "LISTING_SNAPSHOTS": "20240722180837:20240701,20250120103629:20250102",
    "MAX_REQUESTS": str(MAX_REQUESTS),
    "MAX_RESPONSE_BYTES": str(MAX_RESPONSE_BYTES),
    "MAX_TOTAL_BYTES": str(MAX_TOTAL_BYTES),
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}
REQUEST_PATH = Path("research/run_requests/q127r2_finra_wayback_metadata.trigger")
R1_RUN_RECEIPT = "q127r1-finra-regsho-historical-pit-38455702686"


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw:
            continue
        if not re.fullmatch(r"[A-Z0-9_]+=[A-Za-z0-9._,:/%& -]*", raw):
            raise MetadataProbeError(f"REQUEST_LINE_INVALID:{line_no}")
        key, value = raw.split("=", 1)
        if key in values:
            raise MetadataProbeError(f"REQUEST_DUPLICATE_KEY:{key}")
        values[key] = value
    if set(values) != set(FROZEN) | {"REQUEST_SEQUENCE"}:
        raise MetadataProbeError("REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN.items():
        if values.get(key) != expected:
            raise MetadataProbeError(f"FROZEN_REQUEST_MISMATCH:{key}")
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values.get("REQUEST_SEQUENCE", "")):
        raise MetadataProbeError("REQUEST_SEQUENCE_INVALID")
    return values


def validate_r1(receipt: dict[str, Any]) -> None:
    if (
        receipt.get("task_id") != R1_TASK
        or receipt.get("status") != "Q127R1_SOURCE_PIT_FEASIBILITY_COMPLETED"
        or receipt.get("receipt_fingerprint") != R1_FP
        or set((receipt.get("observations") or {}).keys()) != set(FIXED_DATES)
        or receipt.get("pit", {}).get("same_day_pit_safe") is not False
        or receipt.get("pit", {}).get("revision_lineage_established") is not False
    ):
        raise MetadataProbeError("Q127R1_UPSTREAM_RECEIPT_PIN_MISMATCH")
    for date in FIXED_DATES:
        obs = receipt["observations"][date]
        if obs.get("source_url") != TARGET_URLS[date] or obs.get("status") != "PASS":
            raise MetadataProbeError(f"Q127R1_FIXED_OBSERVATION_MISMATCH:{date}")
        if set((obs.get("rows_for_fixed_symbols") or {}).keys()) != set(SYMBOLS):
            raise MetadataProbeError(f"Q127R1_FIXED_SYMBOL_COVERAGE_MISMATCH:{date}")


def run(
    request_path: Path,
    source_receipt_path: Path,
    output_path: Path,
    *,
    fetcher: Callable[..., tuple[int, bytes, dict[str, str]]] = fetch_bounded,
) -> dict[str, Any]:
    request = read_request(request_path)
    source = json.loads(source_receipt_path.read_text(encoding="utf-8"))
    validate_r1(source)
    budget: dict[str, Any] = {"request_count": 0, "metadata_download_bytes": 0, "transport_errors": []}
    requests: list[dict[str, Any]] = []
    errors: list[str] = []

    def one(label: str, url: str, *, parse_json: bool = True, expected_original: str | None = None) -> tuple[int, bytes, list[dict[str, str]] | None]:
        try:
            status, body, headers = fetcher(
                url,
                max_requests=MAX_REQUESTS,
                max_response_bytes=MAX_RESPONSE_BYTES,
                max_total_bytes=MAX_TOTAL_BYTES,
                state=budget,
            )
            record = {
                "label": label,
                "request_url": url,
                "http_status": status,
                "response_bytes": len(body),
                "response_sha256": hashlib.sha256(body).hexdigest(),
                "content_type": headers.get("content-type"),
            }
            requests.append(record)
            if status != 200:
                errors.append(f"{label}:HTTP_{status}")
                return status, body, None
            if not parse_json:
                return status, body, None
            rows = parse_cdx_rows(body, expected_original=expected_original)
            record["capture_count"] = len(rows)
            return status, body, rows
        except Exception as exc:
            errors.append(f"{label}:{type(exc).__name__}:{exc}")
            requests.append({"label": label, "request_url": url, "error": f"{type(exc).__name__}:{exc}"})
            return 0, b"", None

    index_query = build_cdx_url(LISTING_URL, from_year=2024, to_year=2026, limit=100)
    _, _, listing_index_rows = one("official_listing_cdx_index", index_query, expected_original=LISTING_URL)
    if listing_index_rows is not None:
        listing_index_rows = sorted(listing_index_rows, key=lambda x: x["timestamp"])
    file_results: dict[str, Any] = {}
    for date in FIXED_DATES:
        url = TARGET_URLS[date]
        cdx_url = build_cdx_url(url, from_year=2024, to_year=2026, limit=100)
        _, _, rows = one(f"finra_file_cdx_{date}", cdx_url, expected_original=url)
        file_results[date] = {
            "original_url": url,
            "metadata_capture_count": len(rows) if rows is not None else None,
            "captures": rows or [],
            "capture_query_completed": rows is not None,
        }

    snapshot_results: list[dict[str, Any]] = []
    for timestamp, file_date in ARCHIVE_SNAPSHOTS:
        archived_url = f"https://web.archive.org/web/{timestamp}id_/{LISTING_URL}"
        status, body, _ = one(f"historical_listing_snapshot_{timestamp}", archived_url, parse_json=False)
        filename = f"CNMSshvol{file_date}.txt"
        found = status == 200 and filename.encode("ascii") in body
        snapshot_results.append({
            "capture_timestamp": timestamp,
            "target_file_date": file_date[:4] + "-" + file_date[4:6] + "-" + file_date[6:8],
            "response_status": status,
            "response_bytes": len(body),
            "response_sha256": hashlib.sha256(body).hexdigest() if body else None,
            "target_filename_visible": found,
        })
        if status != 200:
            errors.append(f"historical_listing_snapshot_{timestamp}:HTTP_{status}")
        elif not found:
            errors.append(f"historical_listing_snapshot_{timestamp}:TARGET_FILENAME_NOT_FOUND")

    result: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q127r2_finra_wayback_metadata_probe",
        "candidate_id": "Q127-R2",
        "task_id": "Q-2026-10-13-127R2-FINRA-WAYBACK-METADATA",
        "status": "Q127R2_WAYBACK_METADATA_COMPLETE" if not errors and budget["request_count"] == MAX_REQUESTS else "Q127R2_WAYBACK_METADATA_INCOMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": __import__("os").environ.get("GITHUB_SHA"),
        "upstream": {
            "run_id": 38455702686,
            "artifact_name": R1_RUN_RECEIPT,
            "receipt_fingerprint": source["receipt_fingerprint"],
            "task_id": source["task_id"],
        },
        "fixed_population": {"dates": list(FIXED_DATES), "symbols": list(SYMBOLS), "count": len(FIXED_DATES)},
        "method": {
            "source": "Internet Archive CDX metadata plus two fixed captured versions of the official FINRA archive listing",
            "request_count_cap": MAX_REQUESTS,
            "response_byte_cap": MAX_RESPONSE_BYTES,
            "total_metadata_byte_cap": MAX_TOTAL_BYTES,
            "target_data_files_downloaded": 0,
            "only_metadata_or_small_source_listing_bodies": True,
        },
        "listing_index": {
            "url": LISTING_URL,
            "capture_count": len(listing_index_rows) if listing_index_rows is not None else None,
            "captures": listing_index_rows or [],
            "query_completed": listing_index_rows is not None,
        },
        "fixed_file_observations": file_results,
        "historical_listing_snapshots": snapshot_results,
        "summary": {
            "fixed_target_file_count": len(FIXED_DATES),
            "file_cdx_queries_completed": sum(1 for x in file_results.values() if x["capture_query_completed"]),
            "raw_file_captures_found": sum(x["metadata_capture_count"] or 0 for x in file_results.values()),
            "pinned_listing_snapshots_with_target_filename": sum(1 for x in snapshot_results if x["target_filename_visible"]),
            "metadata_request_count": budget["request_count"],
            "metadata_download_bytes": budget["metadata_download_bytes"],
            "error_count": len(errors),
        },
        "errors": errors,
        "pit": {
            "official_same_trade_date_1800_et_upper_bound_preserved": True,
            "historical_listing_presence_observed_for_two_fixed_files": any(x["target_filename_visible"] for x in snapshot_results),
            "exact_first_publication_time_proven": False,
            "raw_file_historical_bytes_recovered": False,
            "original_vs_updated_file_lineage_proven": False,
            "same_day_formal_use_allowed": False,
        },
        "scientific_boundary": {
            "performance": False, "holdout": False, "ranking": False, "selection": False,
            "parameter_search": False, "threshold_search": False, "horizon_search": False,
            "asset_search": False, "variant_search": False, "performance_authorized": False,
            "promotion": False, "live_execution": False,
        },
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
        "interpretation": (
            "CDX records and archived FINRA listing entries are metadata/provenance leads only. A listing snapshot can prove that a filename was visible by capture time, not the exact first-publication time or the original file bytes. No CDX hit is not proof that a file was never public."
        ),
    }
    result["receipt_fingerprint"] = canonical_fingerprint(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.request, args.source_receipt, args.output)
    print(json.dumps({
        "status": result["status"],
        "metadata_request_count": result["summary"]["metadata_request_count"],
        "raw_file_captures_found": result["summary"]["raw_file_captures_found"],
        "listing_snapshots_with_target_filename": result["summary"]["pinned_listing_snapshots_with_target_filename"],
        "metadata_download_bytes": result["summary"]["metadata_download_bytes"],
        "gate_positive": False,
        "performance_authorized": False,
        "live_execution": False,
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
