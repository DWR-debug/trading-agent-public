"""Bounded Q220 HTTP-response representation sensitivity probe.

Fetch exactly five copies of one frozen SEC primary document using one-variable
request-profile contrasts. This tests whether request headers or response
repeatability can explain the existing 55/55 source-hash mismatch. It never
stores document bodies, changes frozen hashes, or clears any research gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RECEIPT_PATH = "research/fixtures/q220_historical_representation_pit_2026-10-12T071514Z.json"
SOURCE_RECEIPT_GIT_BLOB_SHA = "2a3abbff6c6950e4f11d85dba92cb9c57a5c7ee0"
SOURCE_RECEIPT_FINGERPRINT = "c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075"
SOURCE_POPULATION_RECEIPT_FINGERPRINT = "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543"
SOURCE_HASH_FAILURE_COUNT = 55
SINGLE_SUMMARY_PATH = "research/evidence/q220_single_feed_boundary_validation_2026_10_13_summary.json"
SINGLE_SUMMARY_GIT_BLOB_SHA = "807f6796a0f84b27ab04160e944bdfdaec85525b"
SINGLE_SUMMARY_UPSTREAM_RECEIPT_FINGERPRINT = "fe98cecb579d15ecf6e48c3b84a3a699345bf840745e9be0c7cfcd972aebf03a"
TARGET_RECORD_KEY = "0000064040|0000064040-19-000059|10-K|2019-02-13"
EXPECTED_SHA256 = "27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83"
EXPECTED_BYTES = 4_774_458
FROZEN_CAPTURED_SHA256 = "08039132d6d6d1692d1f7552193c70a04cad4c1dcadad1cfa3ca2b8b4efe3fdb"
FROZEN_CAPTURED_BYTES = 4_774_458
SINGLE_FEED_RAW_BODY_SHA256 = "aa1f89efdf13029de9dd8f7eb020502dd518d4350513d4ef041ba67d902ef368"
SINGLE_FEED_RAW_BODY_BYTES = 4_774_237
PRIMARY_FILENAME = "spgi-20181231x10k.htm"
FILING_DATE = "2019-02-13"
INDEX_PRIMARY_EXPECTED_BYTES = 4_774_347
PRIOR_COMPLETE_SUBMISSION_RUN_ID = "38448795085"
PRIOR_COMPLETE_SUBMISSION_ARTIFACT_ID = "11840230646"
PRIOR_COMPLETE_SUBMISSION_RECEIPT_FINGERPRINT = "8de11ae16d336fb50c066ec6c4c77c17a7670116a5d8205c143eeff650186303"
PRIOR_CURRENT_PRIMARY_SHA256 = "2693819652172f0c218394ef036eb3f4af95c2a7077f624f6efcd990df370172"
PRIOR_CURRENT_PRIMARY_BYTES = 4_774_465

MAX_REQUESTS = 5
MAX_RESPONSE_BYTES = 5_900_000
MAX_TOTAL_DOWNLOAD_BYTES = 30_000_000
REQUEST_TIMEOUT_SECONDS = 60
REQUEST_GAP_SECONDS = 1.0
URL = "https://www.sec.gov/Archives/edgar/data/64040/000006404019000059/spgi-20181231x10k.htm"
UA_POPULATION = "DWR-debug/trading-agent-public Q220 as-filed XBRL repair/1.0 research@example.invalid"
UA_PIT = "DWR-debug/trading-agent-public Q220 historical representation PIT/1.0 research@example.invalid"
UA_FORENSIC = "DWR-debug/trading-agent-public Q220 SEC Feed forensic research@example.invalid"
ACCEPT_POPULATION = "text/html,text/plain,application/json,application/xml,*/*"
ACCEPT_PIT = "text/html,application/xhtml+xml,*/*"
ACCEPT_FORENSIC = "text/html,text/plain,application/gzip,application/x-gzip,*/*"

FROZEN_REQUEST_VALUES = {
    "RUN_Q220_HTTP_REPRESENTATION_SENSITIVITY": "true",
    "REASON": "TEST_FIXED_SEC_PRIMARY_HTTP_RESPONSE_REPRESENTATION_AND_REPEATABILITY",
    "SOURCE_RECEIPT_PATH": SOURCE_RECEIPT_PATH,
    "SOURCE_RECEIPT_GIT_BLOB_SHA": SOURCE_RECEIPT_GIT_BLOB_SHA,
    "SOURCE_RECEIPT_FINGERPRINT": SOURCE_RECEIPT_FINGERPRINT,
    "SOURCE_POPULATION_RECEIPT_FINGERPRINT": SOURCE_POPULATION_RECEIPT_FINGERPRINT,
    "SOURCE_HASH_FAILURE_COUNT": str(SOURCE_HASH_FAILURE_COUNT),
    "SINGLE_SUMMARY_PATH": SINGLE_SUMMARY_PATH,
    "SINGLE_SUMMARY_GIT_BLOB_SHA": SINGLE_SUMMARY_GIT_BLOB_SHA,
    "SINGLE_SUMMARY_UPSTREAM_RECEIPT_FINGERPRINT": SINGLE_SUMMARY_UPSTREAM_RECEIPT_FINGERPRINT,
    "TARGET_RECORD_KEY": TARGET_RECORD_KEY,
    "EXPECTED_SHA256": EXPECTED_SHA256,
    "EXPECTED_BYTES": str(EXPECTED_BYTES),
    "FROZEN_CAPTURED_SHA256": FROZEN_CAPTURED_SHA256,
    "FROZEN_CAPTURED_BYTES": str(FROZEN_CAPTURED_BYTES),
    "SINGLE_FEED_RAW_BODY_SHA256": SINGLE_FEED_RAW_BODY_SHA256,
    "SINGLE_FEED_RAW_BODY_BYTES": str(SINGLE_FEED_RAW_BODY_BYTES),
    "PRIMARY_FILENAME": PRIMARY_FILENAME,
    "FILING_DATE": FILING_DATE,
    "INDEX_PRIMARY_EXPECTED_BYTES": str(INDEX_PRIMARY_EXPECTED_BYTES),
    "PRIOR_COMPLETE_SUBMISSION_RUN_ID": PRIOR_COMPLETE_SUBMISSION_RUN_ID,
    "PRIOR_COMPLETE_SUBMISSION_ARTIFACT_ID": PRIOR_COMPLETE_SUBMISSION_ARTIFACT_ID,
    "PRIOR_COMPLETE_SUBMISSION_RECEIPT_FINGERPRINT": PRIOR_COMPLETE_SUBMISSION_RECEIPT_FINGERPRINT,
    "PRIOR_CURRENT_PRIMARY_SHA256": PRIOR_CURRENT_PRIMARY_SHA256,
    "PRIOR_CURRENT_PRIMARY_BYTES": str(PRIOR_CURRENT_PRIMARY_BYTES),
    "MAX_REQUESTS": str(MAX_REQUESTS),
    "MAX_RESPONSE_BYTES": str(MAX_RESPONSE_BYTES),
    "MAX_TOTAL_DOWNLOAD_BYTES": str(MAX_TOTAL_DOWNLOAD_BYTES),
    "REQUEST_TIMEOUT_SECONDS": str(REQUEST_TIMEOUT_SECONDS),
    "REQUEST_GAP_SECONDS": str(REQUEST_GAP_SECONDS),
    "CENSUS_RESTART": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}
REQUEST_KEYS = set(FROZEN_REQUEST_VALUES) | {"REQUEST_SEQUENCE"}

PROFILES = (
    {
        "name": "population_baseline_first",
        "user_agent_profile": "population",
        "accept_profile": "population",
        "user_agent": UA_POPULATION,
        "accept": ACCEPT_POPULATION,
    },
    {
        "name": "pit_user_agent_only",
        "user_agent_profile": "pit",
        "accept_profile": "population",
        "user_agent": UA_PIT,
        "accept": ACCEPT_POPULATION,
    },
    {
        "name": "pit_accept_only",
        "user_agent_profile": "population",
        "accept_profile": "pit",
        "user_agent": UA_POPULATION,
        "accept": ACCEPT_PIT,
    },
    {
        "name": "forensic_combined_profile",
        "user_agent_profile": "forensic",
        "accept_profile": "forensic",
        "user_agent": UA_FORENSIC,
        "accept": ACCEPT_FORENSIC,
    },
    {
        "name": "population_baseline_repeat",
        "user_agent_profile": "population",
        "accept_profile": "population",
        "user_agent": UA_POPULATION,
        "accept": ACCEPT_POPULATION,
    },
)


class ProbeError(ValueError):
    """A frozen input, HTTP response, or bounded-work contract is invalid."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def canonical_fingerprint(value: dict[str, Any], field: str = "receipt_fingerprint") -> str:
    payload = dict(value)
    payload.pop(field, None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded)


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ProbeError(f"REQUEST_LINE_INVALID:{number}")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or key in values:
            raise ProbeError(f"REQUEST_KEY_EMPTY_OR_DUPLICATE:{number}:{key}")
        values[key] = value
    if set(values) != REQUEST_KEYS:
        raise ProbeError("REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN_REQUEST_VALUES.items():
        if values.get(key) != expected:
            raise ProbeError("REQUEST_VALUE_MISMATCH:" + key)
    sequence = values.get("REQUEST_SEQUENCE", "")
    try:
        parsed = datetime.fromisoformat(sequence.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProbeError("REQUEST_SEQUENCE_INVALID") from exc
    if not sequence.endswith("Z") or parsed.tzinfo is None:
        raise ProbeError("REQUEST_SEQUENCE_MUST_BE_UTC_Z")
    return values


def _source_error_field(error: str, key: str) -> str | None:
    match = re.search(r"(?:^|:)" + re.escape(key) + r"=([^:]+)(?:$|:)", error)
    return match.group(1) if match else None


def validate_sources(
    source_path: Path,
    summary_path: Path,
    request: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_raw = source_path.read_bytes()
    if git_blob_sha1(source_raw) != request["SOURCE_RECEIPT_GIT_BLOB_SHA"]:
        raise ProbeError("SOURCE_RECEIPT_BLOB_SHA_MISMATCH")
    source = json.loads(source_raw.decode("utf-8"))
    if canonical_fingerprint(source) != request["SOURCE_RECEIPT_FINGERPRINT"]:
        raise ProbeError("SOURCE_RECEIPT_FINGERPRINT_MISMATCH")
    if (
        source.get("candidate_id") != "Q220"
        or source.get("status") != "Q220_HISTORICAL_REPRESENTATION_PIT_BLOCKED"
        or source.get("gate_positive") is not False
        or source.get("source_hash_failure_count") != SOURCE_HASH_FAILURE_COUNT
        or source.get("source_population_receipt_fingerprint") != SOURCE_POPULATION_RECEIPT_FINGERPRINT
    ):
        raise ProbeError("SOURCE_RECEIPT_STATE_MISMATCH")
    failure_rows = source.get("source_hash_failures")
    if not isinstance(failure_rows, list) or len(failure_rows) != SOURCE_HASH_FAILURE_COUNT:
        raise ProbeError("SOURCE_FAILURE_ROWS_MISMATCH")
    matches = [row for row in failure_rows if row.get("record_key") == TARGET_RECORD_KEY]
    if len(matches) != 1:
        raise ProbeError("TARGET_RECORD_KEY_NOT_UNIQUE_IN_FROZEN_FAILURES")
    source_error = str(matches[0].get("error") or "")
    expected_fields = {
        "expected": EXPECTED_SHA256,
        "actual": FROZEN_CAPTURED_SHA256,
        "expected_bytes": str(EXPECTED_BYTES),
        "actual_bytes": str(FROZEN_CAPTURED_BYTES),
        "primary": PRIMARY_FILENAME,
    }
    for key, expected in expected_fields.items():
        if _source_error_field(source_error, key) != expected:
            raise ProbeError("FROZEN_SOURCE_FIELD_MISMATCH:" + key)

    summary_raw = summary_path.read_bytes()
    if git_blob_sha1(summary_raw) != request["SINGLE_SUMMARY_GIT_BLOB_SHA"]:
        raise ProbeError("SINGLE_SUMMARY_BLOB_SHA_MISMATCH")
    summary = json.loads(summary_raw.decode("utf-8"))
    if (
        summary.get("record_type") != "q220_single_feed_boundary_validation_summary"
        or summary.get("candidate_id") != "Q220"
        or summary.get("status") != "SINGLE_FEED_BOUNDARY_COMPARISON_COMPLETE"
        or summary.get("upstream_receipt_fingerprint") != request["SINGLE_SUMMARY_UPSTREAM_RECEIPT_FINGERPRINT"]
    ):
        raise ProbeError("SINGLE_SUMMARY_IDENTITY_MISMATCH")
    frozen = summary.get("frozen_source") or {}
    frozen_pins = {
        "fixture_git_blob_sha1": SOURCE_RECEIPT_GIT_BLOB_SHA,
        "source_receipt_fingerprint": SOURCE_RECEIPT_FINGERPRINT,
        "population_receipt_fingerprint": SOURCE_POPULATION_RECEIPT_FINGERPRINT,
        "expected_hash_failure_count": SOURCE_HASH_FAILURE_COUNT,
        "record_key": TARGET_RECORD_KEY,
        "primary_filename": PRIMARY_FILENAME,
        "expected_sha256": EXPECTED_SHA256,
        "expected_bytes": EXPECTED_BYTES,
        "previously_captured_sha256": FROZEN_CAPTURED_SHA256,
        "previously_captured_bytes": FROZEN_CAPTURED_BYTES,
    }
    for key, expected in frozen_pins.items():
        if frozen.get(key) != expected:
            raise ProbeError("SINGLE_SUMMARY_FROZEN_PIN_MISMATCH:" + key)
    bounded = summary.get("bounded_run") or {}
    bounded_pins = {
        "current_primary_response_bytes": PRIOR_CURRENT_PRIMARY_BYTES,
        "current_primary_sha256": PRIOR_CURRENT_PRIMARY_SHA256,
        "current_primary_http_status": 200,
        "feed_archive_bytes": 865_768_653,
        "total_source_download_bytes": 870_543_118,
        "scan_complete": True,
    }
    for key, expected in bounded_pins.items():
        if bounded.get(key) != expected:
            raise ProbeError("SINGLE_SUMMARY_BOUNDED_PIN_MISMATCH:" + key)
    extraction = summary.get("extraction") or {}
    if (
        extraction.get("raw_text_block_sha256") != SINGLE_FEED_RAW_BODY_SHA256
        or extraction.get("raw_text_block_bytes") != SINGLE_FEED_RAW_BODY_BYTES
        or extraction.get("frozen_expected_hash_match_count") != 0
    ):
        raise ProbeError("SINGLE_SUMMARY_EXTRACTION_PIN_MISMATCH")
    identity = summary.get("identity_checks") or {}
    required_true = (
        "accession_matches",
        "filer_cik_matches_company_cik",
        "form_matches",
        "filing_date_matches",
        "pds_control_block_valid",
        "pds_control_block_accession_matches",
        "pds_control_block_submission_type_matches_sgml",
        "sgml_control_block_conflict_absent",
    )
    if any(identity.get(key) is not True for key in required_true):
        raise ProbeError("SINGLE_SUMMARY_SOURCE_IDENTITY_NOT_VALID")
    interpretation = summary.get("interpretation") or {}
    for key in (
        "frozen_expected_hash_reproduced",
        "source_vintage_proven",
        "historical_first_public_observation_proven",
        "gate_positive",
        "scientific_evidence",
        "performance_authorization",
        "holdout_selection",
        "ranking",
        "tuning",
        "promotion",
        "live_execution",
    ):
        if interpretation.get(key) is not False:
            raise ProbeError("SINGLE_SUMMARY_GATE_NOT_CLOSED:" + key)
    return source, summary


def request_headers(profile: dict[str, str]) -> dict[str, str]:
    return {
        "User-Agent": profile["user_agent"],
        "Accept": profile["accept"],
        "Accept-Encoding": "identity",
    }


def _response_metadata(headers: Any) -> dict[str, str | None]:
    def value(name: str) -> str | None:
        got = headers.get(name) if headers is not None else None
        return str(got) if got is not None else None

    return {
        "content_type": value("Content-Type"),
        "content_length_header": value("Content-Length"),
        "content_encoding": value("Content-Encoding"),
        "transfer_encoding": value("Transfer-Encoding"),
        "etag": value("ETag"),
        "last_modified": value("Last-Modified"),
        "date": value("Date"),
        "server": value("Server"),
        "accept_ranges": value("Accept-Ranges"),
    }


def default_fetch(
    url: str,
    headers: dict[str, str],
    max_bytes: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            http_status = int(getattr(response, "status", 200))
            response_headers = getattr(response, "headers", {})
            metadata = _response_metadata(response_headers)
            declared = metadata.get("content_length_header")
            if declared and declared.isdigit() and int(declared) > max_bytes:
                return {
                    "status": "DECLARED_LENGTH_OVER_LIMIT",
                    "http_status": http_status,
                    "requested_url": url,
                    "final_url": str(response.geturl()),
                    "response_bytes": 0,
                    "body": b"",
                    "error_code": "CONTENT_LENGTH_OVER_LIMIT",
                    **metadata,
                }
            body = response.read(max_bytes + 1)
            actual_bytes = len(body)
            if actual_bytes > max_bytes:
                status = "RESPONSE_OVER_LIMIT"
                error_code = "BODY_EXCEEDS_RESPONSE_LIMIT"
            elif declared and declared.isdigit() and int(declared) != actual_bytes:
                status = "INCOMPLETE_CONTENT_LENGTH"
                error_code = "CONTENT_LENGTH_MISMATCH"
            elif http_status != 200:
                status = "HTTP_ERROR"
                error_code = "HTTP_" + str(http_status)
            else:
                status = "FETCHED"
                error_code = None
            return {
                "status": status,
                "http_status": http_status,
                "requested_url": url,
                "final_url": str(response.geturl()),
                "response_bytes": actual_bytes,
                "body": body,
                "error_code": error_code,
                **metadata,
            }
    except urllib.error.HTTPError as exc:
        return {
            "status": "HTTP_ERROR",
            "http_status": int(exc.code),
            "requested_url": url,
            "final_url": str(exc.geturl() or url),
            "response_bytes": 0,
            "body": b"",
            "error_code": "HTTP_" + str(exc.code),
            **_response_metadata(exc.headers),
        }
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {
            "status": "FETCH_ERROR",
            "http_status": None,
            "requested_url": url,
            "final_url": None,
            "response_bytes": 0,
            "body": b"",
            "error_code": type(exc).__name__,
            "error_detail": str(exc)[:240],
            **_response_metadata(None),
        }


def _classify_comparison(responses: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {str(row["profile_name"]): row for row in responses}
    first = by_name.get("population_baseline_first") or {}
    ua_only = by_name.get("pit_user_agent_only") or {}
    accept_only = by_name.get("pit_accept_only") or {}
    combined = by_name.get("forensic_combined_profile") or {}
    repeat = by_name.get("population_baseline_repeat") or {}

    def differs(left: dict[str, Any], right: dict[str, Any]) -> bool | None:
        if not left.get("response_sha256") or not right.get("response_sha256"):
            return None
        return (
            left.get("response_sha256") != right.get("response_sha256")
            or left.get("response_bytes") != right.get("response_bytes")
        )

    return {
        "baseline_repeat_stable": (
            not differs(first, repeat) if differs(first, repeat) is not None else None
        ),
        "user_agent_only_body_differs": differs(first, ua_only),
        "accept_only_body_differs": differs(first, accept_only),
        "forensic_combined_body_differs": differs(first, combined),
        "profile_body_differences_observed": sum(
            1 for value in (
                differs(first, ua_only),
                differs(first, accept_only),
                differs(first, combined),
            ) if value is True
        ),
        "baseline_repeat_body_differs": differs(first, repeat),
        "prior_expected_hash_match_count": sum(
            1 for row in responses if row.get("response_sha256") == EXPECTED_SHA256
        ),
        "prior_captured_hash_match_count": sum(
            1 for row in responses if row.get("response_sha256") == FROZEN_CAPTURED_SHA256
        ),
        "original_feed_raw_body_hash_match_count": sum(
            1 for row in responses if row.get("response_sha256") == SINGLE_FEED_RAW_BODY_SHA256
        ),
        "previous_current_primary_hash_match_count": sum(
            1 for row in responses if row.get("response_sha256") == PRIOR_CURRENT_PRIMARY_SHA256
        ),
        "frozen_expected_bytes_match_count": sum(
            1 for row in responses if row.get("response_bytes") == EXPECTED_BYTES
        ),
        "previous_current_bytes_match_count": sum(
            1 for row in responses if row.get("response_bytes") == PRIOR_CURRENT_PRIMARY_BYTES
        ),
    }


def _safe_response_record(profile: dict[str, str], result: dict[str, Any]) -> dict[str, Any]:
    body = result.get("body") if isinstance(result.get("body"), bytes) else b""
    response_bytes = len(body)
    complete = result.get("status") == "FETCHED" and result.get("http_status") == 200
    return {
        "profile_name": profile["name"],
        "user_agent_profile": profile["user_agent_profile"],
        "accept_profile": profile["accept_profile"],
        "accept_encoding": "identity",
        "requested_url": result.get("requested_url") or URL,
        "final_url": result.get("final_url"),
        "status": result.get("status"),
        "http_status": result.get("http_status"),
        "complete_http_200_response": complete,
        "response_bytes": response_bytes if result.get("response_bytes") is None else result.get("response_bytes"),
        "response_sha256": sha256(body) if complete else None,
        "prefix_16_bytes_hex": body[:16].hex() if complete else None,
        "suffix_16_bytes_hex": body[-16:].hex() if complete and body else None,
        "prefix_64_bytes_sha256": sha256(body[:64]) if complete else None,
        "suffix_64_bytes_sha256": sha256(body[-64:]) if complete else None,
        "error_code": result.get("error_code"),
        "error_detail": result.get("error_detail"),
        **{key: result.get(key) for key in (
            "content_type",
            "content_length_header",
            "content_encoding",
            "transfer_encoding",
            "etag",
            "last_modified",
            "date",
            "server",
            "accept_ranges",
        )},
    }


def run(
    request_path: Path,
    source_path: Path,
    summary_path: Path,
    output_path: Path,
    *,
    fetcher: Callable[[str, dict[str, str], int, int], dict[str, Any]] = default_fetch,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q220_http_representation_sensitivity",
        "candidate_id": "Q220",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "NOT_STARTED",
        "request_validation_passed": False,
        "source_validation_passed": False,
        "requested_profile_count": MAX_REQUESTS,
        "completed_request_count": 0,
        "source_download_bytes": 0,
        "max_response_bytes": MAX_RESPONSE_BYTES,
        "max_total_download_bytes": MAX_TOTAL_DOWNLOAD_BYTES,
        "response_profiles": [],
        "comparison": {},
        "gate_positive": False,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "next_gate": (
            "Use only this response-profile diagnosis to choose a distinct provenance step; "
            "never replace source hashes or clear Q220 from HTTP behavior alone."
        ),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    try:
        request = read_request(request_path)
        result["request_validation_passed"] = True
        result["request_sequence"] = request["REQUEST_SEQUENCE"]
        result["request_fingerprint"] = sha256(
            json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        )
        source, summary = validate_sources(source_path, summary_path, request)
        result.update({
            "source_validation_passed": True,
            "source_receipt_fingerprint": source["receipt_fingerprint"],
            "source_population_receipt_fingerprint": source["source_population_receipt_fingerprint"],
            "single_feed_upstream_receipt_fingerprint": summary["upstream_receipt_fingerprint"],
            "target_record_key": TARGET_RECORD_KEY,
            "primary_filename": PRIMARY_FILENAME,
            "source_provenance_baseline": {
                "expected_sha256": EXPECTED_SHA256,
                "expected_bytes": EXPECTED_BYTES,
                "previously_captured_sha256": FROZEN_CAPTURED_SHA256,
                "previously_captured_bytes": FROZEN_CAPTURED_BYTES,
                "original_feed_raw_text_sha256": SINGLE_FEED_RAW_BODY_SHA256,
                "original_feed_raw_text_bytes": SINGLE_FEED_RAW_BODY_BYTES,
                "prior_complete_submission_run_id": int(PRIOR_COMPLETE_SUBMISSION_RUN_ID),
                "prior_complete_submission_artifact_id": int(PRIOR_COMPLETE_SUBMISSION_ARTIFACT_ID),
                "prior_complete_submission_receipt_fingerprint": PRIOR_COMPLETE_SUBMISSION_RECEIPT_FINGERPRINT,
                "previous_current_primary_sha256": PRIOR_CURRENT_PRIMARY_SHA256,
                "previous_current_primary_bytes": PRIOR_CURRENT_PRIMARY_BYTES,
                "index_primary_expected_bytes": INDEX_PRIMARY_EXPECTED_BYTES,
            },
        })
    except Exception as exc:
        result.update({
            "status": "SOURCE_VALIDATION_REJECTED",
            "error": f"{type(exc).__name__}: {exc}"[:700],
            "next_gate": "Reconcile exact frozen receipt pins before making any HTTP request; no source request was made.",
        })
        _write_receipt(output_path, result)
        return result

    total_download_bytes = 0
    responses: list[dict[str, Any]] = []
    for index, profile in enumerate(PROFILES):
        if index > 0:
            sleep_fn(REQUEST_GAP_SECONDS)
        headers = request_headers(profile)
        try:
            fetched = fetcher(URL, headers, MAX_RESPONSE_BYTES, REQUEST_TIMEOUT_SECONDS)
            body = fetched.get("body") if isinstance(fetched.get("body"), bytes) else b""
            if len(body) > MAX_RESPONSE_BYTES:
                body = body[: MAX_RESPONSE_BYTES + 1]
                fetched = {**fetched, "status": "RESPONSE_OVER_LIMIT", "error_code": "BODY_EXCEEDS_RESPONSE_LIMIT"}
            total_download_bytes += len(body)
            if total_download_bytes > MAX_TOTAL_DOWNLOAD_BYTES:
                fetched = {
                    "status": "TOTAL_DOWNLOAD_BUDGET_EXCEEDED",
                    "http_status": fetched.get("http_status"),
                    "requested_url": URL,
                    "final_url": fetched.get("final_url"),
                    "response_bytes": len(body),
                    "body": b"",
                    "error_code": "TOTAL_DOWNLOAD_BUDGET_EXCEEDED",
                }
                body = b""
            fetched = {**fetched, "body": body}
        except Exception as exc:
            fetched = {
                "status": "FETCH_ERROR",
                "http_status": None,
                "requested_url": URL,
                "final_url": None,
                "response_bytes": 0,
                "body": b"",
                "error_code": type(exc).__name__,
                "error_detail": str(exc)[:240],
            }
        responses.append(_safe_response_record(profile, fetched))
        result["completed_request_count"] += 1
        result["source_download_bytes"] = total_download_bytes
    result["response_profiles"] = responses
    all_complete = (
        len(responses) == MAX_REQUESTS
        and all(row.get("status") == "FETCHED" and row.get("http_status") == 200 and row.get("complete_http_200_response") for row in responses)
        and total_download_bytes <= MAX_TOTAL_DOWNLOAD_BYTES
    )
    result["comparison"] = _classify_comparison(responses)
    result["comparison"]["all_responses_complete_http_200"] = all_complete
    result["comparison"]["no_source_bodies_persisted"] = True
    result["comparison"]["source_responses_share_same_requested_url"] = all(
        row.get("requested_url") == URL for row in responses
    )
    if not all_complete:
        result["status"] = "HTTP_REPRESENTATION_PROBE_INCOMPLETE"
        result["next_gate"] = "Preserve the failed bounded receipt. Do not retry automatically or change any source hash."
    elif (
        result["comparison"]["profile_body_differences_observed"] > 0
        or result["comparison"]["baseline_repeat_body_differs"] is True
    ):
        result["status"] = "HTTP_REPRESENTATION_VARIATION_OBSERVED"
        result["next_gate"] = (
            "Isolate the observed one-variable response difference with a separately reviewed byte-level explanation; "
            "all frozen hashes and Q220 gates remain unchanged."
        )
    else:
        result["status"] = "HTTP_REPRESENTATION_INVARIANT_AT_PROBE_TIME"
        result["next_gate"] = (
            "The fixed request profiles were byte-invariant during this probe. Investigate the historical capture/extraction "
            "provenance chain from the frozen population artifact; do not launch another multi-gigabyte SEC Feed download."
        )
    result["receipt_fingerprint"] = canonical_fingerprint(result)
    _write_receipt(output_path, result, preserve_fingerprint=True)
    return result


def _write_receipt(output_path: Path, result: dict[str, Any], preserve_fingerprint: bool = False) -> None:
    if not preserve_fingerprint:
        result["receipt_fingerprint"] = canonical_fingerprint(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def console_summary(result: dict[str, Any]) -> dict[str, Any]:
    comparison = result.get("comparison") or {}
    return {
        "candidate_id": result.get("candidate_id"),
        "status": result.get("status"),
        "request_validation_passed": result.get("request_validation_passed"),
        "source_validation_passed": result.get("source_validation_passed"),
        "completed_request_count": result.get("completed_request_count"),
        "source_download_bytes": result.get("source_download_bytes"),
        "receipt_fingerprint": result.get("receipt_fingerprint"),
        "baseline_repeat_stable": comparison.get("baseline_repeat_stable"),
        "user_agent_only_body_differs": comparison.get("user_agent_only_body_differs"),
        "accept_only_body_differs": comparison.get("accept_only_body_differs"),
        "forensic_combined_body_differs": comparison.get("forensic_combined_body_differs"),
        "gate_positive": False,
        "performance_authorization": False,
        "live_execution": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--single-summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(args.request, args.source_receipt, args.single_summary, args.output)
    print(json.dumps(console_summary(receipt), sort_keys=True))
    if receipt.get("status") in {
        "HTTP_REPRESENTATION_VARIATION_OBSERVED",
        "HTTP_REPRESENTATION_INVARIANT_AT_PROBE_TIME",
    } and receipt.get("completed_request_count") == MAX_REQUESTS:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
