"""One-shot, bounded Wayback CDX metadata probe for four frozen Q221 FPDS URLs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MANIFEST_PATH = "research/evidence/q221_historical_public_boundary_latest.json"
MANIFEST_BLOB_SHA1 = "b78cf6f7b48af3f914ee7c6d06a38f6485b0438f"
MANIFEST_FINGERPRINT = "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
PREREG_PATH = "research/preregistrations/q221_fpds_wayback_cdx_metadata_probe_r1_2026_10_16.json"
REQUEST_PATH = "research/run_requests/q221_fpds_wayback_cdx_metadata_probe.trigger"
PRIOR_ARCHIVE_PREREG_PATH = "research/preregistrations/q221_arquivo_pt_fpds_timemap_probe_r2_2026_10_16.json"
PRIOR_ARCHIVE_PREREG_BLOB_SHA1 = "c3e7b01175811dc22cc6ec70f87750117fab7049"
PRIOR_ARCHIVE_RECEIPT_PATH = "research/evidence/q221_arquivo_pt_fpds_timemap_r2_latest.json"
PRIOR_ARCHIVE_RECEIPT_BLOB_SHA1 = "d0d56836c4356977dfa37e515ffe2516b1e7c6d9"
PRIOR_ARCHIVE_RECEIPT_FINGERPRINT = "a5bb1aee620768f71bad7f05fd8af5ac123b6fe87230bd9df538999640438403"
CDX_ENDPOINT = "https://web.archive.org/cdx/search/cdx"
REQUEST_SEQUENCE = "2026-10-16T12:15:45Z"
MAX_REQUESTS = 4
MAX_RESPONSE_BYTES_EACH = 524_288
MAX_TOTAL_RESPONSE_BYTES = 2_097_152
MAX_CAPTURE_ROWS_PER_URL = 1_000
TIMEOUT_SECONDS = 45
REQUEST_GAP_SECONDS = 1.0
OUTPUT_FIELDS = ("timestamp", "original", "mimetype", "statuscode", "digest", "length")

EXPECTED_RECORDS = (
    {
        "record_id": "CACI_2019_PRE_EVENT",
        "transaction_key": "FA875018C0180|P00003|2019-01-03|28eee911-76af-7147-f760-4ec5f90bec2d-C|N3PBJAVNKF61",
        "piid": "FA875018C0180",
        "modification_number": "P00003",
        "action_date": "2019-01-03",
        "recipient_uei": "N3PBJAVNKF61",
        "source_url": "https://www.fpds.gov/dbsight/FEEDS/ATOM?FEEDNAME=PUBLIC&q=PIID%3A%22FA875018C0180%22",
    },
    {
        "record_id": "BOOZ_ALLEN_2020_PRE_EVENT",
        "transaction_key": "FA807520F0004|0|2020-01-02|ffca72e5-fba2-798a-6969-2a6c45e9f985-C|JCBMLGPE6Z71",
        "piid": "FA807520F0004",
        "modification_number": "0",
        "action_date": "2020-01-02",
        "recipient_uei": "JCBMLGPE6Z71",
        "source_url": "https://www.fpds.gov/dbsight/FEEDS/ATOM?FEEDNAME=PUBLIC&q=PIID%3A%22FA807520F0004%22",
    },
    {
        "record_id": "OSI_AS_E_2023_PRE_EVENT",
        "transaction_key": "70RWMD23C00000001|0|2023-01-03|f857dc49-8bdd-480e-25fb-f2be8c9d65c2-C|CNB9EF8VHML3",
        "piid": "70RWMD23C00000001",
        "modification_number": "0",
        "action_date": "2023-01-03",
        "recipient_uei": "CNB9EF8VHML3",
        "source_url": "https://www.fpds.gov/dbsight/FEEDS/ATOM?FEEDNAME=PUBLIC&q=PIID%3A%2270RWMD23C00000001%22",
    },
    {
        "record_id": "NORTHROP_2024_PRE_EVENT",
        "transaction_key": "FA865124FB001|0|2024-01-02|c19bef58-16e3-f32b-b699-25b3078161f8-C|FVSEZFPCQ316",
        "piid": "FA865124FB001",
        "modification_number": "0",
        "action_date": "2024-01-02",
        "recipient_uei": "FVSEZFPCQ316",
        "source_url": "https://www.fpds.gov/dbsight/FEEDS/ATOM?FEEDNAME=PUBLIC&q=PIID%3A%22FA865124FB001%22",
    },
)
EXPECTED_REQUEST_VALUES = {
    "RUN_Q221_FPDS_WAYBACK_CDX_METADATA_PROBE": "true",
    "REASON": "DISTINCT_WAYBACK_CDX_METADATA_LOOKUP_FOR_FOUR_FROZEN_FPDS_FEED_URLS",
    "PREREG_PATH": PREREG_PATH,
    "SOURCE_MANIFEST_PATH": MANIFEST_PATH,
    "SOURCE_MANIFEST_GIT_BLOB_SHA1": MANIFEST_BLOB_SHA1,
    "SOURCE_MANIFEST_RECEIPT_FINGERPRINT": MANIFEST_FINGERPRINT,
    "PRIOR_ARCHIVE_PREREG_PATH": PRIOR_ARCHIVE_PREREG_PATH,
    "PRIOR_ARCHIVE_PREREG_GIT_BLOB_SHA1": PRIOR_ARCHIVE_PREREG_BLOB_SHA1,
    "PRIOR_ARCHIVE_RECEIPT_PATH": PRIOR_ARCHIVE_RECEIPT_PATH,
    "PRIOR_ARCHIVE_RECEIPT_GIT_BLOB_SHA1": PRIOR_ARCHIVE_RECEIPT_BLOB_SHA1,
    "PRIOR_ARCHIVE_RECEIPT_FINGERPRINT": PRIOR_ARCHIVE_RECEIPT_FINGERPRINT,
    "MAX_REQUESTS": str(MAX_REQUESTS),
    "MAX_RESPONSE_BYTES_EACH": str(MAX_RESPONSE_BYTES_EACH),
    "MAX_TOTAL_RESPONSE_BYTES": str(MAX_TOTAL_RESPONSE_BYTES),
    "MAX_CAPTURE_ROWS_PER_URL": str(MAX_CAPTURE_ROWS_PER_URL),
    "REQUEST_TIMEOUT_SECONDS": str(TIMEOUT_SECONDS),
    "MIN_REQUEST_GAP_SECONDS": "1",
    "MATCH_TYPE": "exact",
    "GZIP": "false",
    "AUTOMATIC_RETRIES": "0",
    "FOLLOW_REDIRECTS": "false",
    "ARCHIVED_REPLAY_REQUESTS": "0",
    "DIRECT_FPDS_REQUESTS": "0",
    "ARQUIVO_PT_REQUESTS": "0",
    "SAM_API_REQUESTS": "0",
    "USASPENDING_REQUESTS": "0",
    "SEC_REQUESTS": "0",
    "COMMONCRAWL_REQUESTS": "0",
    "TARGET_KEY_EXPANSION": "false",
    "ARCHIVE_PAYLOADS_DOWNLOADED": "false",
    "RESPONSE_BODIES_PERSISTED": "false",
    "FROZEN_TRANSACTION_ROWS_MODIFIED": "false",
    "SOURCE_HASHES_MODIFIED": "false",
    "PAPER_ONLY": "true",
    "LIVE_TRADING_ENABLED": "false",
    "ORDERS_ENABLED": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
    "REQUEST_SEQUENCE": REQUEST_SEQUENCE,
}


class ProbeError(ValueError):
    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def canonical_fingerprint(value: dict[str, Any], excluded: tuple[str, ...] = ("receipt_fingerprint",)) -> str:
    payload = {key: item for key, item in value.items() if key not in excluded}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(raw)


def analysis_fingerprint(value: dict[str, Any]) -> str:
    return canonical_fingerprint(value, excluded=(
        "analysis_fingerprint", "receipt_fingerprint", "generated_at_utc", "workflow_run_id", "cross_arch_validation"
    ))


def read_json(path: Path, code: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProbeError(code, type(exc).__name__) from exc
    if not isinstance(value, dict):
        raise ProbeError(code + "_NOT_OBJECT")
    return value, raw


def read_marker(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ProbeError("Q221_WAYBACK_CDX_REQUEST_MARKER_MISSING", type(exc).__name__) from exc
    values: dict[str, str] = {}
    for line_number, line in enumerate(lines, start=1):
        if not line or line.strip() != line or "=" not in line:
            raise ProbeError("Q221_WAYBACK_CDX_REQUEST_MARKER_INVALID_LINE", str(line_number))
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key) or not value or key in values:
            raise ProbeError("Q221_WAYBACK_CDX_REQUEST_MARKER_INVALID_KEY_VALUE", str(line_number))
        values[key] = value
    if values != EXPECTED_REQUEST_VALUES:
        raise ProbeError("Q221_WAYBACK_CDX_REQUEST_MARKER_PIN_MISMATCH")
    datetime.strptime(values["REQUEST_SEQUENCE"], "%Y-%m-%dT%H:%M:%SZ")
    return values


def walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_strings(child)


def validate_preflight(repo_root: Path, request_path: Path, prereg_path: Path) -> dict[str, Any]:
    for path in (request_path, prereg_path):
        try:
            path.resolve().relative_to(repo_root.resolve())
        except ValueError as exc:
            raise ProbeError("Q221_WAYBACK_CDX_PATH_OUTSIDE_REPOSITORY") from exc
    if prereg_path.resolve() != (repo_root / PREREG_PATH).resolve():
        raise ProbeError("Q221_WAYBACK_CDX_PREREG_PATH_MISMATCH")
    marker = read_marker(request_path)
    prereg, prereg_raw = read_json(prereg_path, "Q221_WAYBACK_CDX_PREREG_INVALID")
    if prereg.get("schema_version") != 1 or prereg.get("record_type") != "q221_fpds_wayback_cdx_metadata_probe_preregistration":
        raise ProbeError("Q221_WAYBACK_CDX_PREREG_IDENTITY_MISMATCH")
    if prereg.get("candidate_id") != "Q221" or prereg.get("study_mode") != "BOUNDED_ARCHIVE_CDX_METADATA_ONLY":
        raise ProbeError("Q221_WAYBACK_CDX_PREREG_MODE_MISMATCH")
    if prereg.get("preregistered_at_utc") != marker["REQUEST_SEQUENCE"] or prereg.get("request_sequence") != marker["REQUEST_SEQUENCE"]:
        raise ProbeError("Q221_WAYBACK_CDX_SEQUENCE_MISMATCH")
    if prereg.get("records") != list(EXPECTED_RECORDS):
        raise ProbeError("Q221_WAYBACK_CDX_FROZEN_RECORDS_MISMATCH")

    frozen = prereg.get("frozen_inputs", {})
    expected_frozen = {
        "boundary_path": MANIFEST_PATH,
        "boundary_git_blob_sha1": MANIFEST_BLOB_SHA1,
        "boundary_receipt_fingerprint": MANIFEST_FINGERPRINT,
        "prior_arquivo_prereg_path": PRIOR_ARCHIVE_PREREG_PATH,
        "prior_arquivo_prereg_git_blob_sha1": PRIOR_ARCHIVE_PREREG_BLOB_SHA1,
        "prior_arquivo_receipt_path": PRIOR_ARCHIVE_RECEIPT_PATH,
        "prior_arquivo_receipt_git_blob_sha1": PRIOR_ARCHIVE_RECEIPT_BLOB_SHA1,
        "prior_arquivo_receipt_fingerprint": PRIOR_ARCHIVE_RECEIPT_FINGERPRINT,
        "prior_arquivo_disposition": "METADATA_ROUTE_UNAVAILABLE_FOR_FROZEN_URLS; NO_ARCHIVE_ABSENCE_INFERENCE",
        "prior_arquivo_workflow_run_id": 38869362949,
        "transaction_key_count": 4,
    }
    if frozen != expected_frozen:
        raise ProbeError("Q221_WAYBACK_CDX_FROZEN_INPUTS_MISMATCH")

    manifest, manifest_raw = read_json(repo_root / MANIFEST_PATH, "Q221_WAYBACK_CDX_MANIFEST_INVALID")
    if git_blob_sha1(manifest_raw) != MANIFEST_BLOB_SHA1 or manifest.get("candidate_id") != "Q221":
        raise ProbeError("Q221_WAYBACK_CDX_MANIFEST_BLOB_MISMATCH")
    if manifest.get("receipt_fingerprint") != MANIFEST_FINGERPRINT:
        raise ProbeError("Q221_WAYBACK_CDX_MANIFEST_FINGERPRINT_MISMATCH")
    if manifest.get("historical_first_public_observation_proven") is not False:
        raise ProbeError("Q221_WAYBACK_CDX_MANIFEST_GATE_UNEXPECTEDLY_OPEN")
    strings = set(walk_strings(manifest))
    if any(row["transaction_key"] not in strings for row in EXPECTED_RECORDS):
        raise ProbeError("Q221_WAYBACK_CDX_KEY_NOT_IN_FROZEN_MANIFEST")

    prior_prereg, prior_prereg_raw = read_json(repo_root / PRIOR_ARCHIVE_PREREG_PATH, "Q221_WAYBACK_CDX_PRIOR_PREREG_INVALID")
    if git_blob_sha1(prior_prereg_raw) != PRIOR_ARCHIVE_PREREG_BLOB_SHA1:
        raise ProbeError("Q221_WAYBACK_CDX_PRIOR_PREREG_BLOB_MISMATCH")
    if prior_prereg.get("record_type") != "q221_arquivo_pt_fpds_timemap_probe_preregistration":
        raise ProbeError("Q221_WAYBACK_CDX_PRIOR_PREREG_TYPE_MISMATCH")
    prior_rows = {row.get("record_id"): row for row in prior_prereg.get("records", [])}
    for row in EXPECTED_RECORDS:
        prior = prior_rows.get(row["record_id"], {})
        for field in ("transaction_key", "source_url", "piid", "modification_number", "action_date", "recipient_uei"):
            if prior.get(field) != row.get(field):
                raise ProbeError("Q221_WAYBACK_CDX_PRIOR_URL_OR_KEY_MISMATCH:" + row["record_id"])

    prior_receipt, prior_receipt_raw = read_json(repo_root / PRIOR_ARCHIVE_RECEIPT_PATH, "Q221_WAYBACK_CDX_PRIOR_RECEIPT_INVALID")
    if git_blob_sha1(prior_receipt_raw) != PRIOR_ARCHIVE_RECEIPT_BLOB_SHA1:
        raise ProbeError("Q221_WAYBACK_CDX_PRIOR_RECEIPT_BLOB_MISMATCH")
    if prior_receipt.get("receipt_fingerprint") != PRIOR_ARCHIVE_RECEIPT_FINGERPRINT:
        raise ProbeError("Q221_WAYBACK_CDX_PRIOR_RECEIPT_FINGERPRINT_MISMATCH")
    if prior_receipt.get("status") != "Q221_ARQUIVO_PT_TIMEMAP_METADATA_INCOMPLETE":
        raise ProbeError("Q221_WAYBACK_CDX_PRIOR_RESULT_STATUS_MISMATCH")
    prior_observations = {row.get("record_id"): row for row in prior_receipt.get("observations", [])}
    for row in EXPECTED_RECORDS:
        prior = prior_observations.get(row["record_id"], {})
        if prior.get("source_url") != row["source_url"] or prior.get("transaction_key") != row["transaction_key"]:
            raise ProbeError("Q221_WAYBACK_CDX_PRIOR_RECEIPT_RECORD_MISMATCH:" + row["record_id"])

    expected_contract = {
        "request_count_exact": 4,
        "request_order": "CACI_2019_PRE_EVENT, BOOZ_ALLEN_2020_PRE_EVENT, OSI_AS_E_2023_PRE_EVENT, NORTHROP_2024_PRE_EVENT",
        "max_response_bytes_each": MAX_RESPONSE_BYTES_EACH,
        "max_total_response_bytes": MAX_TOTAL_RESPONSE_BYTES,
        "max_capture_rows_per_url": MAX_CAPTURE_ROWS_PER_URL,
        "timeout_seconds": TIMEOUT_SECONDS,
        "minimum_request_gap_seconds": 1,
        "automatic_retries": 0,
        "redirects_followed": False,
        "match_type": "exact",
        "gzip": False,
        "fields": list(OUTPUT_FIELDS),
        "origin_fpds_requests": 0,
        "archived_replay_requests": 0,
        "arquivo_pt_requests": 0,
        "sam_api_requests": 0,
        "usaspending_requests": 0,
        "sec_requests": 0,
        "commoncrawl_requests": 0,
        "archive_payloads_downloaded": 0,
        "response_bodies_persisted": False,
    }
    if prereg.get("request_contract") != expected_contract:
        raise ProbeError("Q221_WAYBACK_CDX_REQUEST_CONTRACT_MISMATCH")
    safety = prereg.get("safety", {})
    for key in (
        "live_trading_enabled", "orders_enabled", "automatic_promotion", "source_population_changes",
        "frozen_transaction_rows_modified", "recipient_identity_mappings_added",
        "historical_first_public_observation_proven", "event_level_public_boundary_proven",
        "recipient_to_issuer_mapping_frozen", "scientific_evidence", "performance_authorization",
        "holdout_selection", "ranking", "tuning", "promotion", "live_execution",
    ):
        if safety.get(key) is not False:
            raise ProbeError("Q221_WAYBACK_CDX_SAFETY_MISMATCH:" + key)
    if safety.get("paper_only") is not True:
        raise ProbeError("Q221_WAYBACK_CDX_PAPER_ONLY_FALSE")
    return {
        "status": "Q221_WAYBACK_CDX_FROZEN_INPUTS_VALID",
        "request_count": 0,
        "source_requests_made": 0,
        "manifest_blob_sha1": git_blob_sha1(manifest_raw),
        "prior_archive_prereg_blob_sha1": git_blob_sha1(prior_prereg_raw),
        "prior_archive_receipt_blob_sha1": git_blob_sha1(prior_receipt_raw),
        "preregistration_blob_sha1": git_blob_sha1(prereg_raw),
        "records_validated": len(EXPECTED_RECORDS),
        "paper_only": True,
        "event_level_public_boundary_proven": False,
        "historical_first_public_observation_proven": False,
        "recipient_to_issuer_mapping_frozen": False,
    }


def build_cdx_url(source_url: str) -> str:
    query = urllib.parse.urlencode(
        {
            "url": source_url,
            "matchType": "exact",
            "output": "json",
            "fl": ",".join(OUTPUT_FIELDS),
            "limit": str(MAX_CAPTURE_ROWS_PER_URL),
            "gzip": "false",
        },
        quote_via=urllib.parse.quote,
        safe=",",
    )
    return CDX_ENDPOINT + "?" + query


def parse_cdx_body(raw: bytes, expected_original_url: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProbeError("Q221_WAYBACK_CDX_SCHEMA_INVALID", type(exc).__name__) from exc
    if not isinstance(payload, list):
        raise ProbeError("Q221_WAYBACK_CDX_SCHEMA_INCOMPLETE", "expected JSON array")
    # The upstream JsonWriter emits its header only when at least one CDX row is written.
    # With zero rows, the writer emits an empty JSON array followed by a newline.
    if not payload:
        return {
            "query_completed": True,
            "status": "CDX_METADATA_RESPONSE_VALID_EMPTY",
            "capture_count": 0,
            "exact_original_url_capture_count": 0,
            "exact_original_url_http_200_capture_count": 0,
            "captures": [],
        }
    if payload[0] != list(OUTPUT_FIELDS):
        raise ProbeError("Q221_WAYBACK_CDX_FIELD_HEADER_MISMATCH")
    rows = payload[1:]
    if len(rows) > MAX_CAPTURE_ROWS_PER_URL:
        raise ProbeError("Q221_WAYBACK_CDX_ROW_LIMIT_EXCEEDED")
    captures = []
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != len(OUTPUT_FIELDS) or any(not isinstance(cell, str) for cell in row):
            raise ProbeError("Q221_WAYBACK_CDX_ROW_INVALID:" + str(index))
        item = dict(zip(OUTPUT_FIELDS, row))
        if not re.fullmatch(r"\d{14}", item["timestamp"]):
            raise ProbeError("Q221_WAYBACK_CDX_TIMESTAMP_INVALID:" + str(index))
        if not item["original"] or not item["statuscode"] or not item["mimetype"]:
            raise ProbeError("Q221_WAYBACK_CDX_ROW_FIELDS_MISSING:" + str(index))
        if item["length"] and not item["length"].isdigit():
            raise ProbeError("Q221_WAYBACK_CDX_LENGTH_INVALID:" + str(index))
        if item["original"] != expected_original_url:
            raise ProbeError("Q221_WAYBACK_CDX_ORIGINAL_URL_MISMATCH:" + str(index))
        captures.append(item)
    exact_200 = [row for row in captures if row["statuscode"] == "200"]
    return {
        "query_completed": True,
        "status": "CDX_METADATA_RESPONSE_VALID",
        "capture_count": len(captures),
        "exact_original_url_capture_count": len(captures),
        "exact_original_url_http_200_capture_count": len(exact_200),
        "captures": captures,
    }


def empty_observation(record: dict[str, Any], status: str, http_status: int | None = None) -> dict[str, Any]:
    return {
        "record_id": record["record_id"],
        "transaction_key": record["transaction_key"],
        "source_url": record["source_url"],
        "method": "GET",
        "requested_host": "web.archive.org",
        "http_status": http_status,
        "content_type": None,
        "response_bytes": 0,
        "response_sha256": None,
        "response_body_persisted": False,
        "query_completed": False,
        "status": status,
        "capture_count": 0,
        "exact_original_url_capture_count": 0,
        "exact_original_url_http_200_capture_count": 0,
        "captures": [],
    }


def fetch_one(opener: urllib.request.OpenerDirector, record: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        build_cdx_url(record["source_url"]),
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "TradingAgentOS-Q221-Wayback-CDX-Metadata/1.0",
        },
        method="GET",
    )
    try:
        response = opener.open(request, timeout=TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        return empty_observation(record, "HTTP_" + str(exc.code), int(exc.code))
    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        timed_out = isinstance(exc, (TimeoutError, socket.timeout)) or isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout))
        observation = empty_observation(record, "TIMEOUT" if timed_out else "NETWORK_ERROR")
        observation["error_class"] = type(exc).__name__
        return observation
    except Exception as exc:
        observation = empty_observation(record, "CLIENT_ERROR")
        observation["error_class"] = type(exc).__name__
        return observation
    with response:
        status_code = int(response.getcode())
        content_type = response.headers.get("Content-Type")
        if status_code != 200:
            return empty_observation(record, "HTTP_" + str(status_code), status_code)
        raw = response.read(MAX_RESPONSE_BYTES_EACH)
    base = empty_observation(record, "CDX_METADATA_RESPONSE_VALID", status_code)
    base["content_type"] = content_type
    base["response_bytes"] = len(raw)
    base["response_sha256"] = sha256(raw)
    if len(raw) >= MAX_RESPONSE_BYTES_EACH:
        base["status"] = "RESPONSE_AT_OR_OVER_LIMIT"
        return base
    try:
        parsed = parse_cdx_body(raw, record["source_url"])
    except ProbeError as exc:
        base["status"] = exc.code
        return base
    base.update(parsed)
    base["response_body_persisted"] = False
    return base


def build_receipt(observations: list[dict[str, Any]], workflow_run_id: int | None) -> dict[str, Any]:
    complete = len(observations) == MAX_REQUESTS and all(item.get("query_completed") is True for item in observations)
    response_bytes_total = sum(int(item.get("response_bytes") or 0) for item in observations)
    exact_capture_count = sum(int(item.get("exact_original_url_capture_count") or 0) for item in observations)
    exact_200_count = sum(int(item.get("exact_original_url_http_200_capture_count") or 0) for item in observations)
    if exact_200_count:
        next_gate = "Separately preregister a bounded replay inspection for frozen exact-URL HTTP 200 capture metadata; verify the exact PIID/modification/action-date/recipient tuple without claiming first-public time."
    elif complete:
        next_gate = "No exact-URL HTTP 200 capture was returned for this fixed four-key CDX query; seek another independently documented historical transaction record source and do not infer historical absence."
    else:
        next_gate = "Preserve the bounded CDX transport/schema incompleteness; any changed route requires separate review and preregistration."
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q221_fpds_wayback_cdx_metadata_probe",
        "candidate_id": "Q221",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_run_id": workflow_run_id,
        "preregistration_path": PREREG_PATH,
        "preregistration_git_blob_sha1": None,
        "request_marker_path": REQUEST_PATH,
        "request_sequence": REQUEST_SEQUENCE,
        "frozen_inputs": {
            "boundary_path": MANIFEST_PATH,
            "boundary_git_blob_sha1": MANIFEST_BLOB_SHA1,
            "boundary_receipt_fingerprint": MANIFEST_FINGERPRINT,
            "prior_arquivo_prereg_path": PRIOR_ARCHIVE_PREREG_PATH,
            "prior_arquivo_prereg_git_blob_sha1": PRIOR_ARCHIVE_PREREG_BLOB_SHA1,
            "prior_arquivo_receipt_path": PRIOR_ARCHIVE_RECEIPT_PATH,
            "prior_arquivo_receipt_git_blob_sha1": PRIOR_ARCHIVE_RECEIPT_BLOB_SHA1,
            "prior_arquivo_receipt_fingerprint": PRIOR_ARCHIVE_RECEIPT_FINGERPRINT,
        },
        "source_contract": {
            "endpoint": CDX_ENDPOINT,
            "archive_metadata_requests_attempted": len(observations),
            "request_count_known": True,
            "max_requests": MAX_REQUESTS,
            "max_response_bytes_each": MAX_RESPONSE_BYTES_EACH,
            "max_total_response_bytes": MAX_TOTAL_RESPONSE_BYTES,
            "max_capture_rows_per_url": MAX_CAPTURE_ROWS_PER_URL,
            "response_bytes_total": response_bytes_total,
            "automatic_retries": 0,
            "redirects_followed": False,
            "direct_fpds_requests": 0,
            "archived_replay_requests": 0,
            "arquivo_pt_requests": 0,
            "sam_api_requests": 0,
            "usaspending_requests": 0,
            "sec_requests": 0,
            "commoncrawl_requests": 0,
            "archive_payloads_downloaded": 0,
            "response_bodies_persisted": False,
        },
        "aggregate": {
            "metadata_lookup_complete": complete,
            "timemap_queries_completed": sum(int(item.get("query_completed") is True) for item in observations),
            "capture_metadata_row_count": sum(int(item.get("capture_count") or 0) for item in observations),
            "exact_original_url_capture_metadata_count": exact_capture_count,
            "exact_original_url_http_200_capture_metadata_count": exact_200_count,
            "historical_first_public_observation_proven": False,
            "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "q221_gate_positive": False,
        },
        "observations": observations,
        "interpretation": {
            "metadata_only": True,
            "capture_timestamps_are_archive_observations_not_first_public_timestamps": True,
            "empty_or_failed_lookup_is_not_proof_of_historical_absence": True,
            "event_level_public_boundary_proven": False,
            "historical_first_public_observation_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "scientific_evidence": False,
        },
        "next_gate": next_gate,
        "status": "Q221_WAYBACK_CDX_METADATA_COMPLETE" if complete else "Q221_WAYBACK_CDX_METADATA_INCOMPLETE",
        "safety": {
            "paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False,
            "source_population_changes": False, "frozen_transaction_rows_modified": False, "recipient_identity_mappings_added": False,
            "historical_first_public_observation_proven": False, "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False, "scientific_evidence": False, "performance_authorization": False,
            "holdout_selection": False, "ranking": False, "tuning": False, "promotion": False, "live_execution": False,
        },
    }
    receipt["analysis_fingerprint"] = analysis_fingerprint(receipt)
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    return receipt


def build_fallback_receipt(run_id: int | None, *, source_requests_known_zero: bool, reason: str) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q221_fpds_wayback_cdx_metadata_probe",
        "candidate_id": "Q221",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_run_id": run_id,
        "preregistration_path": PREREG_PATH,
        "preregistration_git_blob_sha1": None,
        "request_marker_path": REQUEST_PATH,
        "request_sequence": REQUEST_SEQUENCE,
        "source_contract": {
            "endpoint": CDX_ENDPOINT,
            "archive_metadata_requests_attempted": 0 if source_requests_known_zero else None,
            "request_count_known": source_requests_known_zero,
            "max_requests": MAX_REQUESTS,
            "automatic_retries": 0,
            "redirects_followed": False,
            "direct_fpds_requests": 0,
            "archived_replay_requests": 0,
            "archive_payloads_downloaded": 0,
            "response_bodies_persisted": False,
        },
        "observations": [],
        "interpretation": {
            "metadata_only": True,
            "empty_or_failed_lookup_is_not_proof_of_historical_absence": True,
            "historical_first_public_observation_proven": False,
            "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "scientific_evidence": False,
        },
        "next_gate": "Fail closed; inspect the immutable artifact and preflight/capture logs before any new source contract.",
        "status": "PREFLIGHT_FAILED_NO_SOURCE_REQUESTS" if source_requests_known_zero else "CAPTURE_ABORTED_REQUEST_COUNT_UNKNOWN",
        "fallback_reason_code": reason,
        "safety": {
            "paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False,
            "source_population_changes": False, "frozen_transaction_rows_modified": False, "recipient_identity_mappings_added": False,
            "historical_first_public_observation_proven": False, "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False, "scientific_evidence": False, "performance_authorization": False,
            "holdout_selection": False, "ranking": False, "tuning": False, "promotion": False, "live_execution": False,
        },
    }
    receipt["analysis_fingerprint"] = analysis_fingerprint(receipt)
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    return receipt


def validate_receipt(receipt: dict[str, Any]) -> None:
    if receipt.get("schema_version") != 1 or receipt.get("record_type") != "q221_fpds_wayback_cdx_metadata_probe":
        raise ProbeError("Q221_WAYBACK_CDX_RECEIPT_TYPE_INVALID")
    if receipt.get("receipt_fingerprint") != canonical_fingerprint(receipt):
        raise ProbeError("Q221_WAYBACK_CDX_RECEIPT_FINGERPRINT_MISMATCH")
    if receipt.get("analysis_fingerprint") != analysis_fingerprint(receipt):
        raise ProbeError("Q221_WAYBACK_CDX_ANALYSIS_FINGERPRINT_MISMATCH")
    safety = receipt.get("safety", {})
    for key in (
        "live_trading_enabled", "orders_enabled", "automatic_promotion", "source_population_changes",
        "frozen_transaction_rows_modified", "recipient_identity_mappings_added", "historical_first_public_observation_proven",
        "event_level_public_boundary_proven", "recipient_to_issuer_mapping_frozen", "scientific_evidence",
        "performance_authorization", "holdout_selection", "ranking", "tuning", "promotion", "live_execution",
    ):
        if safety.get(key) is not False:
            raise ProbeError("Q221_WAYBACK_CDX_RECEIPT_SAFETY_MISMATCH:" + key)
    if safety.get("paper_only") is not True:
        raise ProbeError("Q221_WAYBACK_CDX_RECEIPT_PAPER_ONLY_FALSE")
    contract = receipt.get("source_contract", {})
    if contract.get("direct_fpds_requests") != 0 or contract.get("archived_replay_requests") != 0 or contract.get("archive_payloads_downloaded") != 0 or contract.get("response_bodies_persisted") is not False:
        raise ProbeError("Q221_WAYBACK_CDX_RECEIPT_SCOPE_VIOLATION")
    status = receipt.get("status")
    if status in {"Q221_WAYBACK_CDX_METADATA_COMPLETE", "Q221_WAYBACK_CDX_METADATA_INCOMPLETE"}:
        observations = receipt.get("observations")
        if not isinstance(observations, list) or len(observations) != MAX_REQUESTS:
            raise ProbeError("Q221_WAYBACK_CDX_RECEIPT_OBSERVATION_COUNT_INVALID")
        total = 0
        for index, (observation, expected) in enumerate(zip(observations, EXPECTED_RECORDS)):
            if observation.get("record_id") != expected["record_id"] or observation.get("transaction_key") != expected["transaction_key"] or observation.get("source_url") != expected["source_url"]:
                raise ProbeError("Q221_WAYBACK_CDX_RECEIPT_FROZEN_ROW_MISMATCH:" + str(index))
            if observation.get("requested_host") != "web.archive.org" or observation.get("response_body_persisted") is not False:
                raise ProbeError("Q221_WAYBACK_CDX_RECEIPT_SCOPE_METADATA_MISMATCH:" + str(index))
            count = observation.get("response_bytes")
            if not isinstance(count, int) or count < 0 or count > MAX_RESPONSE_BYTES_EACH:
                raise ProbeError("Q221_WAYBACK_CDX_RECEIPT_BYTE_COUNT_INVALID:" + str(index))
            total += count
            for capture in observation.get("captures", []):
                if set(capture) != set(OUTPUT_FIELDS) or capture.get("original") != expected["source_url"]:
                    raise ProbeError("Q221_WAYBACK_CDX_RECEIPT_CAPTURE_FIELDS_INVALID")
        if total > MAX_TOTAL_RESPONSE_BYTES:
            raise ProbeError("Q221_WAYBACK_CDX_RECEIPT_TOTAL_BYTES_EXCEEDED")
        aggregate = receipt.get("aggregate", {})
        if aggregate.get("historical_first_public_observation_proven") is not False or aggregate.get("event_level_public_boundary_proven") is not False:
            raise ProbeError("Q221_WAYBACK_CDX_RECEIPT_GATE_FLAGS_INVALID")
    elif status in {"PREFLIGHT_FAILED_NO_SOURCE_REQUESTS", "CAPTURE_ABORTED_REQUEST_COUNT_UNKNOWN"}:
        if receipt.get("observations") != []:
            raise ProbeError("Q221_WAYBACK_CDX_FALLBACK_HAS_OBSERVATIONS")
        if status == "PREFLIGHT_FAILED_NO_SOURCE_REQUESTS" and (
            contract.get("request_count_known") is not True or contract.get("archive_metadata_requests_attempted") != 0
        ):
            raise ProbeError("Q221_WAYBACK_CDX_PREFLIGHT_FALLBACK_REQUEST_COUNT_INVALID")
        if status == "CAPTURE_ABORTED_REQUEST_COUNT_UNKNOWN" and contract.get("request_count_known") is not False:
            raise ProbeError("Q221_WAYBACK_CDX_CAPTURE_FALLBACK_REQUEST_COUNT_INVALID")
    else:
        raise ProbeError("Q221_WAYBACK_CDX_RECEIPT_STATUS_INVALID")


def capture(repo_root: Path, request_path: Path, prereg_path: Path, run_id: int, output: Path) -> int:
    validate_preflight(repo_root, request_path, prereg_path)
    opener = urllib.request.build_opener(NoRedirect())
    observations: list[dict[str, Any]] = []
    last_start: float | None = None
    for record in EXPECTED_RECORDS:
        if last_start is not None:
            remaining = REQUEST_GAP_SECONDS - (time.monotonic() - last_start)
            if remaining > 0:
                time.sleep(remaining)
        last_start = time.monotonic()
        observations.append(fetch_one(opener, record))
    receipt = build_receipt(observations, workflow_run_id=run_id)
    receipt["preregistration_git_blob_sha1"] = git_blob_sha1((repo_root / prereg_path).read_bytes())
    receipt["analysis_fingerprint"] = analysis_fingerprint(receipt)
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "archive_metadata_requests_attempted": receipt["source_contract"]["archive_metadata_requests_attempted"],
        "queries_completed": receipt["aggregate"]["timemap_queries_completed"],
        "capture_metadata_row_count": receipt["aggregate"]["capture_metadata_row_count"],
        "source_requests_to_origin": 0,
        "archived_replay_requests": 0,
        "paper_only": True,
    }, sort_keys=True))
    return 0 if receipt["status"] == "Q221_WAYBACK_CDX_METADATA_COMPLETE" else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("validate-only", "capture", "fallback", "verify"), required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--request", type=Path, default=Path(REQUEST_PATH))
    parser.add_argument("--prereg", type=Path, default=Path(PREREG_PATH))
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--source-requests-known-zero", action="store_true")
    parser.add_argument("--reason", default="UNSPECIFIED_FAIL_CLOSED")
    args = parser.parse_args(argv)

    if args.mode == "validate-only":
        print(json.dumps(validate_preflight(args.repo_root, args.request, args.prereg), sort_keys=True))
        return 0
    if args.mode == "capture":
        if args.output is None or args.run_id is None:
            parser.error("capture mode requires --output and --run-id")
        return capture(args.repo_root, args.request, args.prereg, args.run_id, args.output)
    if args.mode == "fallback":
        if args.output is None:
            parser.error("fallback mode requires --output")
        receipt = build_fallback_receipt(args.run_id, source_requests_known_zero=args.source_requests_known_zero, reason=args.reason)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": receipt["status"], "source_requests_known_zero": args.source_requests_known_zero}, sort_keys=True))
        return 0
    if args.mode == "verify":
        if args.input is None or args.output is None:
            parser.error("verify mode requires --input and --output")
        receipt, _ = read_json(args.input, "Q221_WAYBACK_CDX_RECEIPT_READ_FAILED")
        validate_receipt(receipt)
        validation = {
            "schema_version": 1,
            "record_type": "q221_fpds_wayback_cdx_metadata_probe_validation",
            "status": "VALIDATED_FAIL_CLOSED" if receipt["status"] != "Q221_WAYBACK_CDX_METADATA_COMPLETE" else "VALIDATED",
            "receipt_fingerprint": receipt["receipt_fingerprint"],
            "analysis_fingerprint": receipt["analysis_fingerprint"],
            "network_requests_made": 0,
            "event_level_public_boundary_proven": False,
            "historical_first_public_observation_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "scientific_evidence": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(validation, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
