"""Inventory dated USAspending contract archives for the frozen Q221 sample.

This is a source-feasibility probe only. It lists archive metadata and does not
download ZIPs, infer transaction publication time, read market outcomes, or
authorize performance. A dated archive series is only a candidate for the next
transaction-presence experiment; all event-level PIT gates remain closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

API_URL = "https://api.usaspending.gov/api/v2/bulk_download/list_monthly_files/"
USER_AGENT = "TradingAgent-Public-Q221-Archive-Inventory/1.0"
SOURCE_CODE_COMMIT = "03b9e2554837998c4c261c65e2947dc79f23855a"
SOURCE_IMPL_URL = (
    "https://github.com/fedspendingtransparency/usaspending-api/blob/"
    + SOURCE_CODE_COMMIT
    + "/usaspending_api/download/v2/list_monthly_downloads.py"
)
SOURCE_CONTRACT_URL = (
    "https://github.com/fedspendingtransparency/usaspending-api/blob/"
    + SOURCE_CODE_COMMIT
    + "/usaspending_api/api_contracts/contracts/v2/bulk_download/list_monthly_files.md"
)
MAX_RESPONSE_BYTES = 5_000_000
MAX_FISCAL_YEARS = 10
REQUEST_TIMEOUT_SECONDS = 30

FULL_RE = re.compile(r"^FY(?P<year>\d{4})_All_Contracts_Full_(?P<stamp>\d{8})\.zip$")
DELTA_RE = re.compile(r"^FY\(All\)_All_Contracts_Delta_(?P<stamp>\d{8})\.zip$")


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _parse_manifest(manifest: dict[str, Any]) -> tuple[dict[int, set[str]], list[str]]:
    """Read only fixed transaction keys already recorded in the Q221 receipt.

    Action dates partition the candidate archive fiscal year only. They are
    never interpreted as a public-observation timestamp.
    """
    queries = manifest.get("queries")
    if not isinstance(queries, list):
        return {}, ["manifest has no queries array"]

    by_fy: dict[int, set[str]] = {}
    errors: list[str] = []
    key_count = 0
    for query_index, query in enumerate(queries):
        if not isinstance(query, dict):
            errors.append(f"queries[{query_index}] is not an object")
            continue
        keys = query.get("selected_transaction_keys")
        if not isinstance(keys, list):
            errors.append(f"queries[{query_index}] has no selected_transaction_keys array")
            continue
        for key_index, raw_key in enumerate(keys):
            if not isinstance(raw_key, str):
                errors.append(f"queries[{query_index}].selected_transaction_keys[{key_index}] is not text")
                continue
            parts = raw_key.split("|")
            if len(parts) != 5:
                errors.append(f"malformed frozen transaction key at queries[{query_index}][{key_index}]")
                continue
            try:
                action_day = date.fromisoformat(parts[2])
            except ValueError:
                errors.append(f"invalid action-date component at queries[{query_index}][{key_index}]")
                continue
            # Federal fiscal year changes on October 1. This only selects
            # archive partitions; it is not treated as public availability.
            fiscal_year = action_day.year + int(action_day.month >= 10)
            by_fy.setdefault(fiscal_year, set()).add(raw_key)
            key_count += 1

    if key_count == 0:
        errors.append("no valid frozen transaction keys found")
    if len(by_fy) > MAX_FISCAL_YEARS:
        errors.append(f"target spans {len(by_fy)} fiscal years; bound is {MAX_FISCAL_YEARS}")
    return by_fy, errors


# One-shot request pins the current Q221 manifest; updating it requires an explicit re-registration.
FROZEN_MANIFEST_PATH = "research/evidence/q221_historical_public_boundary_latest.json"
FROZEN_MANIFEST_GIT_BLOB_SHA = "b78cf6f7b48af3f914ee7c6d06a38f6485b0438f"
FROZEN_MANIFEST_RECEIPT_FINGERPRINT = "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
FROZEN_TARGET_KEY_COUNTS_BY_FY = {2019: 49, 2020: 50, 2021: 50, 2022: 50, 2023: 50, 2024: 49, 2025: 50}
FROZEN_REQUEST_VALUES = {
    "RUN_Q221_MONTHLY_ARCHIVE_INVENTORY": "true",
    "REASON": "VERSIONED_ARCHIVE_CATALOG_INVENTORY_FOR_FROZEN_Q221_SAMPLE",
    "SOURCE_MANIFEST_PATH": FROZEN_MANIFEST_PATH,
    "SOURCE_MANIFEST_GIT_BLOB_SHA": FROZEN_MANIFEST_GIT_BLOB_SHA,
    "SOURCE_MANIFEST_RECEIPT_FINGERPRINT": FROZEN_MANIFEST_RECEIPT_FINGERPRINT,
    "TARGET_KEY_COUNT": "348",
    "TARGET_FISCAL_YEARS": "2019,2020,2021,2022,2023,2024,2025",
    "TARGET_KEY_COUNTS_BY_FY": "2019:49,2020:50,2021:50,2022:50,2023:50,2024:49,2025:50",
    "MAX_FISCAL_YEARS": "7",
    "CENSUS_RESTART": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}
REQUEST_KEYS = set(FROZEN_REQUEST_VALUES) | {"REQUEST_SEQUENCE"}


def _git_blob_sha1(body: bytes) -> str:
    header = b"blob " + str(len(body)).encode("ascii") + b"\0"
    return hashlib.sha1(header + body).hexdigest()


def _read_key_value_request(request_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    raw = request_path.read_text(encoding="utf-8")
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line or line.strip() != line or "=" not in line:
            raise ValueError(f"Q221_REQUEST_INVALID_LINE:{line_number}")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key) or not value:
            raise ValueError(f"Q221_REQUEST_INVALID_KEY_VALUE:{line_number}")
        if key in values:
            raise ValueError(f"Q221_REQUEST_DUPLICATE_KEY:{key}")
        values[key] = value
    if set(values) != REQUEST_KEYS:
        missing = sorted(REQUEST_KEYS - set(values))
        extra = sorted(set(values) - REQUEST_KEYS)
        raise ValueError(f"Q221_REQUEST_KEY_SET_MISMATCH:missing={missing}:extra={extra}")
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values["REQUEST_SEQUENCE"]):
        raise ValueError("Q221_REQUEST_SEQUENCE_INVALID")
    for key, expected in FROZEN_REQUEST_VALUES.items():
        if values[key] != expected:
            raise ValueError(f"Q221_REQUEST_VALUE_MISMATCH:{key}")
    return values


def validate_request(request_path: Path, input_path: Path) -> dict[str, Any]:
    """Fail closed unless the request matches the frozen 348-key Q221 manifest."""
    values = _read_key_value_request(request_path)
    raw = input_path.read_bytes()
    actual_blob_sha = _git_blob_sha1(raw)
    if actual_blob_sha != values["SOURCE_MANIFEST_GIT_BLOB_SHA"]:
        raise ValueError("Q221_SOURCE_MANIFEST_GIT_BLOB_SHA_MISMATCH:" + actual_blob_sha)
    manifest = json.loads(raw.decode("utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Q221_SOURCE_MANIFEST_ROOT_INVALID")
    if manifest.get("receipt_fingerprint") != values["SOURCE_MANIFEST_RECEIPT_FINGERPRINT"]:
        raise ValueError("Q221_SOURCE_MANIFEST_RECEIPT_FINGERPRINT_MISMATCH")
    if manifest.get("candidate_id") != "Q221":
        raise ValueError("Q221_SOURCE_MANIFEST_CANDIDATE_MISMATCH")
    if manifest.get("gate_positive") is not False:
        raise ValueError("Q221_SOURCE_MANIFEST_GATE_MUST_REMAIN_NEGATIVE")
    if manifest.get("historical_first_public_observation_proven") is not False:
        raise ValueError("Q221_SOURCE_MANIFEST_PUBLIC_CLOCK_GATE_MUST_REMAIN_NEGATIVE")
    if manifest.get("event_level_public_boundary_proven") is not False:
        raise ValueError("Q221_SOURCE_MANIFEST_EVENT_BOUNDARY_GATE_MUST_REMAIN_NEGATIVE")
    if manifest.get("action_date_is_not_public_observation_time") is not True:
        raise ValueError("Q221_ACTION_DATE_PUBLIC_CLOCK_GUARD_MISSING")
    targets, errors = _parse_manifest(manifest)
    if errors:
        raise ValueError("Q221_SOURCE_MANIFEST_INVALID:" + ";".join(errors[:5]))
    raw_keys = [
        key
        for query in manifest["queries"]
        for key in query.get("selected_transaction_keys", [])
    ]
    if len(raw_keys) != int(values["TARGET_KEY_COUNT"]) or len(set(raw_keys)) != len(raw_keys):
        raise ValueError("Q221_TARGET_KEY_COUNT_OR_DUPLICATE_MISMATCH")
    actual_years = sorted(targets)
    expected_years = [int(x) for x in values["TARGET_FISCAL_YEARS"].split(",")]
    if actual_years != expected_years or len(actual_years) > int(values["MAX_FISCAL_YEARS"]):
        raise ValueError("Q221_TARGET_FISCAL_YEAR_SET_MISMATCH")
    expected_counts = {
        int(pair.split(":")[0]): int(pair.split(":")[1])
        for pair in values["TARGET_KEY_COUNTS_BY_FY"].split(",")
    }
    actual_counts = {year: len(keys) for year, keys in targets.items()}
    if actual_counts != expected_counts:
        raise ValueError("Q221_TARGET_FISCAL_YEAR_COUNTS_MISMATCH")
    return {
        "request_sequence": values["REQUEST_SEQUENCE"],
        "source_manifest_path": values["SOURCE_MANIFEST_PATH"],
        "source_manifest_git_blob_sha": actual_blob_sha,
        "source_manifest_receipt_fingerprint": manifest["receipt_fingerprint"],
        "target_key_count": len(raw_keys),
        "target_fiscal_years": actual_years,
        "target_key_counts_by_fiscal_year": {str(year): actual_counts[year] for year in actual_years},
        "request_valid": True,
    }


def request_inventory(fiscal_year: int) -> tuple[int, str, bytes, dict[str, Any]]:
    """Make one bounded read-only catalog POST; never fetch an archive payload."""
    payload = json.dumps({
        "agency": "all",
        "fiscal_year": fiscal_year,
        "type": "contracts",
    }, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ValueError(f"inventory response exceeded {MAX_RESPONSE_BYTES} bytes")
        status = int(getattr(response, "status", 200))
        content_type = str(response.headers.get("Content-Type", ""))
    decoded = json.loads(body.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("inventory response is not a JSON object")
    return status, content_type, body, decoded


def _normalise_items(
    fiscal_year: int, rows: list[Any]
) -> tuple[list[dict[str, Any]], list[str]]:
    items: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"monthly_files[{index}] is not an object")
            continue
        name = row.get("file_name")
        updated = row.get("updated_date")
        url = row.get("url")
        if not all(isinstance(x, str) and x for x in (name, updated, url)):
            errors.append(f"monthly_files[{index}] misses file_name, updated_date, or url")
            continue

        match = FULL_RE.fullmatch(name)
        kind = "full"
        if match:
            if int(match.group("year")) != fiscal_year:
                errors.append(f"full archive filename has unexpected fiscal year: {name}")
                continue
        else:
            match = DELTA_RE.fullmatch(name)
            kind = "delta"
        if not match:
            errors.append(f"unrecognised archive filename: {name}")
            continue

        stamp = match.group("stamp")
        try:
            filename_date = datetime.strptime(stamp, "%Y%m%d").date().isoformat()
            published_date = date.fromisoformat(updated).isoformat()
        except ValueError:
            errors.append(f"invalid archive date in {name}")
            continue
        if filename_date != published_date:
            errors.append(f"filename date and updated_date disagree for {name}")
            continue

        parsed_url = urlparse(url)
        host = (parsed_url.hostname or "").lower()
        if (
            parsed_url.scheme != "https"
            or not host
            or not (host == "usaspending.gov" or host.endswith(".usaspending.gov"))
            or parsed_url.username is not None
            or parsed_url.password is not None
        ):
            errors.append(f"archive URL is not a trusted HTTPS USAspending URL for {name}")
            continue
        items.append({
            "file_name": name,
            "kind": kind,
            "updated_date": published_date,
            "url": url,
            "url_host": parsed_url.hostname.lower(),
        })
    return sorted(items, key=lambda x: (x["updated_date"], x["kind"], x["file_name"])), errors


def _write(output: Path, receipt: dict[str, Any]) -> None:
    without_fingerprint = dict(receipt)
    without_fingerprint.pop("receipt_fingerprint", None)
    canonical = json.dumps(
        without_fingerprint, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    receipt["receipt_fingerprint"] = _sha256(canonical.encode("utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run(input_path: Path, output_path: Path, request_path: Path | None = None) -> dict[str, Any]:
    """Write a machine-readable, fail-closed inventory receipt on all outcomes."""
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q221_monthly_archive_inventory_probe",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "Q221",
        "api_endpoint": API_URL,
        "source_implementation_url": SOURCE_IMPL_URL,
        "source_contract_url": SOURCE_CONTRACT_URL,
        "source_code_commit": SOURCE_CODE_COMMIT,
        "max_response_bytes": MAX_RESPONSE_BYTES,
        "max_fiscal_years": MAX_FISCAL_YEARS,
        "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "request_mode": "READ_ONLY_METADATA_POST; NO_ARCHIVE_PAYLOADS_DOWNLOADED",
        "input_manifest_path": input_path.as_posix(),
        "request_validation_required": request_path is not None,
        "request_validation_passed": False,
        "source_manifest_git_blob_sha": None,
        "source_manifest_receipt_fingerprint": None,
        "request_sequence": None,
        "target_fiscal_years": [],
        "target_key_counts_by_fiscal_year": {},
        "target_key_hashes_by_fiscal_year": {},
        "fiscal_year_results": [],
        "archive_item_count": 0,
        "full_archive_count": 0,
        "delta_archive_count": 0,
        "dated_archive_series_found": False,
        "archive_transaction_presence_tested": False,
        "archive_transaction_absence_tested": False,
        "historical_first_public_observation_proven": False,
        "event_level_public_boundary_proven": False,
        "historical_applicability_proven": False,
        "recipient_to_issuer_mapping_frozen": False,
        "lookahead_used": False,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
    }

    if request_path is not None:
        try:
            request_receipt = validate_request(request_path, input_path)
            receipt.update({
                "request_validation_passed": True,
                "source_manifest_git_blob_sha": request_receipt["source_manifest_git_blob_sha"],
                "source_manifest_receipt_fingerprint": request_receipt["source_manifest_receipt_fingerprint"],
                "request_sequence": request_receipt["request_sequence"],
                "frozen_request_validation": request_receipt,
            })
        except Exception as exc:
            receipt.update({
                "status": "REQUEST_REJECTED",
                "request_validation_passed": False,
                "error": f"{type(exc).__name__}: {exc}"[:500],
                "next_gate": "repair or explicitly re-register the frozen Q221 request; no API request was made",
            })
            _write(output_path, receipt)
            return receipt

    try:
        raw_manifest = input_path.read_bytes()
        receipt["input_manifest_sha256"] = _sha256(raw_manifest)
        manifest = json.loads(raw_manifest.decode("utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest root is not a JSON object")
    except Exception as exc:
        receipt.update({
            "status": "FIXED_TRANSACTION_MANIFEST_UNAVAILABLE_OR_INVALID",
            "error": f"{type(exc).__name__}: {exc}"[:500],
            "next_gate": "repair the fixed public-boundary receipt input; do not infer source-clock readiness",
        })
        _write(output_path, receipt)
        return receipt

    targets, parse_errors = _parse_manifest(manifest)
    receipt["target_fiscal_years"] = sorted(targets)
    receipt["target_key_counts_by_fiscal_year"] = {
        str(year): len(targets[year]) for year in sorted(targets)
    }
    receipt["target_key_hashes_by_fiscal_year"] = {
        str(year): _sha256("\n".join(sorted(targets[year])).encode("utf-8"))
        for year in sorted(targets)
    }
    if parse_errors:
        receipt.update({
            "status": "FIXED_TRANSACTION_MANIFEST_INVALID",
            "manifest_errors": parse_errors[:50],
            "next_gate": "repair the fixed key schema/coverage before querying an archive; do not silently drop keys",
        })
        _write(output_path, receipt)
        return receipt

    year_results: list[dict[str, Any]] = []
    any_request_error = False
    any_shape_error = False
    for fiscal_year in sorted(targets):
        year_receipt: dict[str, Any] = {
            "fiscal_year": fiscal_year,
            "target_key_count": len(targets[fiscal_year]),
            "http_status": None,
            "content_type": None,
            "response_sha256": None,
            "response_bytes": None,
            "full_archive_count": 0,
            "delta_archive_count": 0,
            "full_archive_dates": [],
            "delta_archive_dates": [],
            "archive_items": [],
            "status": "NOT_QUERIED",
        }
        try:
            status, content_type, body, decoded = request_inventory(fiscal_year)
            year_receipt.update({
                "http_status": status,
                "content_type": content_type,
                "response_sha256": _sha256(body),
                "response_bytes": len(body),
            })
            rows = decoded.get("monthly_files")
            if status != 200 or not isinstance(rows, list):
                any_shape_error = True
                year_receipt.update({
                    "status": "INVALID_HTTP_STATUS_OR_RESPONSE_SHAPE",
                    "error": f"HTTP {status}; monthly_files is {type(rows).__name__}",
                })
                year_results.append(year_receipt)
                continue
            items, item_errors = _normalise_items(fiscal_year, rows)
            if item_errors:
                any_shape_error = True
            full_items = [x for x in items if x["kind"] == "full"]
            delta_items = [x for x in items if x["kind"] == "delta"]
            year_receipt.update({
                "full_archive_count": len(full_items),
                "delta_archive_count": len(delta_items),
                "full_archive_dates": sorted({x["updated_date"] for x in full_items}),
                "delta_archive_dates": sorted({x["updated_date"] for x in delta_items}),
                "archive_items": items,
                "invalid_item_count": len(item_errors),
                "invalid_item_examples": item_errors[:20],
                "status": "CATALOG_PARSED" if not item_errors else "CATALOG_HAS_INVALID_ITEMS",
            })
        except Exception as exc:
            any_request_error = True
            year_receipt.update({
                "status": "REQUEST_OR_JSON_PARSE_FAILED",
                "error": f"{type(exc).__name__}: {exc}"[:500],
            })
        year_results.append(year_receipt)

    receipt["fiscal_year_results"] = year_results
    all_items = [item for row in year_results for item in row.get("archive_items", [])]
    receipt["archive_item_count"] = len(all_items)
    receipt["full_archive_count"] = sum(row.get("full_archive_count", 0) for row in year_results)
    receipt["delta_archive_count"] = sum(row.get("delta_archive_count", 0) for row in year_results)
    receipt["dated_archive_series_found"] = any(
        len(row.get("full_archive_dates", [])) >= 2
        or len(row.get("delta_archive_dates", [])) >= 2
        for row in year_results
    )
    every_year_parsed = all(row.get("status") == "CATALOG_PARSED" for row in year_results)

    if any_request_error or any_shape_error or not every_year_parsed:
        status = "ARCHIVE_LISTING_INCOMPLETE"
        next_gate = "diagnose the bounded catalog/API errors; do not treat partial archive inventory as evidence"
    elif not all_items:
        status = "ARCHIVE_LISTING_EMPTY"
        next_gate = "no matching contract archive metadata was listed; investigate source availability before any transaction-clock inference"
    elif receipt["dated_archive_series_found"]:
        status = "DATED_ARCHIVE_SERIES_FOUND"
        next_gate = (
            "run a separate bounded row-presence test on fixed transaction keys against selected archive versions; "
            "even a first archive appearance is not itself proof of first API/UI publication"
        )
    else:
        status = "ARCHIVE_LISTING_OK_NO_VERSION_SERIES_FOUND"
        next_gate = (
            "no multi-date archive family was observed for these years; do not download broad archives or infer a PIT boundary"
        )

    receipt.update({
        "status": status,
        "next_gate": next_gate,
        "archive_transaction_presence_tested": False,
        "archive_transaction_absence_tested": False,
        "historical_first_public_observation_proven": False,
        "event_level_public_boundary_proven": False,
        "historical_applicability_proven": False,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
    })
    _write(output_path, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("research/evidence/q221_historical_public_boundary_latest.json"),
        help="frozen Q221 public-boundary receipt",
    )
    parser.add_argument("--output", type=Path, required=True, help="path for the inventory receipt")
    parser.add_argument("--request", type=Path, help="explicit frozen one-shot request file")
    args = parser.parse_args()
    receipt = run(args.input, args.output, request_path=args.request)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("status") == "DATED_ARCHIVE_SERIES_FOUND" else 2


if __name__ == "__main__":
    raise SystemExit(main())
