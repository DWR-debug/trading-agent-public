"""Bounded Arquivo.pt Memento TimeMap metadata probe for four frozen Q221 FPDS URLs.

No FPDS/SAM.gov/USAspending/SEC requests are made. Archived replay URLs and
origin URLs are never opened. TimeMap responses are parsed in memory; the
receipt stores only capture metadata and response digests, never raw bodies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REQUEST_PATH = "research/run_requests/q221_arquivo_pt_fpds_timemap_probe.trigger"
PREREG_PATH = "research/preregistrations/q221_arquivo_pt_fpds_timemap_probe_2026_10_16.json"
BOUNDARY_PATH = "research/evidence/q221_historical_public_boundary_latest.json"
PRE_EVENT_PATH = "research/evidence/q221_pre_event_parent_identity_feasibility_latest.json"
PRIOR_FPDS_PATH = "research/evidence/q221_fpds_public_atom_identity_bridge_latest.json"
BOUNDARY_BLOB_SHA1 = "b78cf6f7b48af3f914ee7c6d06a38f6485b0438f"
BOUNDARY_FP = "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
PRE_EVENT_FP = "7b969cc7dd0a5c5e94050c9e99b797e59b77d20712e51661b1b281fb170dd953"
PRE_EVENT_ANALYSIS_FP = "75a9818d18436dbf24beb877b00431c0c46015cad4a35efc66a07e2d9c69832f"
PRIOR_FPDS_BLOB_SHA1 = "af5cb7aaeec92b162ad69817df4917687cdfcf56"
PRIOR_FPDS_FP = "f041edf725388a47aeb1ec96076bfbffcdc8946acc87fb4c8cb515f8c3c03817"
PRIOR_FPDS_CAPTURE_FP = "77966d35322e4b4a2fb4d67da27adb43a3ad9f3f854242a83696899709983c8f"
TIME_MAP_BASE_URL = "https://arquivo.pt/wayback/timemap/json/"
ALLOWED_ARCHIVE_HOST = "arquivo.pt"
MAX_REQUESTS = 4
MAX_RESPONSE_BYTES_EACH = 500_000
MAX_TOTAL_RESPONSE_BYTES = 2_000_000
MAX_ROWS_PER_URL = 500
TIMEOUT_SECONDS = 35
REQUEST_GAP_SECONDS = 1.0

EXPECTED_RECORDS = (
    {
        "record_id": "CACI_2019_PRE_EVENT",
        "transaction_key": "FA875018C0180|P00003|2019-01-03|28eee911-76af-7147-f760-4ec5f90bec2d-C|N3PBJAVNKF61",
        "piid": "FA875018C0180",
        "modification_number": "P00003",
        "action_date": "2019-01-03",
        "recipient_uei": "N3PBJAVNKF61",
        "recipient_id": "28eee911-76af-7147-f760-4ec5f90bec2d-C",
        "accepted_legal_names": ["CACI, INC. - FEDERAL"],
        "pre_event_accession": "0001564590-18-022021",
        "identifier_regime_at_action": "DUNS_AUTHORITATIVE_UEI_NOT_YET_AUTHORITATIVE",
        "source_url": "https://www.fpds.gov/dbsight/FEEDS/ATOM?FEEDNAME=PUBLIC&q=PIID%3A%22FA875018C0180%22",
    },
    {
        "record_id": "BOOZ_ALLEN_2020_PRE_EVENT",
        "transaction_key": "FA807520F0004|0|2020-01-02|ffca72e5-fba2-798a-6969-2a6c45e9f985-C|JCBMLGPE6Z71",
        "piid": "FA807520F0004",
        "modification_number": "0",
        "action_date": "2020-01-02",
        "recipient_uei": "JCBMLGPE6Z71",
        "recipient_id": "ffca72e5-fba2-798a-6969-2a6c45e9f985-C",
        "accepted_legal_names": ["BOOZ ALLEN HAMILTON INC", "Booz Allen Hamilton Inc."],
        "pre_event_accession": "0001443646-18-000100",
        "identifier_regime_at_action": "DUNS_AUTHORITATIVE_UEI_NOT_YET_AUTHORITATIVE",
        "source_url": "https://www.fpds.gov/dbsight/FEEDS/ATOM?FEEDNAME=PUBLIC&q=PIID%3A%22FA807520F0004%22",
    },
    {
        "record_id": "OSI_AS_E_2023_PRE_EVENT",
        "transaction_key": "70RWMD23C00000001|0|2023-01-03|f857dc49-8bdd-480e-25fb-f2be8c9d65c2-C|CNB9EF8VHML3",
        "piid": "70RWMD23C00000001",
        "modification_number": "0",
        "action_date": "2023-01-03",
        "recipient_uei": "CNB9EF8VHML3",
        "recipient_id": "f857dc49-8bdd-480e-25fb-f2be8c9d65c2-C",
        "accepted_legal_names": ["AMERICAN SCIENCE & ENGINEERING INC", "American Science and Engineering, Inc."],
        "pre_event_accession": "0001104659-22-092999",
        "identifier_regime_at_action": "UEI_AUTHORITATIVE",
        "source_url": "https://www.fpds.gov/dbsight/FEEDS/ATOM?FEEDNAME=PUBLIC&q=PIID%3A%2270RWMD23C00000001%22",
    },
    {
        "record_id": "NORTHROP_2024_PRE_EVENT",
        "transaction_key": "FA865124FB001|0|2024-01-02|c19bef58-16e3-f32b-b699-25b3078161f8-C|FVSEZFPCQ316",
        "piid": "FA865124FB001",
        "modification_number": "0",
        "action_date": "2024-01-02",
        "recipient_uei": "FVSEZFPCQ316",
        "recipient_id": "c19bef58-16e3-f32b-b699-25b3078161f8-C",
        "accepted_legal_names": ["NORTHROP GRUMMAN SYSTEMS CORPORATION", "Northrop Grumman Systems Corporation"],
        "pre_event_accession": "0001133421-23-000006",
        "identifier_regime_at_action": "UEI_AUTHORITATIVE",
        "source_url": "https://www.fpds.gov/dbsight/FEEDS/ATOM?FEEDNAME=PUBLIC&q=PIID%3A%22FA865124FB001%22",
    },
)

EXPECTED_REQUEST_VALUES = {
    "RUN_Q221_ARQUIVO_PT_FPDS_TIMEMAP_PROBE": "true",
    "REASON": "DISTINCT_ARCHIVE_METADATA_LOOKUP_FOR_FOUR_FROZEN_FPDS_FEED_URLS",
    "BOUNDARY_PATH": BOUNDARY_PATH,
    "BOUNDARY_GIT_BLOB_SHA1": BOUNDARY_BLOB_SHA1,
    "BOUNDARY_RECEIPT_FINGERPRINT": BOUNDARY_FP,
    "PRE_EVENT_PATH": PRE_EVENT_PATH,
    "PRE_EVENT_RECEIPT_FINGERPRINT": PRE_EVENT_FP,
    "PREREG_PATH": PREREG_PATH,
    "TIME_MAP_BASE_URL": TIME_MAP_BASE_URL,
    "MAX_REQUESTS": str(MAX_REQUESTS),
    "MAX_RESPONSE_BYTES_EACH": str(MAX_RESPONSE_BYTES_EACH),
    "MAX_TOTAL_RESPONSE_BYTES": str(MAX_TOTAL_RESPONSE_BYTES),
    "REQUEST_TIMEOUT_SECONDS": str(TIMEOUT_SECONDS),
    "MIN_REQUEST_GAP_SECONDS": "1",
    "AUTOMATIC_RETRIES": "0",
    "FOLLOW_REDIRECTS": "false",
    "ARCHIVED_REPLAY_REQUESTS": "0",
    "DIRECT_FPDS_REQUESTS": "0",
    "SAM_API_REQUESTS": "0",
    "USASPENDING_REQUESTS": "0",
    "SEC_REQUESTS": "0",
    "COMMONCRAWL_INDEX_REQUESTS": "0",
    "WAYBACK_ARCHIVE_REQUESTS": "0",
    "TARGET_KEY_EXPANSION": "false",
    "ARCHIVE_PAYLOADS_DOWNLOADED": "false",
    "RESPONSE_BODIES_PERSISTED": "false",
    "RECIPIENT_IDENTITY_MAPPINGS_ADDED": "false",
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


class ProbeError(ValueError):
    """Frozen inputs or responses violate the registered contract."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def canonical_fingerprint(value: dict[str, Any], field: str = "receipt_fingerprint") -> str:
    payload = dict(value)
    payload.pop(field, None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(raw)


def analysis_fingerprint(value: dict[str, Any]) -> str:
    payload = dict(value)
    for field in ("analysis_fingerprint", "receipt_fingerprint", "generated_at_utc", "workflow_run_id", "cross_arch_validation"):
        payload.pop(field, None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(raw)


def read_key_value_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.strip() != line or "=" not in line:
            raise ProbeError(f"Q221_ARQUIVO_REQUEST_INVALID_LINE:{line_no}")
        key, value = line.split("=", 1)
        if not key or not value or key in values:
            raise ProbeError(f"Q221_ARQUIVO_REQUEST_INVALID_KEY_VALUE:{line_no}")
        values[key] = value
    if set(values) != set(EXPECTED_REQUEST_VALUES) | {"REQUEST_SEQUENCE"}:
        raise ProbeError("Q221_ARQUIVO_REQUEST_KEY_SET_MISMATCH")
    for key, expected in EXPECTED_REQUEST_VALUES.items():
        if values.get(key) != expected:
            raise ProbeError("Q221_ARQUIVO_REQUEST_VALUE_MISMATCH:" + key)
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values["REQUEST_SEQUENCE"]):
        raise ProbeError("Q221_ARQUIVO_REQUEST_SEQUENCE_INVALID")
    datetime.fromisoformat(values["REQUEST_SEQUENCE"].replace("Z", "+00:00"))
    return values


def read_object(path: Path, error_code: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProbeError(error_code) from exc
    if not isinstance(value, dict):
        raise ProbeError(error_code + "_NOT_OBJECT")
    return value, raw


def validate_preflight(repo_root: Path, request_path: Path, prereg_path: Path) -> dict[str, Any]:
    request = read_key_value_request(request_path)
    prereg, prereg_raw = read_object(prereg_path, "Q221_ARQUIVO_PREREG_INVALID")
    if prereg.get("record_type") != "q221_arquivo_pt_fpds_timemap_probe_preregistration" or prereg.get("candidate_id") != "Q221":
        raise ProbeError("Q221_ARQUIVO_PREREG_IDENTITY_MISMATCH")
    if prereg.get("preregistered_at_utc") != request.get("REQUEST_SEQUENCE"):
        raise ProbeError("Q221_ARQUIVO_PREREG_SEQUENCE_MISMATCH")
    if prereg.get("study_mode") != "BOUNDED_ARCHIVE_METADATA_FEASIBILITY":
        raise ProbeError("Q221_ARQUIVO_PREREG_MODE_MISMATCH")
    frozen = prereg.get("frozen_inputs", {})
    pins = (
        ("boundary_path", BOUNDARY_PATH),
        ("boundary_git_blob_sha1", BOUNDARY_BLOB_SHA1),
        ("boundary_receipt_fingerprint", BOUNDARY_FP),
        ("pre_event_feasibility_path", PRE_EVENT_PATH),
        ("pre_event_feasibility_receipt_fingerprint", PRE_EVENT_FP),
        ("prior_fpds_probe_run_id", 38712516839),
        ("prior_fpds_probe_receipt_fingerprint", PRIOR_FPDS_FP),
        ("prior_fpds_capture_receipt_fingerprint", PRIOR_FPDS_CAPTURE_FP),
    )
    for key, expected in pins:
        if frozen.get(key) != expected:
            raise ProbeError("Q221_ARQUIVO_PREREG_FROZEN_INPUT_MISMATCH:" + key)
    archive = prereg.get("official_archive", {})
    if archive.get("name") != "Arquivo.pt Memento TimeMap" or archive.get("time_map_template") != TIME_MAP_BASE_URL + "{fully-percent-encoded-exact-original-url}":
        raise ProbeError("Q221_ARQUIVO_ARCHIVE_CONTRACT_MISMATCH")
    limits = prereg.get("execution_limits", {})
    expected_limits = {
        "exact_archive_url_queries": MAX_REQUESTS,
        "requests_per_fixed_original_url": 1,
        "automatic_retries": 0,
        "follow_redirects": False,
        "request_timeout_seconds": TIMEOUT_SECONDS,
        "minimum_gap_between_requests_seconds": 1,
        "max_response_bytes_each": MAX_RESPONSE_BYTES_EACH,
        "max_total_response_bytes": MAX_TOTAL_RESPONSE_BYTES,
        "max_timemap_rows_per_url": MAX_ROWS_PER_URL,
        "archived_replay_requests": 0,
        "direct_fpds_requests": 0,
        "sam_api_requests": 0,
        "usaspending_requests": 0,
        "sec_requests": 0,
        "commoncrawl_index_requests": 0,
        "wayback_archive_requests": 0,
        "target_key_expansion": False,
        "archive_payloads_downloaded": False,
        "response_bodies_persisted": False,
        "recipient_identity_mappings_added": False,
        "frozen_transaction_rows_modified": False,
        "source_hashes_modified": False,
    }
    for key, expected in expected_limits.items():
        if limits.get(key) != expected:
            raise ProbeError("Q221_ARQUIVO_PREREG_LIMIT_MISMATCH:" + key)
    records = prereg.get("records")
    if not isinstance(records, list) or len(records) != MAX_REQUESTS:
        raise ProbeError("Q221_ARQUIVO_RECORD_COUNT_MISMATCH")
    for expected, actual in zip(EXPECTED_RECORDS, records):
        for key, value in expected.items():
            if actual.get(key) != value:
                raise ProbeError(f"Q221_ARQUIVO_RECORD_PIN_MISMATCH:{expected['record_id']}:{key}")
    if [row.get("record_id") for row in records] != [row["record_id"] for row in EXPECTED_RECORDS]:
        raise ProbeError("Q221_ARQUIVO_RECORD_ORDER_MISMATCH")

    boundary, boundary_raw = read_object(repo_root / BOUNDARY_PATH, "Q221_ARQUIVO_BOUNDARY_RECEIPT_INVALID")
    if git_blob_sha1(boundary_raw) != BOUNDARY_BLOB_SHA1:
        raise ProbeError("Q221_ARQUIVO_BOUNDARY_GIT_BLOB_SHA_MISMATCH")
    if canonical_fingerprint(boundary) != BOUNDARY_FP or boundary.get("receipt_fingerprint") != BOUNDARY_FP:
        raise ProbeError("Q221_ARQUIVO_BOUNDARY_RECEIPT_FINGERPRINT_MISMATCH")
    if boundary.get("candidate_id") != "Q221" or boundary.get("historical_first_public_observation_proven") is not False:
        raise ProbeError("Q221_ARQUIVO_BOUNDARY_GATE_STATE_CHANGED")
    boundary_rows = boundary.get("transactions", [])
    if not isinstance(boundary_rows, list) or len(boundary_rows) != 348:
        raise ProbeError("Q221_ARQUIVO_BOUNDARY_ROW_COUNT_MISMATCH")
    by_key = {str(row.get("transaction_key")): row for row in boundary_rows if isinstance(row, dict)}
    if len(by_key) != 348:
        raise ProbeError("Q221_ARQUIVO_BOUNDARY_KEYS_NOT_UNIQUE")
    for expected in EXPECTED_RECORDS:
        row = by_key.get(expected["transaction_key"])
        if not isinstance(row, dict):
            raise ProbeError("Q221_ARQUIVO_FROZEN_TRANSACTION_MISSING:" + expected["record_id"])
        for field in ("action_date", "recipient_uei", "recipient_id"):
            if str(row.get(field) or "") != expected[field]:
                raise ProbeError(f"Q221_ARQUIVO_BOUNDARY_ROW_PIN_MISMATCH:{expected['record_id']}:{field}")
        if row.get("recipient_to_issuer_status") != "UNMAPPED_NO_FROZEN_PRE_EVENT_IDENTITY_RECEIPT":
            raise ProbeError("Q221_ARQUIVO_UPSTREAM_MAPPING_STATUS_CHANGED:" + expected["record_id"])

    pre_event, _ = read_object(repo_root / PRE_EVENT_PATH, "Q221_ARQUIVO_PRE_EVENT_RECEIPT_INVALID")
    if (
        pre_event.get("record_type") != "q221_pre_event_parent_identity_feasibility"
        or pre_event.get("receipt_fingerprint") != PRE_EVENT_FP
        or canonical_fingerprint(pre_event) != PRE_EVENT_FP
        or pre_event.get("status") != "Q221_PRE_EVENT_PARENT_SOURCE_FEASIBILITY_COMPLETE_LINEAGE_UNRESOLVED"
        or pre_event.get("interpretation", {}).get("recipient_to_issuer_mapping_frozen") is not False
        or pre_event.get("interpretation", {}).get("q221_gate_positive") is not False
        or pre_event.get("analysis_fingerprint") != PRE_EVENT_ANALYSIS_FP
    ):
        raise ProbeError("Q221_ARQUIVO_PRE_EVENT_RECEIPT_STATE_MISMATCH")

    prior, prior_raw = read_object(repo_root / PRIOR_FPDS_PATH, "Q221_ARQUIVO_PRIOR_FPDS_RECEIPT_INVALID")
    if git_blob_sha1(prior_raw) != PRIOR_FPDS_BLOB_SHA1:
        raise ProbeError("Q221_ARQUIVO_PRIOR_FPDS_BLOB_SHA_MISMATCH")
    if prior.get("receipt_fingerprint") != PRIOR_FPDS_FP or canonical_fingerprint(prior) != PRIOR_FPDS_FP:
        raise ProbeError("Q221_ARQUIVO_PRIOR_FPDS_RECEIPT_FINGERPRINT_MISMATCH")
    if prior.get("cross_arch_validation", {}).get("capture_receipt_fingerprint") != PRIOR_FPDS_CAPTURE_FP:
        raise ProbeError("Q221_ARQUIVO_PRIOR_FPDS_CAPTURE_FINGERPRINT_MISMATCH")
    prior_rows = prior.get("observations")
    if not isinstance(prior_rows, list) or len(prior_rows) != MAX_REQUESTS:
        raise ProbeError("Q221_ARQUIVO_PRIOR_FPDS_ROW_COUNT_MISMATCH")
    for expected, actual in zip(EXPECTED_RECORDS, prior_rows):
        if actual.get("record_id") != expected["record_id"] or actual.get("requested_url") != expected["source_url"]:
            raise ProbeError("Q221_ARQUIVO_PRIOR_FPDS_RECORD_URL_MISMATCH")
        if actual.get("http_status") != 302 or actual.get("status") != "REDIRECT_BLOCKED":
            raise ProbeError("Q221_ARQUIVO_PRIOR_FPDS_RESULT_CHANGED")

    return {
        "request": request,
        "preregistration": prereg,
        "preregistration_git_blob_sha1": git_blob_sha1(prereg_raw),
        "boundary": boundary,
        "pre_event": pre_event,
        "prior_fpds": prior,
        "records": list(EXPECTED_RECORDS),
    }


def timemap_request_url(source_url: str) -> str:
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.hostname != "www.fpds.gov" or parsed.path != "/dbsight/FEEDS/ATOM":
        raise ProbeError("Q221_ARQUIVO_ORIGINAL_URL_OUTSIDE_FROZEN_FPDS_ROUTE")
    return TIME_MAP_BASE_URL + urllib.parse.quote(source_url, safe="")


def parse_timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ProbeError("Q221_ARQUIVO_TIMEMAP_TIMESTAMP_MISSING")
    if re.fullmatch(r"\d{14}", value):
        parsed = datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    else:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ProbeError("Q221_ARQUIVO_TIMEMAP_TIMESTAMP_INVALID") from exc
        if parsed.tzinfo is None:
            raise ProbeError("Q221_ARQUIVO_TIMEMAP_TIMESTAMP_MISSING_TIMEZONE")
        parsed = parsed.astimezone(timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def parse_timemap_jsonl(body: bytes, expected_url: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(body.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProbeError(f"Q221_ARQUIVO_TIMEMAP_INVALID_JSON:{line_no}") from exc
        if not isinstance(item, dict):
            raise ProbeError(f"Q221_ARQUIVO_TIMEMAP_ROW_NOT_OBJECT:{line_no}")
        timestamp = item.get("timestamp") or item.get("memento_datetime") or item.get("datetime")
        original = item.get("url") or item.get("original") or item.get("original_url")
        if not isinstance(original, str) or not original:
            raise ProbeError(f"Q221_ARQUIVO_TIMEMAP_ORIGINAL_URL_MISSING:{line_no}")
        if len(rows) >= MAX_ROWS_PER_URL:
            raise ProbeError("Q221_ARQUIVO_TIMEMAP_ROW_CAP_EXCEEDED")
        rows.append({
            "capture_timestamp_utc": parse_timestamp(timestamp),
            "indexed_original_url": original,
            "exact_original_url_match": original == expected_url,
            "source_http_status": str(item.get("status") or item.get("statuscode") or item.get("http_status") or ""),
            "mime": str(item.get("mime") or item.get("mimetype") or item.get("mime-detected") or "")[:160],
            "digest": str(item.get("digest") or "")[:160],
            "record_length": str(item.get("length") or "")[:40],
            "warc_filename_present": bool(item.get("filename") or item.get("warc_filename")),
            "warc_offset_present": item.get("offset") is not None or item.get("warc_record_offset") is not None,
        })
    return rows


class ResponseBudget:
    def __init__(self) -> None:
        self.used = 0
        self.last_start = 0.0

    def wait(self) -> None:
        delay = REQUEST_GAP_SECONDS - (time.monotonic() - self.last_start)
        if delay > 0:
            time.sleep(delay)
        self.last_start = time.monotonic()

    def add(self, size: int) -> None:
        if size < 0 or self.used + size > MAX_TOTAL_RESPONSE_BYTES:
            raise ProbeError("Q221_ARQUIVO_TOTAL_RESPONSE_BUDGET_EXCEEDED")
        self.used += size


def _read_limited(stream: Any, limit: int) -> bytes:
    """Read at most the remaining byte budget; never probe beyond the cap."""
    return stream.read(limit)


def fetch_timemap(source_url: str, budget: ResponseBudget) -> dict[str, Any]:
    request_url = timemap_request_url(source_url)
    parsed = urlparse(request_url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_ARCHIVE_HOST or not parsed.path.startswith("/wayback/timemap/json/"):
        raise ProbeError("Q221_ARQUIVO_TIMEMAP_URL_OUTSIDE_ALLOWLIST")
    observation: dict[str, Any] = {
        "source_url": source_url,
        "method": "GET",
        "requested_host": parsed.hostname,
        "http_status": None,
        "content_type": "",
        "response_bytes": 0,
        "response_sha256": None,
        "response_body_persisted": False,
        "query_completed": False,
        "capture_count": 0,
        "exact_original_url_capture_count": 0,
        "exact_original_url_http_200_capture_count": 0,
        "captures": [],
        "status": "NOT_ATTEMPTED",
    }
    request = urllib.request.Request(
        request_url,
        headers={
            "User-Agent": "DWR-debug/trading-agent-public Q221 Arquivo.pt TimeMap probe/1.0",
            "Accept": "application/json, application/x-ndjson;q=0.9",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
        method="GET",
    )
    budget.wait()
    limit = min(MAX_RESPONSE_BYTES_EACH, MAX_TOTAL_RESPONSE_BYTES - budget.used)
    if limit <= 0:
        observation.update({"status": "NOT_ATTEMPTED_TOTAL_BUDGET_EXHAUSTED", "error_code": "Q221_ARQUIVO_TOTAL_RESPONSE_BUDGET_EXHAUSTED"})
        return observation
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            status = int(getattr(response, "status", 200))
            content_type = str(response.headers.get("Content-Type", ""))
            declared_length = str(response.headers.get("Content-Length", ""))
            try:
                declared_bytes = int(declared_length) if declared_length else None
            except ValueError:
                declared_bytes = None
            if declared_bytes is not None and declared_bytes > limit:
                observation.update({
                    "http_status": status,
                    "content_type": content_type,
                    "response_expected_bytes": declared_bytes,
                    "status": "RESPONSE_OVER_LIMIT",
                    "query_completed": False,
                })
                return observation
            body = _read_limited(response, limit)
    except urllib.error.HTTPError as exc:
        # No redirect target is followed, and error bodies are not fetched/persisted.
        observation.update({
            "http_status": int(exc.code),
            "content_type": str(exc.headers.get("Content-Type", "")),
            "status": "REDIRECT_BLOCKED" if exc.code in {301, 302, 303, 307, 308} else f"HTTP_{exc.code}",
            "redirect_location_host": urlparse(str(exc.headers.get("Location") or "")).hostname,
        })
        return observation
    except ProbeError as exc:
        observation.update({"status": "RESPONSE_OVER_LIMIT", "error_code": str(exc)[:180]})
        return observation
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        observation.update({"status": "NETWORK_ERROR", "error_type": type(exc).__name__})
        return observation

    try:
        budget.add(len(body))
    except ProbeError as exc:
        observation.update({"status": "TOTAL_RESPONSE_BUDGET_EXCEEDED", "error_code": str(exc)})
        return observation
    observation.update({
        "http_status": status,
        "content_type": content_type,
        "response_bytes": len(body),
        "response_sha256": sha256(body),
    })
    if status != 200:
        observation["status"] = f"HTTP_{status}"
        return observation
    if len(body) == limit:
        # At the exact limit the archive may have more bytes, so do not parse
        # a potentially truncated TimeMap as complete metadata.
        observation.update({"status": "RESPONSE_LIMIT_REACHED_OR_TRUNCATED", "query_completed": False})
        return observation
    if "json" not in content_type.lower() and "ndjson" not in content_type.lower():
        observation.update({"status": "UNEXPECTED_CONTENT_TYPE", "query_completed": False})
        return observation
    try:
        captures = parse_timemap_jsonl(body, source_url)
    except ProbeError as exc:
        observation.update({"status": "TIMEMAP_SCHEMA_INVALID", "error_code": str(exc)[:180]})
        return observation
    exact = [row for row in captures if row["exact_original_url_match"]]
    exact_200 = [row for row in exact if row["source_http_status"] == "200"]
    observation.update({
        "status": "TIMEMAP_OK_WITH_CAPTURES" if captures else "TIMEMAP_OK_ZERO_ROWS",
        "query_completed": True,
        "capture_count": len(captures),
        "exact_original_url_capture_count": len(exact),
        "exact_original_url_http_200_capture_count": len(exact_200),
        "captures": captures,
    })
    return observation


def add_fingerprints(receipt: dict[str, Any]) -> dict[str, Any]:
    receipt.pop("analysis_fingerprint", None)
    receipt.pop("receipt_fingerprint", None)
    receipt["analysis_fingerprint"] = analysis_fingerprint(receipt)
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    return receipt


def fallback_receipt(run_id: int | None, reason: str, *, source_requests_known_zero: bool) -> dict[str, Any]:
    attempted = 0 if source_requests_known_zero else None
    receipt = {
        "schema_version": 1,
        "record_type": "q221_arquivo_pt_fpds_timemap_probe",
        "candidate_id": "Q221",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_run_id": run_id,
        "preregistration_path": PREREG_PATH,
        "request_path": REQUEST_PATH,
        "source_contract": {
            "archive": "Arquivo.pt Memento TimeMap",
            "archive_metadata_requests_attempted": attempted,
            "archive_request_count_known": source_requests_known_zero,
            "automatic_retries": 0,
            "redirects_followed": False,
            "archived_replay_requests": 0,
            "direct_fpds_requests": 0,
            "sam_api_requests": 0,
            "usaspending_requests": 0,
            "sec_requests": 0,
            "commoncrawl_index_requests": 0,
            "wayback_archive_requests": 0,
            "archive_payloads_downloaded": 0,
            "response_bodies_persisted": False,
        },
        "observations": [],
        "aggregate": {
            "metadata_lookup_complete": False,
            "timemap_queries_completed": 0,
            "capture_metadata_row_count": 0,
            "exact_original_url_capture_metadata_count": 0,
            "exact_original_url_http_200_capture_metadata_count": 0,
            "historical_first_public_observation_proven": False,
            "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "q221_gate_positive": False,
        },
        "status": "Q221_ARQUIVO_PT_PREFLIGHT_REJECTED" if source_requests_known_zero else "Q221_ARQUIVO_PT_CAPTURE_OUTCOME_UNKNOWN",
        "errors": [{"code": reason[:180]}],
        "interpretation": {
            "metadata_only": True,
            "capture_timestamps_are_archive_observations_not_first_public_timestamps": True,
            "empty_or_failed_lookup_is_not_proof_of_historical_absence": True,
            "historical_first_public_observation_proven": False,
            "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "scientific_evidence": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
    }
    return add_fingerprints(receipt)


def capture(repo_root: Path, request_path: Path, prereg_path: Path, run_id: int | None) -> dict[str, Any]:
    try:
        frozen = validate_preflight(repo_root, request_path, prereg_path)
    except (ProbeError, OSError, ValueError) as exc:
        return fallback_receipt(run_id, str(exc), source_requests_known_zero=True)
    budget = ResponseBudget()
    observations = []
    for record in frozen["records"]:
        if budget.used >= MAX_TOTAL_RESPONSE_BYTES:
            break
        try:
            row = fetch_timemap(record["source_url"], budget)
            row["record_id"] = record["record_id"]
            row["transaction_key"] = record["transaction_key"]
            observations.append(row)
        except Exception as exc:
            observations.append({
                "record_id": record["record_id"],
                "transaction_key": record["transaction_key"],
                "source_url": record["source_url"],
                "method": "GET",
                "http_status": None,
                "response_bytes": 0,
                "response_sha256": None,
                "response_body_persisted": False,
                "query_completed": False,
                "capture_count": 0,
                "exact_original_url_capture_count": 0,
                "exact_original_url_http_200_capture_count": 0,
                "captures": [],
                "status": "INTERNAL_PROBE_ERROR",
                "error_type": type(exc).__name__,
            })
    completed = len(observations) == MAX_REQUESTS and all(row.get("query_completed") is True for row in observations)
    capture_count = sum(int(row.get("capture_count", 0)) for row in observations)
    exact_count = sum(int(row.get("exact_original_url_capture_count", 0)) for row in observations)
    exact_200_count = sum(int(row.get("exact_original_url_http_200_capture_count", 0)) for row in observations)
    receipt = {
        "schema_version": 1,
        "record_type": "q221_arquivo_pt_fpds_timemap_probe",
        "candidate_id": "Q221",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_run_id": run_id,
        "preregistration_path": PREREG_PATH,
        "preregistration_git_blob_sha1": frozen["preregistration_git_blob_sha1"],
        "request_path": REQUEST_PATH,
        "frozen_inputs": {
            "boundary_path": BOUNDARY_PATH,
            "boundary_git_blob_sha1": BOUNDARY_BLOB_SHA1,
            "boundary_receipt_fingerprint": BOUNDARY_FP,
            "pre_event_receipt_fingerprint": PRE_EVENT_FP,
            "prior_fpds_blob_sha1": PRIOR_FPDS_BLOB_SHA1,
            "prior_fpds_receipt_fingerprint": PRIOR_FPDS_FP,
            "prior_fpds_capture_receipt_fingerprint": PRIOR_FPDS_CAPTURE_FP,
            "record_count": len(frozen["records"]),
        },
        "source_contract": {
            "archive": "Arquivo.pt Memento TimeMap",
            "time_map_base_url": TIME_MAP_BASE_URL,
            "archive_metadata_requests_attempted": len(observations),
            "archive_request_count_known": True,
            "response_bytes_total": budget.used,
            "max_response_bytes_each": MAX_RESPONSE_BYTES_EACH,
            "max_total_response_bytes": MAX_TOTAL_RESPONSE_BYTES,
            "automatic_retries": 0,
            "redirects_followed": False,
            "archived_replay_requests": 0,
            "direct_fpds_requests": 0,
            "sam_api_requests": 0,
            "usaspending_requests": 0,
            "sec_requests": 0,
            "commoncrawl_index_requests": 0,
            "wayback_archive_requests": 0,
            "archive_payloads_downloaded": 0,
            "response_bodies_persisted": False,
        },
        "observations": observations,
        "aggregate": {
            "metadata_lookup_complete": completed,
            "timemap_queries_completed": sum(1 for row in observations if row.get("query_completed") is True),
            "capture_metadata_row_count": capture_count,
            "exact_original_url_capture_metadata_count": exact_count,
            "exact_original_url_http_200_capture_metadata_count": exact_200_count,
            "historical_first_public_observation_proven": False,
            "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "q221_gate_positive": False,
        },
        "status": "Q221_ARQUIVO_PT_TIMEMAP_METADATA_COMPLETE" if completed else "Q221_ARQUIVO_PT_TIMEMAP_METADATA_INCOMPLETE",
        "next_gate": "If exact-original-URL capture metadata exists, preregister a separate bounded archived replay that inspects exact transaction tuples; never infer first-public time or gate clearance from metadata alone.",
        "interpretation": {
            "metadata_only": True,
            "capture_timestamps_are_archive_observations_not_first_public_timestamps": True,
            "empty_or_failed_lookup_is_not_proof_of_historical_absence": True,
            "historical_first_public_observation_proven": False,
            "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "scientific_evidence": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
    }
    return add_fingerprints(receipt)


def verify_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    errors = []
    if not isinstance(receipt, dict) or receipt.get("record_type") != "q221_arquivo_pt_fpds_timemap_probe":
        errors.append("Q221_ARQUIVO_CAPTURE_RECEIPT_IDENTITY_MISMATCH")
    if not errors:
        if receipt.get("receipt_fingerprint") != canonical_fingerprint(receipt):
            errors.append("Q221_ARQUIVO_CAPTURE_RECEIPT_FINGERPRINT_MISMATCH")
        if receipt.get("analysis_fingerprint") != analysis_fingerprint(receipt):
            errors.append("Q221_ARQUIVO_CAPTURE_ANALYSIS_FINGERPRINT_MISMATCH")
        contract = receipt.get("source_contract", {})
        if contract.get("automatic_retries") != 0 or contract.get("redirects_followed") is not False:
            errors.append("Q221_ARQUIVO_CAPTURE_RETRY_OR_REDIRECT_POLICY_MISMATCH")
        if contract.get("archived_replay_requests") != 0 or contract.get("archive_payloads_downloaded") != 0:
            errors.append("Q221_ARQUIVO_CAPTURE_ARCHIVE_PAYLOAD_POLICY_MISMATCH")
        if any(contract.get(key) != 0 for key in ("direct_fpds_requests", "sam_api_requests", "usaspending_requests", "sec_requests", "commoncrawl_index_requests", "wayback_archive_requests")):
            errors.append("Q221_ARQUIVO_CAPTURE_ORIGIN_REQUEST_POLICY_MISMATCH")
        if contract.get("archive_metadata_requests_attempted") is not None and contract.get("archive_metadata_requests_attempted") > MAX_REQUESTS:
            errors.append("Q221_ARQUIVO_CAPTURE_REQUEST_LIMIT_EXCEEDED")
        observations = receipt.get("observations", [])
        if not isinstance(observations, list) or len(observations) > MAX_REQUESTS:
            errors.append("Q221_ARQUIVO_CAPTURE_OBSERVATION_COUNT_INVALID")
            observations = []
        if contract.get("archive_request_count_known") is True and contract.get("archive_metadata_requests_attempted") != len(observations):
            errors.append("Q221_ARQUIVO_CAPTURE_REQUEST_COUNT_MISMATCH")
        frozen_urls = {row["source_url"] for row in EXPECTED_RECORDS}
        observed_urls = []
        for row in observations:
            if not isinstance(row, dict) or row.get("source_url") not in frozen_urls:
                errors.append("Q221_ARQUIVO_CAPTURE_SOURCE_URL_OUTSIDE_FROZEN_SET")
                continue
            observed_urls.append(row["source_url"])
            if row.get("method") != "GET" or row.get("response_body_persisted") is not False:
                errors.append("Q221_ARQUIVO_CAPTURE_METHOD_OR_BODY_PERSISTENCE_INVALID")
        if len(observed_urls) != len(set(observed_urls)):
            errors.append("Q221_ARQUIVO_CAPTURE_DUPLICATE_URL_QUERY")
        if contract.get("response_bodies_persisted") is not False:
            errors.append("Q221_ARQUIVO_CAPTURE_BODY_PERSISTENCE_INVALID")
        safety = receipt.get("safety", {})
        if safety.get("paper_only") is not True:
            errors.append("Q221_ARQUIVO_CAPTURE_PAPER_ONLY_INVALID")
        for key in ("live_trading_enabled", "orders_enabled", "automatic_promotion", "performance_authorization", "holdout_selection", "ranking", "tuning", "promotion", "live_execution"):
            if safety.get(key) is not False:
                errors.append("Q221_ARQUIVO_CAPTURE_SAFETY_FLAG_INVALID:" + key)
        for key in ("historical_first_public_observation_proven", "event_level_public_boundary_proven", "recipient_to_issuer_mapping_frozen", "q221_gate_positive"):
            if receipt.get("aggregate", {}).get(key) is not False:
                errors.append("Q221_ARQUIVO_CAPTURE_GATE_STATE_INVALID:" + key)
    result = {
        "schema_version": 1,
        "record_type": "q221_arquivo_pt_fpds_timemap_offline_validation",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "validation_status": "VALIDATED" if not errors else "FAILED_CLOSED",
        "capture_receipt_fingerprint": receipt.get("receipt_fingerprint") if isinstance(receipt, dict) else None,
        "analysis_fingerprint": receipt.get("analysis_fingerprint") if isinstance(receipt, dict) else None,
        "network_requests_made": 0,
        "source_gate_positive": False,
        "historical_first_public_observation_proven": False,
        "event_level_public_boundary_proven": False,
        "recipient_to_issuer_mapping_frozen": False,
        "scientific_evidence": False,
        "errors": errors,
    }
    result["receipt_fingerprint"] = canonical_fingerprint(result)
    return result


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("validate-only", "capture", "verify", "fallback"), required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--request", type=Path, default=ROOT / REQUEST_PATH)
    parser.add_argument("--prereg", type=Path, default=ROOT / PREREG_PATH)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run-id", type=int, default=None)
    parser.add_argument("--reason", default="CAPTURE_RECEIPT_MISSING")
    parser.add_argument("--source-requests-known-zero", action="store_true")
    args = parser.parse_args()
    if args.mode == "validate-only":
        validate_preflight(args.repo_root, args.request, args.prereg)
        print("Q221_ARQUIVO_PREFLIGHT=VALID; SOURCE_REQUESTS=0")
        return 0
    if args.mode == "capture":
        if args.output is None:
            raise SystemExit("--output is required in capture mode")
        receipt = capture(args.repo_root, args.request, args.prereg, args.run_id)
        write_json(args.output, receipt)
        print(json.dumps({
            "status": receipt.get("status"),
            "analysis_fingerprint": receipt.get("analysis_fingerprint"),
            "archive_metadata_requests_attempted": receipt.get("source_contract", {}).get("archive_metadata_requests_attempted"),
            "metadata_lookup_complete": receipt.get("aggregate", {}).get("metadata_lookup_complete", False),
        }, sort_keys=True))
        return 0 if receipt.get("status") == "Q221_ARQUIVO_PT_TIMEMAP_METADATA_COMPLETE" else 2
    if args.mode == "verify":
        if args.input is None or args.output is None:
            raise SystemExit("--input and --output are required in verify mode")
        try:
            receipt = json.loads(args.input.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            receipt = {}
        validation = verify_receipt(receipt)
        write_json(args.output, validation)
        print(json.dumps(validation, sort_keys=True))
        return 0 if validation["validation_status"] == "VALIDATED" else 2
    if args.mode == "fallback":
        if args.output is None:
            raise SystemExit("--output is required in fallback mode")
        receipt = fallback_receipt(
            args.run_id,
            args.reason,
            source_requests_known_zero=bool(args.source_requests_known_zero),
        )
        write_json(args.output, receipt)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
