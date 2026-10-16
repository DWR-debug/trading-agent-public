"""One-shot metadata-only CDX MIME-type diagnostic for Q221 DoD 097.

Performs at most one bounded GET to web.archive.org's CDX endpoint. Never requests
the archived ZIP and never inspects contract transaction rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from automation import q221_dod_097_wayback_archive_presence as source_probe

PREREG_PATH = "research/preregistrations/q221_dod_097_cdx_mimetype_diagnostic_r4_2026_10_15.json"
REQUEST_PATH = "research/run_requests/q221_dod_097_cdx_mimetype_diagnostic_r4.trigger"
R3_PREREG_PATH = source_probe.PREREG_PATH_R3
R3_REQUEST_PATH = source_probe.REQUEST_PATH_R3
CDX_ENDPOINT = "https://web.archive.org/cdx/search/cdx"
ARCHIVE_URL = source_probe.ARCHIVE_URL
ARCHIVE_FILENAME = source_probe.ARCHIVE_FILENAME
CAPTURE_TIMESTAMP = source_probe.CAPTURE_TIMESTAMP
CDX_SHA1_BASE32 = source_probe.CDX_SHA1_BASE32
CDX_LENGTH = source_probe.CDX_LENGTH
MANIFEST_PATH = source_probe.MANIFEST_PATH
MANIFEST_BLOB = source_probe.MANIFEST_BLOB
MANIFEST_FP = source_probe.MANIFEST_FP
MAX_CDX_BYTES = 5_000_000
REQUEST_TIMEOUT_SECONDS = 60
MAX_REQUESTS = 1
REQUEST_SEQUENCE = "2026-10-15T20:08:53Z"
PRIOR_R3 = {
    "workflow_run_id": 38798769065,
    "receipt_git_blob_sha1": "91e45f71a2b31721375f8fa0812ebac038fc8d1f",
    "receipt_fingerprint": "895a6d4e343cb535866df81ce06d6d824e1d05b1c7af114aa3befeb5c5473a5b",
    "status": "Q221_DOD_097_ARCHIVE_REPLAY_LENGTH_MISMATCH",
    "archive_replay_bytes": 13697800,
    "pinned_cdx_length_bytes": CDX_LENGTH,
    "archive_replay_sha256": "e9e952812886ffddd5d50ef6b712e58c804d5e01034a491f1f43432ef565c1bc",
    "cdx_response_sha256": "ba2a8c37c9b7751964fd8f6304d7fa666d8b445c380b262c8da9afa8323f1ba6",
}
FROZEN_REQUEST = {
    "RUN_Q221_DOD_097_CDX_MIMETYPE_DIAGNOSTIC_R4": "true",
    "REASON": "ONE_SHOT_METADATA_ONLY_CDX_MIMETYPE_DIAGNOSTIC_AFTER_R3_REPLAY_LENGTH_MISMATCH",
    "SOURCE_MANIFEST_PATH": MANIFEST_PATH,
    "SOURCE_MANIFEST_GIT_BLOB_SHA": MANIFEST_BLOB,
    "SOURCE_MANIFEST_RECEIPT_FINGERPRINT": MANIFEST_FP,
    "TARGET_ARCHIVE_FILENAME": ARCHIVE_FILENAME,
    "TARGET_ARCHIVE_CAPTURE": CAPTURE_TIMESTAMP,
    "TARGET_ARCHIVE_CDX_SHA1_BASE32": CDX_SHA1_BASE32,
    "TARGET_ARCHIVE_BYTES": str(CDX_LENGTH),
    "CDX_FIELDS": "timestamp,original,mimetype,statuscode,digest,length",
    "MAX_REQUESTS": "1",
    "MAX_CDX_RESPONSE_BYTES": str(MAX_CDX_BYTES),
    "PER_REQUEST_TIMEOUT_SECONDS": str(REQUEST_TIMEOUT_SECONDS),
    "ARCHIVE_REPLAY_REQUESTS_ALLOWED": "false",
    "ARCHIVE_PAYLOAD_ALLOWED": "false",
    "ARCHIVE_BYTES_PERSISTED_OR_UPLOADED": "false",
    "AUTOMATIC_RETRIES": "false",
    "ALTERNATE_SOURCES_ALLOWED": "false",
    "SOURCE_POPULATION_CHANGED": "false",
    "CENSUS_RESTART": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
    "REQUEST_SEQUENCE": REQUEST_SEQUENCE,
}


class DiagnosticError(ValueError):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status, self.message = status, message


def fingerprint(receipt: dict) -> str:
    body = {key: value for key, value in receipt.items() if key != "receipt_fingerprint"}
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_FROZEN_INPUT_READ_FAILED", type(exc).__name__) from exc
    if not isinstance(value, dict):
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_FROZEN_INPUT_SHAPE_INVALID", str(path))
    return value


def validate_inputs(root: Path, prereg_path: Path | None = None, request_path: Path | None = None) -> dict:
    root = root.resolve()
    prereg_file = Path(prereg_path) if prereg_path is not None else root / PREREG_PATH
    marker_file = Path(request_path) if request_path is not None else root / REQUEST_PATH
    for path, expected, code in (
        (prereg_file, PREREG_PATH, "Q221_DOD_097_CDX_DIAGNOSTIC_PREREG_PATH_INVALID"),
        (marker_file, REQUEST_PATH, "Q221_DOD_097_CDX_DIAGNOSTIC_MARKER_PATH_INVALID"),
    ):
        try:
            relative = path.resolve().relative_to(root).as_posix()
        except ValueError as exc:
            raise DiagnosticError(code, "path is outside repository root") from exc
        if relative != expected:
            raise DiagnosticError(code, str(path))
    prereg = read_json(prereg_file)
    if prereg.get("schema_version") != 1 or prereg.get("record_type") != "q221_dod_097_cdx_mimetype_diagnostic_preregistration":
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_PREREG_TYPE_INVALID", "type/version differs")
    if prereg.get("attempt_number") != 4 or prereg.get("request_sequence") != REQUEST_SEQUENCE:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_PREREG_SEQUENCE_INVALID", "attempt or sequence differs")
    expected_manifest = {
        "path": MANIFEST_PATH,
        "git_blob_sha1": MANIFEST_BLOB,
        "receipt_fingerprint": MANIFEST_FP,
        "expected_transaction_count": source_probe.MANIFEST_COUNT,
        "frozen_target_count": source_probe.TARGET_COUNT,
    }
    if prereg.get("source_manifest") != expected_manifest:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_MANIFEST_PIN_MISMATCH", "manifest differs")
    expected_archive = {
        "filename": ARCHIVE_FILENAME,
        "original_url": ARCHIVE_URL,
        "wayback_capture_timestamp": CAPTURE_TIMESTAMP,
        "capture_timestamp_utc": source_probe.CAPTURE_UTC,
        "cdx_sha1_base32": CDX_SHA1_BASE32,
        "cdx_length_bytes": CDX_LENGTH,
    }
    if prereg.get("target_archive") != expected_archive:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_ARCHIVE_PIN_MISMATCH", "archive differs")
    if prereg.get("prior_attempt") != {
        "workflow_run_id": PRIOR_R3["workflow_run_id"],
        "receipt_git_blob_sha1": PRIOR_R3["receipt_git_blob_sha1"],
        "receipt_fingerprint": PRIOR_R3["receipt_fingerprint"],
        "status": PRIOR_R3["status"],
        "cdx_status": 200,
        "cdx_response_bytes": 3330,
        "cdx_response_sha256": PRIOR_R3["cdx_response_sha256"],
        "archive_replay_status": 200,
        "archive_replay_content_type": "application/zip",
        "archive_replay_bytes": PRIOR_R3["archive_replay_bytes"],
        "archive_replay_sha256": PRIOR_R3["archive_replay_sha256"],
        "expected_cdx_length_bytes": CDX_LENGTH,
        "outcome": "CDX target capture verified; raw replay rejected on length mismatch before ZIP/CSV inspection. No row result.",
    }:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_PRIOR_RECEIPT_MISMATCH", "R3 receipt lineage differs")
    expected_contract = {
        "question": "What MIME type does CDX assign to the exact pinned target capture, and what basic HTTP response metadata accompanies the bounded CDX response?",
        "endpoint": CDX_ENDPOINT,
        "same_prefix_and_filters_as_r3": True,
        "cdx_fields": ["timestamp", "original", "mimetype", "statuscode", "digest", "length"],
        "expected_exact_capture_timestamp": CAPTURE_TIMESTAMP,
        "max_source_requests": MAX_REQUESTS,
        "max_cdx_response_bytes": MAX_CDX_BYTES,
        "per_request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "redirect_policy": "reject",
        "archive_replay_request_count": 0,
        "archive_payload_download_allowed": False,
        "archive_bytes_persisted_or_uploaded": False,
        "no_retries": True,
        "no_alternate_sources": True,
    }
    if prereg.get("diagnostic_contract") != expected_contract:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_CONTRACT_MISMATCH", "contract differs")
    expected_recovery = {
        "prior_workflow_run_id": PRIOR_R3["workflow_run_id"],
        "prior_receipt_git_blob_sha1": PRIOR_R3["receipt_git_blob_sha1"],
        "prior_status": PRIOR_R3["status"],
        "prior_cdx_target_capture_verified": True,
        "prior_replay_bytes": PRIOR_R3["archive_replay_bytes"],
        "prior_pinned_length_bytes": CDX_LENGTH,
        "prior_length_difference_bytes": PRIOR_R3["archive_replay_bytes"] - CDX_LENGTH,
        "prior_row_presence_result_available": False,
        "prior_receipt_request_count": 2,
        "original_r1_r2_r3_markers_reused": False,
        "reason": "R3 verified the exact CDX index row but rejected the replay body on length before ZIP/CSV inspection. R4 is a separate single-request metadata diagnostic that adds the omitted CDX MIME field; it does not retry the archive replay.",
    }
    if prereg.get("recovery") != expected_recovery:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_RECOVERY_LINEAGE_INVALID", "recovery differs")
    safety = prereg.get("safety", {})
    if safety.get("paper_only") is not True:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_PAPER_ONLY_MISSING", "PAPER_ONLY not true")
    for key in (
        "live_trading_enabled", "orders_enabled", "scientific_evidence", "performance_authorization",
        "holdout_selection", "ranking", "tuning", "promotion", "live_execution", "archive_replay_allowed",
        "archive_payload_persisted", "archive_schema_examined", "transaction_row_presence_examined",
        "source_population_changed", "census_restarted", "alternate_source_used", "automatic_retry",
    ):
        if safety.get(key) is not False:
            raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_SAFETY_GATE_OPEN", key)
    try:
        marker_lines = marker_file.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_MARKER_MISSING", type(exc).__name__) from exc
    marker = {}
    for number, line in enumerate(marker_lines, 1):
        if not line or line.strip() != line or "=" not in line:
            raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_MARKER_INVALID", f"line {number}")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key) or not value or key in marker:
            raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_MARKER_INVALID", f"key/value at line {number}")
        marker[key] = value
    if marker != FROZEN_REQUEST:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_MARKER_MISMATCH", "marker differs from frozen request")
    datetime.strptime(marker["REQUEST_SEQUENCE"], "%Y-%m-%dT%H:%M:%SZ")
    frozen = source_probe.validate_frozen_inputs(root, root / R3_PREREG_PATH, root / R3_REQUEST_PATH)
    if len(frozen["targets"]) != source_probe.TARGET_COUNT or frozen["manifest_blob_sha1"] != MANIFEST_BLOB:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_TARGET_COUNT_MISMATCH", "R3 frozen manifest differs")
    return {
        "preregistration": prereg,
        "request": marker,
        "manifest_blob_sha1": frozen["manifest_blob_sha1"],
        "target_count": len(frozen["targets"]),
        "archive": expected_archive,
        "preregistration_path": PREREG_PATH,
        "request_marker_path": REQUEST_PATH,
    }


def build_cdx_url() -> str:
    params = [
        ("url", "files.usaspending.gov/award_data_archive/"),
        ("matchType", "prefix"), ("output", "json"),
        ("filter", "statuscode:200"), ("filter", "original:.*097.*Contracts.*zip"),
        ("fl", "timestamp,original,mimetype,statuscode,digest,length"),
        ("from", "2019"), ("to", "2026"), ("limit", "100"), ("gzip", "false"),
    ]
    return CDX_ENDPOINT + "?" + urllib.parse.urlencode(params)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_cdx_bounded(url: str, state: dict) -> tuple[int, bytes, dict[str, str]]:
    if state.get("request_count", 0) >= MAX_REQUESTS:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_REQUEST_CAP_EXCEEDED", "one GET is the hard cap")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "web.archive.org" or parsed.path != "/cdx/search/cdx" or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_HOST_FORBIDDEN", url)
    if url != build_cdx_url():
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_QUERY_PIN_MISMATCH", url)
    state["request_count"] += 1
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DWR-debug/trading-agent-public/Q221-DOD-097-CDX-MIME-Diagnostic/1.0",
            "Accept": "application/json",
            "Accept-Encoding": "identity",
        },
    )
    opener = urllib.request.build_opener(_NoRedirect())
    status, headers, body = 0, {}, b""
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status = int(getattr(response, "status", 200))
            headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
            body = response.read(MAX_CDX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        headers = {str(k).lower(): str(v) for k, v in (exc.headers or {}).items()}
        body = exc.read(MAX_CDX_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        state["transport_errors"].append(type(exc).__name__)
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_TRANSPORT_ERROR", type(exc).__name__) from exc
    state["response_bytes"] += len(body)
    state["responses"].append({
        "url": url,
        "http_status": status,
        "content_type": headers.get("content-type", ""),
        "content_length_header": headers.get("content-length", ""),
        "content_encoding": headers.get("content-encoding", ""),
        "transfer_encoding": headers.get("transfer-encoding", ""),
        "response_bytes": len(body),
        "response_sha256": hashlib.sha256(body).hexdigest(),
    })
    if len(body) > MAX_CDX_BYTES:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_RESPONSE_CAP_EXCEEDED", str(len(body)))
    if 300 <= status < 400:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_REDIRECT_BLOCKED", str(status))
    if status != 200:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_HTTP_NOT_200", str(status))
    return status, body, headers


def parse_rows(body: bytes) -> list[dict[str, str]]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_NOT_JSON", type(exc).__name__) from exc
    if not isinstance(payload, list) or not payload or not all(isinstance(row, list) for row in payload):
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_SHAPE_INVALID", "expected CDX header and rows")
    fields = ("timestamp", "original", "mimetype", "statuscode", "digest", "length")
    header = payload[0]
    if not isinstance(header, list) or not set(fields).issubset(header):
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_HEADER_INVALID", "expected MIME type and frozen CDX fields")
    indices = {field: header.index(field) for field in fields}
    rows = []
    for index, raw in enumerate(payload[1:], 1):
        if len(raw) != len(header):
            raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_ROW_WIDTH_INVALID", str(index))
        row = {field: str(raw[indices[field]]) for field in fields}
        if (
            not re.fullmatch(r"\d{14}", row["timestamp"])
            or not row["original"].startswith("https://files.usaspending.gov/award_data_archive/")
            or row["statuscode"] != "200"
            or not row["mimetype"] or not row["digest"] or not row["length"].isdigit()
        ):
            raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_ROW_INVALID", str(index))
        rows.append(row)
    if len(rows) >= 100:
        raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_RESULT_CAP_REACHED", "possibly truncated")
    return rows


def _base_receipt() -> dict:
    return {
        "schema_version": 1,
        "record_type": "q221_dod_097_cdx_mimetype_diagnostic",
        "candidate_id": "Q221",
        "generated_at_utc": datetime.now().astimezone().isoformat(),
        "source_of_truth": "DWR-debug/trading-agent-public",
        "status": "Q221_DOD_097_CDX_DIAGNOSTIC_NOT_RUN",
        "request": {
            "request_sequence": REQUEST_SEQUENCE,
            "preregistration_path": PREREG_PATH,
            "request_marker_path": REQUEST_PATH,
            "endpoint": CDX_ENDPOINT,
            "fields": ["timestamp", "original", "mimetype", "statuscode", "digest", "length"],
            "request_cap": MAX_REQUESTS,
            "timeout_seconds": REQUEST_TIMEOUT_SECONDS,
            "archive_replay_requests_allowed": False,
            "archive_payload_download_allowed": False,
        },
        "frozen_source_manifest": {
            "path": MANIFEST_PATH,
            "git_blob_sha1": MANIFEST_BLOB,
            "receipt_fingerprint": MANIFEST_FP,
            "expected_transaction_count": source_probe.MANIFEST_COUNT,
        },
        "target_archive": {
            "filename": ARCHIVE_FILENAME,
            "original_url": ARCHIVE_URL,
            "wayback_capture_timestamp": CAPTURE_TIMESTAMP,
            "capture_timestamp_utc": source_probe.CAPTURE_UTC,
            "cdx_sha1_base32": CDX_SHA1_BASE32,
            "cdx_length_bytes": CDX_LENGTH,
        },
        "prior_r3_evidence": PRIOR_R3,
        "target_count_from_frozen_manifest": source_probe.TARGET_COUNT,
        "cdx_inventory": None,
        "source_probe": {
            "request_profile": "R4_CDX_METADATA_ONLY",
            "request_count": 0,
            "response_bytes": 0,
            "responses": [],
            "transport_errors": [],
            "archive_replay_request_count": 0,
            "archive_payload_downloaded": False,
        },
        "interpretation": {
            "diagnostic_only": True,
            "mimetype_interprets_cdx_metadata_only": True,
            "archive_schema_examined": False,
            "transaction_row_presence_examined": False,
            "first_public_observation_time_proven": False,
            "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "positive_or_negative_historical_row_result_available": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "scientific_evidence": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
            "archive_replay_allowed": False,
            "archive_payload_persisted": False,
            "archive_schema_examined": False,
            "transaction_row_presence_examined": False,
            "source_population_changed": False,
            "census_restarted": False,
            "alternate_source_used": False,
            "automatic_retry": False,
            "source_requests_made": 0,
        },
        "errors": [],
        "next_gate": "No transaction-row or historical public-clock gate is changed by this metadata diagnostic.",
    }


def run_diagnostic(root: Path, prereg_path: Path | None = None, request_path: Path | None = None,
                   output_path: Path | None = None, fetcher=None) -> dict:
    output = output_path or (root / "q221-dod-097-cdx-mimetype-diagnostic-r4.json")
    receipt = _base_receipt()
    state = {"request_count": 0, "response_bytes": 0, "responses": [], "transport_errors": []}
    fetch = fetcher or fetch_cdx_bounded
    try:
        inputs = validate_inputs(root, prereg_path, request_path)
        receipt["request"]["request_sequence"] = inputs["request"]["REQUEST_SEQUENCE"]
        receipt["frozen_source_manifest"]["git_blob_sha1_verified"] = inputs["manifest_blob_sha1"]
        status, body, headers = fetch(build_cdx_url(), state)
        rows = parse_rows(body)
        matches = [row for row in rows if row["original"] == ARCHIVE_URL and row["timestamp"] == CAPTURE_TIMESTAMP]
        if len(matches) != 1:
            raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_TARGET_COUNT_MISMATCH", str(len(matches)))
        row = matches[0]
        if row["statuscode"] != "200" or row["digest"] != CDX_SHA1_BASE32 or int(row["length"]) != CDX_LENGTH:
            raise DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_PIN_MISMATCH", "exact capture digest, length or status differs")
        receipt["cdx_inventory"] = {
            "http_status": status,
            "content_type": headers.get("content-type", ""),
            "content_length_header": headers.get("content-length", ""),
            "content_encoding": headers.get("content-encoding", ""),
            "transfer_encoding": headers.get("transfer-encoding", ""),
            "response_bytes": len(body),
            "response_sha256": hashlib.sha256(body).hexdigest(),
            "record_count": len(rows),
            "unique_original_url_count": len({item["original"] for item in rows}),
            "target_capture": row,
            "target_capture_verified": True,
            "mimetype_class": "warc_revisit" if row["mimetype"].lower().startswith("warc/revisit") else "ordinary_cdx_mimetype",
            "scope": "same bounded CDX prefix/filter scope as R3; metadata only, no archive replay",
        }
        receipt["status"] = "Q221_DOD_097_CDX_MIMETYPE_DIAGNOSTIC_COMPLETE"
    except DiagnosticError as exc:
        receipt["status"] = exc.status
        receipt["errors"].append({"code": exc.status, "message": exc.message})
    except Exception as exc:
        receipt["status"] = "Q221_DOD_097_CDX_DIAGNOSTIC_UNEXPECTED_FAILURE"
        receipt["errors"].append({"code": "UNEXPECTED_EXCEPTION", "message": type(exc).__name__})
    finally:
        receipt["source_probe"].update({
            "request_count": state["request_count"],
            "response_bytes": state["response_bytes"],
            "responses": state["responses"],
            "transport_errors": state["transport_errors"],
            "archive_replay_request_count": 0,
            "archive_payload_downloaded": False,
        })
        receipt["safety"].update({
            "source_requests_made": state["request_count"],
            "archive_replay_allowed": False,
            "archive_payload_persisted": False,
            "archive_schema_examined": False,
            "transaction_row_presence_examined": False,
            "scientific_evidence": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        })
        receipt["receipt_fingerprint"] = fingerprint(receipt)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--prereg", type=Path, default=None)
    parser.add_argument("--request", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    try:
        inputs = validate_inputs(root, args.prereg, args.request)
    except DiagnosticError as exc:
        print(json.dumps({"status": exc.status, "message": exc.message}, sort_keys=True))
        return 2
    if args.validate_only:
        print(json.dumps({
            "status": "Q221_DOD_097_CDX_DIAGNOSTIC_FROZEN_INPUTS_VALID",
            "manifest_blob_sha1": inputs["manifest_blob_sha1"],
            "target_count": inputs["target_count"],
            "source_requests_made": 0,
        }, sort_keys=True))
        return 0
    receipt = run_diagnostic(root, args.prereg, args.request, args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "Q221_DOD_097_CDX_MIMETYPE_DIAGNOSTIC_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
