"""One-shot Common Crawl CDXJ metadata probe for four frozen Q221 URL keys."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MANIFEST_PATH = "research/evidence/q221_historical_public_boundary_latest.json"
MANIFEST_BLOB_SHA1 = "b78cf6f7b48af3f914ee7c6d06a38f6485b0438f"
MANIFEST_FINGERPRINT = "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
PREREG_PATH = "research/preregistrations/q221_fpds_commoncrawl_index_metadata_probe_r1_2026_10_16.json"
REQUEST_PATH = "research/run_requests/q221_fpds_commoncrawl_index_metadata_probe.trigger"
SEQUENCE_ID = "Q221-CC-INDEX-R1-20261016-A"
ARQUIVO_PREREG_PATH = "research/preregistrations/q221_arquivo_pt_fpds_timemap_probe_r2_2026_10_16.json"
ARQUIVO_PREREG_BLOB_SHA1 = "c3e7b01175811dc22cc6ec70f87750117fab7049"
ARQUIVO_RECEIPT_PATH = "research/evidence/q221_arquivo_pt_fpds_timemap_r2_latest.json"
ARQUIVO_RECEIPT_BLOB_SHA1 = "d0d56836c4356977dfa37e515ffe2516b1e7c6d9"
ARQUIVO_RECEIPT_FINGERPRINT = "a5bb1aee620768f71bad7f05fd8af5ac123b6fe87230bd9df538999640438403"
WAYBACK_PREREG_PATH = "research/preregistrations/q221_fpds_wayback_cdx_metadata_probe_r1_2026_10_16.json"
WAYBACK_PREREG_BLOB_SHA1 = "205740eb6d64619010ba74172f80bb3ddbdf4464"
WAYBACK_RECEIPT_PATH = "research/evidence/q221_fpds_wayback_cdx_metadata_attempt_38900486932.json"
WAYBACK_RECEIPT_BLOB_SHA1 = "844dd2da40c9ca32adfccb1c2a4d2bcea590af86"
WAYBACK_RECEIPT_FINGERPRINT = "84dc038f080aafbbedb5338fa66a77781fe10619fbb1aad6e750345e6d4ca39b"
CDX_BASE = "https://index.commoncrawl.org"
MAX_REQUESTS = 4
MAX_RESPONSE_BYTES_EACH = 524_288
MAX_TOTAL_RESPONSE_BYTES = 2_097_152
MAX_ROWS_PER_URL = 50
TIMEOUT_SECONDS = 45
REQUEST_GAP_SECONDS = 1.0
OUTPUT_FIELDS = ("timestamp", "url", "status", "mime", "digest", "length", "offset", "filename")

EXPECTED_RECORDS = (
    {
        "record_id": "CACI_2019_PRE_EVENT",
        "transaction_key": "FA875018C0180|P00003|2019-01-03|28eee911-76af-7147-f760-4ec5f90bec2d-C|N3PBJAVNKF61",
        "piid": "FA875018C0180",
        "modification_number": "P00003",
        "action_date": "2019-01-03",
        "recipient_uei": "N3PBJAVNKF61",
        "original_url": "https://www.fpds.gov/dbsight/FEEDS/ATOM?FEEDNAME=PUBLIC&q=PIID%3A%22FA875018C0180%22",
        "crawl": "CC-MAIN-2018-51",
        "crawl_start_date": "2018-12-09",
        "crawl_end_date": "2018-12-19",
    },
    {
        "record_id": "BOOZ_ALLEN_2020_PRE_EVENT",
        "transaction_key": "FA807520F0004|0|2020-01-02|ffca72e5-fba2-798a-6969-2a6c45e9f985-C|JCBMLGPE6Z71",
        "piid": "FA807520F0004",
        "modification_number": "0",
        "action_date": "2020-01-02",
        "recipient_uei": "JCBMLGPE6Z71",
        "original_url": "https://www.fpds.gov/dbsight/FEEDS/ATOM?FEEDNAME=PUBLIC&q=PIID%3A%22FA807520F0004%22",
        "crawl": "CC-MAIN-2019-51",
        "crawl_start_date": "2019-12-05",
        "crawl_end_date": "2019-12-16",
    },
    {
        "record_id": "OSI_AS_E_2023_PRE_EVENT",
        "transaction_key": "70RWMD23C00000001|0|2023-01-03|f857dc49-8bdd-480e-25fb-f2be8c9d65c2-C|CNB9EF8VHML3",
        "piid": "70RWMD23C00000001",
        "modification_number": "0",
        "action_date": "2023-01-03",
        "recipient_uei": "CNB9EF8VHML3",
        "original_url": "https://www.fpds.gov/dbsight/FEEDS/ATOM?FEEDNAME=PUBLIC&q=PIID%3A%2270RWMD23C00000001%22",
        "crawl": "CC-MAIN-2022-49",
        "crawl_start_date": "2022-11-26",
        "crawl_end_date": "2022-12-10",
    },
    {
        "record_id": "NORTHROP_2024_PRE_EVENT",
        "transaction_key": "FA865124FB001|0|2024-01-02|c19bef58-16e3-f32b-b699-25b3078161f8-C|FVSEZFPCQ316",
        "piid": "FA865124FB001",
        "modification_number": "0",
        "action_date": "2024-01-02",
        "recipient_uei": "FVSEZFPCQ316",
        "original_url": "https://www.fpds.gov/dbsight/FEEDS/ATOM?FEEDNAME=PUBLIC&q=PIID%3A%22FA865124FB001%22",
        "crawl": "CC-MAIN-2023-50",
        "crawl_start_date": "2023-11-28",
        "crawl_end_date": "2023-12-12",
    },
)

EXPECTED_REQUEST_VALUES = {
    "RUN_Q221_FPDS_COMMONCRAWL_INDEX_PROBE": "true",
    "REASON": "DISTINCT_COMMONCRAWL_PRE_EVENT_INDEX_METADATA_LOOKUP_FOR_FOUR_FROZEN_URLS",
    "PREREG_PATH": PREREG_PATH,
    "SEQUENCE_ID": SEQUENCE_ID,
    "SOURCE_MANIFEST_PATH": MANIFEST_PATH,
    "SOURCE_MANIFEST_GIT_BLOB_SHA1": MANIFEST_BLOB_SHA1,
    "SOURCE_MANIFEST_RECEIPT_FINGERPRINT": MANIFEST_FINGERPRINT,
    "ARQUIVO_PREREG_GIT_BLOB_SHA1": ARQUIVO_PREREG_BLOB_SHA1,
    "ARQUIVO_RECEIPT_GIT_BLOB_SHA1": ARQUIVO_RECEIPT_BLOB_SHA1,
    "ARQUIVO_RECEIPT_FINGERPRINT": ARQUIVO_RECEIPT_FINGERPRINT,
    "WAYBACK_PREREG_GIT_BLOB_SHA1": WAYBACK_PREREG_BLOB_SHA1,
    "WAYBACK_RECEIPT_GIT_BLOB_SHA1": WAYBACK_RECEIPT_BLOB_SHA1,
    "WAYBACK_RECEIPT_FINGERPRINT": WAYBACK_RECEIPT_FINGERPRINT,
    "MAX_REQUESTS": str(MAX_REQUESTS),
    "MAX_RESPONSE_BYTES_EACH": str(MAX_RESPONSE_BYTES_EACH),
    "MAX_TOTAL_RESPONSE_BYTES": str(MAX_TOTAL_RESPONSE_BYTES),
    "MAX_ROWS_PER_URL": str(MAX_ROWS_PER_URL),
    "REQUEST_TIMEOUT_SECONDS": str(TIMEOUT_SECONDS),
    "MIN_REQUEST_GAP_SECONDS": "1",
    "MATCH_TYPE": "exact",
    "OUTPUT": "json",
    "AUTOMATIC_RETRIES": "0",
    "FOLLOW_REDIRECTS": "false",
    "DIRECT_FPDS_REQUESTS": "0",
    "WAYBACK_REQUESTS": "0",
    "ARQUIVO_PT_REQUESTS": "0",
    "SAM_API_REQUESTS": "0",
    "USASPENDING_REQUESTS": "0",
    "SEC_REQUESTS": "0",
    "COMMONCRAWL_WARC_RANGE_REQUESTS": "0",
    "COMMONCRAWL_WARC_PAYLOADS_DOWNLOADED": "false",
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
}

REQUIRED_CAPTURE_FIELDS = ("timestamp", "url", "status", "mime", "digest", "length", "offset", "filename")


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
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(encoded)


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
        raise ProbeError("Q221_COMMONCRAWL_REQUEST_MARKER_MISSING", type(exc).__name__) from exc
    values: dict[str, str] = {}
    for line_number, line in enumerate(lines, start=1):
        if not line or line.strip() != line or "=" not in line:
            raise ProbeError("Q221_COMMONCRAWL_REQUEST_MARKER_INVALID_LINE", str(line_number))
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key) or not value or key in values:
            raise ProbeError("Q221_COMMONCRAWL_REQUEST_MARKER_INVALID_KEY_VALUE", str(line_number))
        values[key] = value
    if values != EXPECTED_REQUEST_VALUES:
        raise ProbeError("Q221_COMMONCRAWL_REQUEST_MARKER_PIN_MISMATCH")
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
            raise ProbeError("Q221_COMMONCRAWL_PATH_OUTSIDE_REPOSITORY") from exc
    if prereg_path.resolve() != (repo_root / PREREG_PATH).resolve():
        raise ProbeError("Q221_COMMONCRAWL_PREREG_PATH_MISMATCH")

    marker = read_marker(request_path)
    prereg, prereg_raw = read_json(prereg_path, "Q221_COMMONCRAWL_PREREG_INVALID")
    if prereg.get("schema_version") != 1 or prereg.get("record_type") != "q221_fpds_commoncrawl_index_metadata_probe_preregistration":
        raise ProbeError("Q221_COMMONCRAWL_PREREG_IDENTITY_MISMATCH")
    if prereg.get("candidate_id") != "Q221" or prereg.get("study_mode") != "BOUNDED_PRE_EVENT_ARCHIVE_INDEX_METADATA_ONLY":
        raise ProbeError("Q221_COMMONCRAWL_PREREG_MODE_MISMATCH")
    if prereg.get("sequence_id") != marker["SEQUENCE_ID"] or marker["SEQUENCE_ID"] != SEQUENCE_ID:
        raise ProbeError("Q221_COMMONCRAWL_SEQUENCE_ID_MISMATCH")
    if prereg.get("records") != list(EXPECTED_RECORDS):
        raise ProbeError("Q221_COMMONCRAWL_FROZEN_RECORDS_MISMATCH")

    frozen = prereg.get("frozen_inputs", {})
    expected_frozen = {
        "boundary_path": MANIFEST_PATH,
        "boundary_git_blob_sha1": MANIFEST_BLOB_SHA1,
        "boundary_receipt_fingerprint": MANIFEST_FINGERPRINT,
        "arquivo_prereg_path": ARQUIVO_PREREG_PATH,
        "arquivo_prereg_git_blob_sha1": ARQUIVO_PREREG_BLOB_SHA1,
        "arquivo_receipt_path": ARQUIVO_RECEIPT_PATH,
        "arquivo_receipt_git_blob_sha1": ARQUIVO_RECEIPT_BLOB_SHA1,
        "arquivo_receipt_fingerprint": ARQUIVO_RECEIPT_FINGERPRINT,
        "wayback_prereg_path": WAYBACK_PREREG_PATH,
        "wayback_prereg_git_blob_sha1": WAYBACK_PREREG_BLOB_SHA1,
        "wayback_receipt_path": WAYBACK_RECEIPT_PATH,
        "wayback_receipt_git_blob_sha1": WAYBACK_RECEIPT_BLOB_SHA1,
        "wayback_receipt_fingerprint": WAYBACK_RECEIPT_FINGERPRINT,
        "transaction_key_count": 4,
    }
    if frozen != expected_frozen:
        raise ProbeError("Q221_COMMONCRAWL_FROZEN_INPUTS_MISMATCH")

    manifest, manifest_raw = read_json(repo_root / MANIFEST_PATH, "Q221_COMMONCRAWL_MANIFEST_INVALID")
    if git_blob_sha1(manifest_raw) != MANIFEST_BLOB_SHA1 or manifest.get("candidate_id") != "Q221":
        raise ProbeError("Q221_COMMONCRAWL_MANIFEST_BLOB_MISMATCH")
    if manifest.get("receipt_fingerprint") != MANIFEST_FINGERPRINT:
        raise ProbeError("Q221_COMMONCRAWL_MANIFEST_FINGERPRINT_MISMATCH")
    if manifest.get("historical_first_public_observation_proven") is not False:
        raise ProbeError("Q221_COMMONCRAWL_MANIFEST_GATE_UNEXPECTEDLY_OPEN")
    manifest_strings = set(walk_strings(manifest))
    if any(record["transaction_key"] not in manifest_strings for record in EXPECTED_RECORDS):
        raise ProbeError("Q221_COMMONCRAWL_KEY_NOT_IN_FROZEN_MANIFEST")

    arquivo_prereg, arquivo_prereg_raw = read_json(repo_root / ARQUIVO_PREREG_PATH, "Q221_COMMONCRAWL_ARQUIVO_PREREG_INVALID")
    if git_blob_sha1(arquivo_prereg_raw) != ARQUIVO_PREREG_BLOB_SHA1:
        raise ProbeError("Q221_COMMONCRAWL_ARQUIVO_PREREG_BLOB_MISMATCH")
    if arquivo_prereg.get("record_type") != "q221_arquivo_pt_fpds_timemap_probe_preregistration":
        raise ProbeError("Q221_COMMONCRAWL_ARQUIVO_PREREG_TYPE_MISMATCH")
    arquivo_rows = {row.get("record_id"): row for row in arquivo_prereg.get("records", [])}
    for record in EXPECTED_RECORDS:
        old = arquivo_rows.get(record["record_id"], {})
        for field in ("transaction_key", "piid", "modification_number", "action_date", "recipient_uei"):
            if old.get(field) != record.get(field):
                raise ProbeError("Q221_COMMONCRAWL_ARQUIVO_PIN_MISMATCH:" + record["record_id"])
        if old.get("source_url") != record["original_url"]:
            raise ProbeError("Q221_COMMONCRAWL_ARQUIVO_URL_PIN_MISMATCH:" + record["record_id"])

    arquivo_receipt, arquivo_receipt_raw = read_json(repo_root / ARQUIVO_RECEIPT_PATH, "Q221_COMMONCRAWL_ARQUIVO_RECEIPT_INVALID")
    if git_blob_sha1(arquivo_receipt_raw) != ARQUIVO_RECEIPT_BLOB_SHA1:
        raise ProbeError("Q221_COMMONCRAWL_ARQUIVO_RECEIPT_BLOB_MISMATCH")
    if arquivo_receipt.get("receipt_fingerprint") != ARQUIVO_RECEIPT_FINGERPRINT:
        raise ProbeError("Q221_COMMONCRAWL_ARQUIVO_RECEIPT_FINGERPRINT_MISMATCH")
    if arquivo_receipt.get("status") != "Q221_ARQUIVO_PT_TIMEMAP_METADATA_INCOMPLETE":
        raise ProbeError("Q221_COMMONCRAWL_ARQUIVO_RECEIPT_STATUS_MISMATCH")

    wayback_prereg, wayback_prereg_raw = read_json(repo_root / WAYBACK_PREREG_PATH, "Q221_COMMONCRAWL_WAYBACK_PREREG_INVALID")
    if git_blob_sha1(wayback_prereg_raw) != WAYBACK_PREREG_BLOB_SHA1:
        raise ProbeError("Q221_COMMONCRAWL_WAYBACK_PREREG_BLOB_MISMATCH")
    if wayback_prereg.get("record_type") != "q221_fpds_wayback_cdx_metadata_probe_preregistration":
        raise ProbeError("Q221_COMMONCRAWL_WAYBACK_PREREG_TYPE_MISMATCH")
    wayback_rows = {row.get("record_id"): row for row in wayback_prereg.get("records", [])}
    for record in EXPECTED_RECORDS:
        old = wayback_rows.get(record["record_id"], {})
        for field in ("transaction_key", "piid", "modification_number", "action_date", "recipient_uei"):
            if old.get(field) != record.get(field):
                raise ProbeError("Q221_COMMONCRAWL_WAYBACK_PIN_MISMATCH:" + record["record_id"])
        if old.get("source_url") != record["original_url"]:
            raise ProbeError("Q221_COMMONCRAWL_WAYBACK_URL_PIN_MISMATCH:" + record["record_id"])

    wayback_receipt, wayback_receipt_raw = read_json(repo_root / WAYBACK_RECEIPT_PATH, "Q221_COMMONCRAWL_WAYBACK_RECEIPT_INVALID")
    if git_blob_sha1(wayback_receipt_raw) != WAYBACK_RECEIPT_BLOB_SHA1:
        raise ProbeError("Q221_COMMONCRAWL_WAYBACK_RECEIPT_BLOB_MISMATCH")
    if wayback_receipt.get("receipt_fingerprint") != WAYBACK_RECEIPT_FINGERPRINT:
        raise ProbeError("Q221_COMMONCRAWL_WAYBACK_RECEIPT_FINGERPRINT_MISMATCH")
    if wayback_receipt.get("status") != "Q221_WAYBACK_CDX_METADATA_INCOMPLETE":
        raise ProbeError("Q221_COMMONCRAWL_WAYBACK_RECEIPT_STATUS_MISMATCH")

    expected_contract = {
        "request_count_exact": 4,
        "request_order": "CACI_2019_PRE_EVENT, BOOZ_ALLEN_2020_PRE_EVENT, OSI_AS_E_2023_PRE_EVENT, NORTHROP_2024_PRE_EVENT",
        "max_response_bytes_each": MAX_RESPONSE_BYTES_EACH,
        "max_total_response_bytes": MAX_TOTAL_RESPONSE_BYTES,
        "max_rows_per_url": MAX_ROWS_PER_URL,
        "timeout_seconds": TIMEOUT_SECONDS,
        "minimum_request_gap_seconds": 1,
        "automatic_retries": 0,
        "redirects_followed": False,
        "match_type": "exact",
        "output": "json",
        "direct_fpds_requests": 0,
        "wayback_requests": 0,
        "arquivo_pt_requests": 0,
        "sam_api_requests": 0,
        "usaspending_requests": 0,
        "sec_requests": 0,
        "commoncrawl_warc_range_requests": 0,
        "commoncrawl_warc_payloads_downloaded": 0,
        "response_bodies_persisted": False,
    }
    if prereg.get("request_contract") != expected_contract:
        raise ProbeError("Q221_COMMONCRAWL_REQUEST_CONTRACT_MISMATCH")
    for key in (
        "live_trading_enabled", "orders_enabled", "automatic_promotion", "source_population_changes",
        "frozen_transaction_rows_modified", "recipient_identity_mappings_added", "historical_first_public_observation_proven",
        "event_level_public_boundary_proven", "recipient_to_issuer_mapping_frozen", "scientific_evidence",
        "performance_authorization", "holdout_selection", "ranking", "tuning", "promotion", "live_execution",
    ):
        if prereg.get("safety", {}).get(key) is not False:
            raise ProbeError("Q221_COMMONCRAWL_SAFETY_MISMATCH:" + key)
    if prereg.get("safety", {}).get("paper_only") is not True:
        raise ProbeError("Q221_COMMONCRAWL_PAPER_ONLY_FALSE")

    # The pinned crawl windows must be strictly pre-event.
    for record in EXPECTED_RECORDS:
        if record["crawl_end_date"] >= record["action_date"]:
            raise ProbeError("Q221_COMMONCRAWL_CRAWL_NOT_PRE_EVENT:" + record["record_id"])

    return {
        "status": "Q221_COMMONCRAWL_FROZEN_INPUTS_VALID",
        "request_count": 0,
        "source_requests_made": 0,
        "manifest_blob_sha1": git_blob_sha1(manifest_raw),
        "arquivo_prereg_blob_sha1": git_blob_sha1(arquivo_prereg_raw),
        "arquivo_receipt_blob_sha1": git_blob_sha1(arquivo_receipt_raw),
        "wayback_prereg_blob_sha1": git_blob_sha1(wayback_prereg_raw),
        "wayback_receipt_blob_sha1": git_blob_sha1(wayback_receipt_raw),
        "preregistration_blob_sha1": git_blob_sha1(prereg_raw),
        "records_validated": len(EXPECTED_RECORDS),
        "paper_only": True,
        "historical_first_public_observation_proven": False,
        "event_level_public_boundary_proven": False,
        "recipient_to_issuer_mapping_frozen": False,
    }


def build_index_url(record: dict[str, Any]) -> str:
    query = urllib.parse.urlencode(
        {
            "url": record["original_url"],
            "matchType": "exact",
            "output": "json",
            "limit": str(MAX_ROWS_PER_URL),
        },
        quote_via=urllib.parse.quote_plus,
    )
    return f"{CDX_BASE}/{record['crawl']}-index?{query}"


def parse_jsonl_body(raw: bytes, record: dict[str, Any]) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProbeError("Q221_COMMONCRAWL_JSONL_INVALID_UTF8", type(exc).__name__) from exc
    if not text.strip():
        return {
            "query_completed": True,
            "status": "COMMONCRAWL_INDEX_VALID_EMPTY",
            "capture_count": 0,
            "exact_url_capture_count": 0,
            "exact_url_http_200_capture_count": 0,
            "captures": [],
        }
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) > MAX_ROWS_PER_URL:
        raise ProbeError("Q221_COMMONCRAWL_ROW_LIMIT_EXCEEDED")
    captures: list[dict[str, str]] = []
    for index, line in enumerate(lines):
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProbeError("Q221_COMMONCRAWL_JSONL_ROW_INVALID:" + str(index), type(exc).__name__) from exc
        if not isinstance(item, dict) or any(field not in item for field in REQUIRED_CAPTURE_FIELDS):
            raise ProbeError("Q221_COMMONCRAWL_CAPTURE_FIELDS_MISSING:" + str(index))
        if item["url"] != record["original_url"]:
            raise ProbeError("Q221_COMMONCRAWL_NONEXACT_URL_RETURNED:" + str(index))
        if not isinstance(item["timestamp"], str) or not re.fullmatch(r"\d{14}", item["timestamp"]):
            raise ProbeError("Q221_COMMONCRAWL_TIMESTAMP_INVALID:" + str(index))
        if not isinstance(item["status"], str) or not re.fullmatch(r"\d{3}", item["status"]):
            raise ProbeError("Q221_COMMONCRAWL_STATUS_INVALID:" + str(index))
        if not isinstance(item["mime"], str) or not item["mime"] or not isinstance(item["digest"], str):
            raise ProbeError("Q221_COMMONCRAWL_MIME_OR_DIGEST_INVALID:" + str(index))
        if not str(item["length"]).isdigit() or not str(item["offset"]).isdigit():
            raise ProbeError("Q221_COMMONCRAWL_LENGTH_OR_OFFSET_INVALID:" + str(index))
        expected_prefix = f"crawl-data/{record['crawl']}/segments/"
        if not isinstance(item["filename"], str) or not item["filename"].startswith(expected_prefix) or "/warc/" not in item["filename"]:
            raise ProbeError("Q221_COMMONCRAWL_FILENAME_COLLECTION_MISMATCH:" + str(index))
        captures.append({field: str(item[field]) for field in REQUIRED_CAPTURE_FIELDS})
    return {
        "query_completed": True,
        "status": "COMMONCRAWL_INDEX_METADATA_VALID",
        "capture_count": len(captures),
        "exact_url_capture_count": len(captures),
        "exact_url_http_200_capture_count": sum(row["status"] == "200" for row in captures),
        "captures": captures,
    }


def empty_observation(record: dict[str, Any], status: str, http_status: int | None = None) -> dict[str, Any]:
    return {
        "record_id": record["record_id"],
        "transaction_key": record["transaction_key"],
        "original_url": record["original_url"],
        "crawl": record["crawl"],
        "crawl_start_date": record["crawl_start_date"],
        "crawl_end_date": record["crawl_end_date"],
        "action_date": record["action_date"],
        "method": "GET",
        "requested_host": "index.commoncrawl.org",
        "http_status": http_status,
        "content_type": None,
        "response_bytes": 0,
        "response_sha256": None,
        "response_body_persisted": False,
        "query_completed": False,
        "status": status,
        "capture_count": 0,
        "exact_url_capture_count": 0,
        "exact_url_http_200_capture_count": 0,
        "captures": [],
    }


def fetch_one(opener: urllib.request.OpenerDirector, record: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        build_index_url(record),
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "TradingAgentOS-Q221-CommonCrawl-Index-Metadata/1.0",
        },
        method="GET",
    )
    try:
        response = opener.open(request, timeout=TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        return empty_observation(record, "HTTP_" + str(exc.code), int(exc.code))
    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        timed_out = isinstance(exc, (TimeoutError, socket.timeout)) or isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout))
        item = empty_observation(record, "TIMEOUT" if timed_out else "NETWORK_ERROR")
        item["error_class"] = type(exc).__name__
        return item
    except Exception as exc:
        item = empty_observation(record, "CLIENT_ERROR")
        item["error_class"] = type(exc).__name__
        return item

    with response:
        code = int(response.getcode())
        ctype = response.headers.get("Content-Type")
        if code != 200:
            return empty_observation(record, "HTTP_" + str(code), code)
        raw = response.read(MAX_RESPONSE_BYTES_EACH)
    item = empty_observation(record, "COMMONCRAWL_INDEX_METADATA_VALID", code)
    item["content_type"] = ctype
    item["response_bytes"] = len(raw)
    item["response_sha256"] = sha256(raw)
    if len(raw) >= MAX_RESPONSE_BYTES_EACH:
        item["status"] = "RESPONSE_AT_OR_OVER_LIMIT"
        return item
    try:
        parsed = parse_jsonl_body(raw, record)
    except ProbeError as exc:
        item["status"] = exc.code
        return item
    item.update(parsed)
    item["response_body_persisted"] = False
    return item


def build_receipt(observations: list[dict[str, Any]], run_id: int | None, prereg_blob_sha1: str | None) -> dict[str, Any]:
    complete = len(observations) == MAX_REQUESTS and all(row.get("query_completed") is True for row in observations)
    bytes_total = sum(int(row.get("response_bytes") or 0) for row in observations)
    captures_total = sum(int(row.get("capture_count") or 0) for row in observations)
    captures_200 = sum(int(row.get("exact_url_http_200_capture_count") or 0) for row in observations)
    if captures_200:
        next_gate = "Separately preregister an exact, bounded WARC range inspection for each selected capture; verify the frozen transaction tuple and retain the indexed capture timestamp only as an archive observation, not as first-public proof."
    elif complete:
        next_gate = "No exact-URL HTTP 200 capture was returned across these four pre-event collections; preserve the negative index result and seek a different, separately reviewed historical transaction source. Do not infer historical absence."
    else:
        next_gate = "Preserve the fail-closed index response; do not retry or fetch WARC bytes. Any changed query requires a separate preregistration."
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q221_fpds_commoncrawl_index_metadata_probe",
        "candidate_id": "Q221",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_run_id": run_id,
        "sequence_id": SEQUENCE_ID,
        "preregistration_path": PREREG_PATH,
        "preregistration_git_blob_sha1": prereg_blob_sha1,
        "request_marker_path": REQUEST_PATH,
        "frozen_inputs": {
            "boundary_path": MANIFEST_PATH,
            "boundary_git_blob_sha1": MANIFEST_BLOB_SHA1,
            "boundary_receipt_fingerprint": MANIFEST_FINGERPRINT,
            "arquivo_prereg_git_blob_sha1": ARQUIVO_PREREG_BLOB_SHA1,
            "arquivo_receipt_git_blob_sha1": ARQUIVO_RECEIPT_BLOB_SHA1,
            "arquivo_receipt_fingerprint": ARQUIVO_RECEIPT_FINGERPRINT,
            "wayback_prereg_git_blob_sha1": WAYBACK_PREREG_BLOB_SHA1,
            "wayback_receipt_git_blob_sha1": WAYBACK_RECEIPT_BLOB_SHA1,
            "wayback_receipt_fingerprint": WAYBACK_RECEIPT_FINGERPRINT,
        },
        "source_contract": {
            "endpoint": CDX_BASE,
            "index_metadata_requests_attempted": len(observations),
            "request_count_known": True,
            "max_requests": MAX_REQUESTS,
            "max_response_bytes_each": MAX_RESPONSE_BYTES_EACH,
            "max_total_response_bytes": MAX_TOTAL_RESPONSE_BYTES,
            "max_rows_per_url": MAX_ROWS_PER_URL,
            "response_bytes_total": bytes_total,
            "automatic_retries": 0,
            "redirects_followed": False,
            "direct_fpds_requests": 0,
            "wayback_requests": 0,
            "arquivo_pt_requests": 0,
            "sam_api_requests": 0,
            "usaspending_requests": 0,
            "sec_requests": 0,
            "commoncrawl_warc_range_requests": 0,
            "commoncrawl_warc_payloads_downloaded": 0,
            "response_bodies_persisted": False,
        },
        "aggregate": {
            "metadata_lookup_complete": complete,
            "queries_completed": sum(int(row.get("query_completed") is True) for row in observations),
            "capture_metadata_row_count": captures_total,
            "exact_url_http_200_capture_metadata_count": captures_200,
            "historical_first_public_observation_proven": False,
            "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "q221_gate_positive": False,
        },
        "observations": observations,
        "interpretation": {
            "metadata_only": True,
            "archive_timestamps_are_not_first_public_timestamps": True,
            "empty_or_failed_lookup_is_not_proof_of_historical_absence": True,
            "event_level_public_boundary_proven": False,
            "historical_first_public_observation_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "scientific_evidence": False,
        },
        "next_gate": next_gate,
        "status": "Q221_COMMONCRAWL_INDEX_METADATA_COMPLETE" if complete else "Q221_COMMONCRAWL_INDEX_METADATA_INCOMPLETE",
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "source_population_changes": False,
            "frozen_transaction_rows_modified": False,
            "recipient_identity_mappings_added": False,
            "historical_first_public_observation_proven": False,
            "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "scientific_evidence": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
    }
    receipt["analysis_fingerprint"] = analysis_fingerprint(receipt)
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    return receipt


def build_fallback_receipt(run_id: int | None, *, request_count_known_zero: bool, reason: str) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q221_fpds_commoncrawl_index_metadata_probe",
        "candidate_id": "Q221",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_run_id": run_id,
        "sequence_id": SEQUENCE_ID,
        "preregistration_path": PREREG_PATH,
        "preregistration_git_blob_sha1": None,
        "request_marker_path": REQUEST_PATH,
        "source_contract": {
            "endpoint": CDX_BASE,
            "index_metadata_requests_attempted": 0 if request_count_known_zero else None,
            "request_count_known": request_count_known_zero,
            "max_requests": MAX_REQUESTS,
            "automatic_retries": 0,
            "redirects_followed": False,
            "direct_fpds_requests": 0,
            "wayback_requests": 0,
            "arquivo_pt_requests": 0,
            "sam_api_requests": 0,
            "usaspending_requests": 0,
            "sec_requests": 0,
            "commoncrawl_warc_range_requests": 0,
            "commoncrawl_warc_payloads_downloaded": 0,
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
        "status": "PREFLIGHT_FAILED_NO_SOURCE_REQUESTS" if request_count_known_zero else "CAPTURE_ABORTED_REQUEST_COUNT_UNKNOWN",
        "fallback_reason_code": reason,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "source_population_changes": False,
            "frozen_transaction_rows_modified": False,
            "recipient_identity_mappings_added": False,
            "historical_first_public_observation_proven": False,
            "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "scientific_evidence": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
    }
    receipt["analysis_fingerprint"] = analysis_fingerprint(receipt)
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    return receipt


def validate_receipt(receipt: dict[str, Any]) -> None:
    if receipt.get("schema_version") != 1 or receipt.get("record_type") != "q221_fpds_commoncrawl_index_metadata_probe":
        raise ProbeError("Q221_COMMONCRAWL_RECEIPT_TYPE_INVALID")
    if receipt.get("receipt_fingerprint") != canonical_fingerprint(receipt):
        raise ProbeError("Q221_COMMONCRAWL_RECEIPT_FINGERPRINT_MISMATCH")
    if receipt.get("analysis_fingerprint") != analysis_fingerprint(receipt):
        raise ProbeError("Q221_COMMONCRAWL_ANALYSIS_FINGERPRINT_MISMATCH")
    safety = receipt.get("safety", {})
    for key in (
        "live_trading_enabled", "orders_enabled", "automatic_promotion", "source_population_changes",
        "frozen_transaction_rows_modified", "recipient_identity_mappings_added", "historical_first_public_observation_proven",
        "event_level_public_boundary_proven", "recipient_to_issuer_mapping_frozen", "scientific_evidence",
        "performance_authorization", "holdout_selection", "ranking", "tuning", "promotion", "live_execution",
    ):
        if safety.get(key) is not False:
            raise ProbeError("Q221_COMMONCRAWL_RECEIPT_SAFETY_MISMATCH:" + key)
    if safety.get("paper_only") is not True:
        raise ProbeError("Q221_COMMONCRAWL_RECEIPT_PAPER_ONLY_FALSE")
    contract = receipt.get("source_contract", {})
    for key in ("direct_fpds_requests", "wayback_requests", "arquivo_pt_requests", "sam_api_requests", "usaspending_requests", "sec_requests", "commoncrawl_warc_range_requests", "commoncrawl_warc_payloads_downloaded"):
        if contract.get(key) != 0:
            raise ProbeError("Q221_COMMONCRAWL_RECEIPT_SCOPE_VIOLATION:" + key)
    if contract.get("response_bodies_persisted") is not False:
        raise ProbeError("Q221_COMMONCRAWL_RESPONSE_BODY_PERSISTED")
    status = receipt.get("status")
    if status in {"Q221_COMMONCRAWL_INDEX_METADATA_COMPLETE", "Q221_COMMONCRAWL_INDEX_METADATA_INCOMPLETE"}:
        observations = receipt.get("observations")
        if not isinstance(observations, list) or len(observations) != MAX_REQUESTS:
            raise ProbeError("Q221_COMMONCRAWL_OBSERVATION_COUNT_INVALID")
        total = 0
        for index, (observation, expected) in enumerate(zip(observations, EXPECTED_RECORDS)):
            if observation.get("record_id") != expected["record_id"] or observation.get("transaction_key") != expected["transaction_key"]:
                raise ProbeError("Q221_COMMONCRAWL_RECEIPT_FROZEN_ROW_MISMATCH:" + str(index))
            if observation.get("original_url") != expected["original_url"] or observation.get("crawl") != expected["crawl"]:
                raise ProbeError("Q221_COMMONCRAWL_RECEIPT_URL_OR_CRAWL_MISMATCH:" + str(index))
            if observation.get("requested_host") != "index.commoncrawl.org" or observation.get("response_body_persisted") is not False:
                raise ProbeError("Q221_COMMONCRAWL_RECEIPT_SCOPE_METADATA_MISMATCH:" + str(index))
            size = observation.get("response_bytes")
            if not isinstance(size, int) or size < 0 or size > MAX_RESPONSE_BYTES_EACH:
                raise ProbeError("Q221_COMMONCRAWL_RECEIPT_BYTE_COUNT_INVALID:" + str(index))
            total += size
            for capture in observation.get("captures", []):
                if set(capture) != set(REQUIRED_CAPTURE_FIELDS):
                    raise ProbeError("Q221_COMMONCRAWL_RECEIPT_CAPTURE_FIELDS_INVALID")
                if capture.get("url") != expected["original_url"]:
                    raise ProbeError("Q221_COMMONCRAWL_RECEIPT_NONEXACT_CAPTURE")
                if not str(capture.get("filename", "")).startswith(f"crawl-data/{expected['crawl']}/segments/"):
                    raise ProbeError("Q221_COMMONCRAWL_RECEIPT_CAPTURE_CRAWL_MISMATCH")
        if total > MAX_TOTAL_RESPONSE_BYTES:
            raise ProbeError("Q221_COMMONCRAWL_RECEIPT_TOTAL_BYTES_EXCEEDED")
        if receipt.get("aggregate", {}).get("historical_first_public_observation_proven") is not False:
            raise ProbeError("Q221_COMMONCRAWL_RECEIPT_GATE_FLAGS_INVALID")
    elif status in {"PREFLIGHT_FAILED_NO_SOURCE_REQUESTS", "CAPTURE_ABORTED_REQUEST_COUNT_UNKNOWN"}:
        if receipt.get("observations") != []:
            raise ProbeError("Q221_COMMONCRAWL_FALLBACK_HAS_OBSERVATIONS")
        if status == "PREFLIGHT_FAILED_NO_SOURCE_REQUESTS":
            if contract.get("request_count_known") is not True or contract.get("index_metadata_requests_attempted") != 0:
                raise ProbeError("Q221_COMMONCRAWL_PREFLIGHT_FALLBACK_REQUEST_COUNT_INVALID")
        elif contract.get("request_count_known") is not False:
            raise ProbeError("Q221_COMMONCRAWL_CAPTURE_FALLBACK_REQUEST_COUNT_INVALID")
    else:
        raise ProbeError("Q221_COMMONCRAWL_RECEIPT_STATUS_INVALID")


def capture(repo_root: Path, request_path: Path, prereg_path: Path, run_id: int, output: Path) -> int:
    validate_preflight(repo_root, request_path, prereg_path)
    opener = urllib.request.build_opener(NoRedirect())
    observations: list[dict[str, Any]] = []
    last_start: float | None = None
    for record in EXPECTED_RECORDS:
        if last_start is not None:
            delay = REQUEST_GAP_SECONDS - (time.monotonic() - last_start)
            if delay > 0:
                time.sleep(delay)
        last_start = time.monotonic()
        observations.append(fetch_one(opener, record))
    prereg_raw = (repo_root / prereg_path).read_bytes()
    receipt = build_receipt(observations, run_id, git_blob_sha1(prereg_raw))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "index_metadata_requests_attempted": receipt["source_contract"]["index_metadata_requests_attempted"],
        "queries_completed": receipt["aggregate"]["queries_completed"],
        "capture_metadata_row_count": receipt["aggregate"]["capture_metadata_row_count"],
        "direct_fpds_requests": 0,
        "warc_range_requests": 0,
        "paper_only": True,
    }, sort_keys=True))
    return 0 if receipt["status"] == "Q221_COMMONCRAWL_INDEX_METADATA_COMPLETE" else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("validate-only", "capture", "fallback", "verify"), required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--request", type=Path, default=Path(REQUEST_PATH))
    parser.add_argument("--prereg", type=Path, default=Path(PREREG_PATH))
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--request-count-known-zero", action="store_true")
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
        receipt = build_fallback_receipt(args.run_id, request_count_known_zero=args.request_count_known_zero, reason=args.reason)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": receipt["status"], "request_count_known_zero": args.request_count_known_zero}, sort_keys=True))
        return 0
    if args.mode == "verify":
        if args.input is None or args.output is None:
            parser.error("verify mode requires --input and --output")
        receipt, _ = read_json(args.input, "Q221_COMMONCRAWL_RECEIPT_READ_FAILED")
        validate_receipt(receipt)
        validation = {
            "schema_version": 1,
            "record_type": "q221_fpds_commoncrawl_index_metadata_probe_validation",
            "status": "VALIDATED_FAIL_CLOSED" if receipt["status"] != "Q221_COMMONCRAWL_INDEX_METADATA_COMPLETE" else "VALIDATED",
            "receipt_fingerprint": receipt["receipt_fingerprint"],
            "analysis_fingerprint": receipt["analysis_fingerprint"],
            "network_requests_made": 0,
            "historical_first_public_observation_proven": False,
            "event_level_public_boundary_proven": False,
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
