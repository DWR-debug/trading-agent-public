"""One-shot HEAD-only Wayback raw-replay response-header diagnostic for Q221 DoD 097.

Makes one HEAD request to the exact pinned replay URL. It never reads or persists
an archive response body, never issues a GET, and never examines CSV/ZIP rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

PREREG_PATH = "research/preregistrations/q221_dod_097_wayback_replay_head_r6_2026_10_16.json"
REQUEST_PATH = "research/run_requests/q221_dod_097_wayback_replay_head_r6.trigger"
R3_RECEIPT_PATH = "research/evidence/q221_dod_097_wayback_archive_presence_attempt_38798769065.json"
R5_RECEIPT_PATH = "research/evidence/q221_dod_097_cdx_mimetype_diagnostic_r5_attempt_38855135000.json"
MANIFEST_PATH = "research/evidence/q221_historical_public_boundary_latest.json"
MANIFEST_BLOB = "b78cf6f7b48af3f914ee7c6d06a38f6485b0438f"
MANIFEST_FP = "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
R3_BLOB = "91e45f71a2b31721375f8fa0812ebac038fc8d1f"
R3_FP = "895a6d4e343cb535866df81ce06d6d824e1d05b1c7af114aa3befeb5c5473a5b"
R5_BLOB = "9f2eb4d0e1efb419e39cb2cb8909842fd93f8164"
R5_FP = "a29529db8730d85c3c72a2b773033faa39653ef62a9d69703ce5a60433a9fc9d"
REPLAY_URL = "https://web.archive.org/web/20250128184322id_/https://files.usaspending.gov/award_data_archive/FY2025_097_Contracts_Full_20250106.zip"
ARCHIVE_URL = "https://files.usaspending.gov/award_data_archive/FY2025_097_Contracts_Full_20250106.zip"
CAPTURE_TIMESTAMP = "20250128184322"
CDX_SHA1_BASE32 = "IYPLEC2VXYNMEA2CUHSSPVKPEJRKBJQB"
CDX_LENGTH = 13605284
MAX_REQUESTS = 1
TIMEOUT_SECONDS = 60
REQUEST_SEQUENCE = "2026-10-16T05:36:08Z"
ALLOWED_HEADERS = ["content-length","content-type","content-encoding","transfer-encoding","last-modified","date","server","accept-ranges","content-range","etag"]
TARGET_ARCHIVE = {"filename":"FY2025_097_Contracts_Full_20250106.zip","original_url":"https://files.usaspending.gov/award_data_archive/FY2025_097_Contracts_Full_20250106.zip","wayback_capture_timestamp":"20250128184322","capture_timestamp_utc":"2025-01-28T18:43:22Z","cdx_sha1_base32":"IYPLEC2VXYNMEA2CUHSSPVKPEJRKBJQB","cdx_length_bytes":13605284}
EXPECTED_MANIFEST = {"path":"research/evidence/q221_historical_public_boundary_latest.json","git_blob_sha1":"b78cf6f7b48af3f914ee7c6d06a38f6485b0438f","receipt_fingerprint":"9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4","expected_transaction_count":348,"frozen_target_count":28}
EXPECTED_R3 = {"path":"research/evidence/q221_dod_097_wayback_archive_presence_attempt_38798769065.json","git_blob_sha1":"91e45f71a2b31721375f8fa0812ebac038fc8d1f","receipt_fingerprint":"895a6d4e343cb535866df81ce06d6d824e1d05b1c7af114aa3befeb5c5473a5b","status":"Q221_DOD_097_ARCHIVE_REPLAY_LENGTH_MISMATCH","request_count":2,"archive_replay_response_bytes":13697800,"cdx_length_bytes":13605284,"length_difference_bytes":92516}
EXPECTED_R5 = {"path":"research/evidence/q221_dod_097_cdx_mimetype_diagnostic_r5_attempt_38855135000.json","git_blob_sha1":"9f2eb4d0e1efb419e39cb2cb8909842fd93f8164","receipt_fingerprint":"a29529db8730d85c3c72a2b773033faa39653ef62a9d69703ce5a60433a9fc9d","status":"Q221_DOD_097_CDX_MIMETYPE_DIAGNOSTIC_COMPLETE","request_count":1,"mimetype":"application/zip","target_timestamp":"20250128184322","cdx_length_bytes":13605284}
EXPECTED_CONTRACT = {"question":"Which HTTP response headers does the exact Wayback raw-replay endpoint currently advertise for a HEAD request, without retrieving the archive body?","method":"HEAD","endpoint_url":"https://web.archive.org/web/20250128184322id_/https://files.usaspending.gov/award_data_archive/FY2025_097_Contracts_Full_20250106.zip","expected_capture_timestamp":"20250128184322","allowed_header_names":["content-length","content-type","content-encoding","transfer-encoding","last-modified","date","server","accept-ranges","content-range","etag"],"max_source_requests":1,"timeout_seconds":60,"redirect_policy":"reject","automatic_retries":0,"alternate_sources_allowed":false,"response_body_read_bytes":0,"archive_payload_download_allowed":false,"archive_replay_get_allowed":false,"transaction_row_presence_examined":false}
EXPECTED_SAFETY = {"paper_only":true,"live_trading_enabled":false,"orders_enabled":false,"scientific_evidence":false,"performance_authorization":false,"holdout_selection":false,"ranking":false,"tuning":false,"promotion":false,"live_execution":false,"source_population_changed":false,"census_restarted":false,"alternate_source_used":false,"automatic_retry":false,"archive_replay_get_allowed":false,"archive_payload_download_allowed":false,"archive_payload_persisted":false,"archive_schema_examined":false,"transaction_row_presence_examined":false,"recipient_to_issuer_mapping_frozen":false,"historical_first_public_observation_proven":false,"event_level_public_boundary_proven":false}
FROZEN_REQUEST = {"RUN_Q221_DOD_097_WAYBACK_REPLAY_HEAD_R6":"true","REASON":"CAPTURE_MISSING_HTTP_RESPONSE_HEADERS_AFTER_R3_BODY_LENGTH_MISMATCH_AND_R5_ORDINARY_CDX_MIMETYPE","SOURCE_MANIFEST_PATH":"research/evidence/q221_historical_public_boundary_latest.json","SOURCE_MANIFEST_GIT_BLOB_SHA":"b78cf6f7b48af3f914ee7c6d06a38f6485b0438f","SOURCE_MANIFEST_RECEIPT_FINGERPRINT":"9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4","R3_RECEIPT_PATH":"research/evidence/q221_dod_097_wayback_archive_presence_attempt_38798769065.json","R3_RECEIPT_GIT_BLOB_SHA":"91e45f71a2b31721375f8fa0812ebac038fc8d1f","R3_RECEIPT_FINGERPRINT":"895a6d4e343cb535866df81ce06d6d824e1d05b1c7af114aa3befeb5c5473a5b","R5_RECEIPT_PATH":"research/evidence/q221_dod_097_cdx_mimetype_diagnostic_r5_attempt_38855135000.json","R5_RECEIPT_GIT_BLOB_SHA":"9f2eb4d0e1efb419e39cb2cb8909842fd93f8164","R5_RECEIPT_FINGERPRINT":"a29529db8730d85c3c72a2b773033faa39653ef62a9d69703ce5a60433a9fc9d","TARGET_ARCHIVE_FILENAME":"FY2025_097_Contracts_Full_20250106.zip","TARGET_ARCHIVE_CAPTURE":"20250128184322","TARGET_ARCHIVE_CDX_SHA1_BASE32":"IYPLEC2VXYNMEA2CUHSSPVKPEJRKBJQB","TARGET_ARCHIVE_BYTES":"13605284","REPLAY_URL":"https://web.archive.org/web/20250128184322id_/https://files.usaspending.gov/award_data_archive/FY2025_097_Contracts_Full_20250106.zip","HTTP_METHOD":"HEAD","MAX_REQUESTS":"1","PER_REQUEST_TIMEOUT_SECONDS":"60","RESPONSE_BODY_BYTES_READ":"0","ARCHIVE_REPLAY_GET_ALLOWED":"false","ARCHIVE_PAYLOAD_DOWNLOAD_ALLOWED":"false","ARCHIVE_PAYLOAD_PERSISTED":"false","AUTOMATIC_RETRIES":"false","REDIRECTS_ALLOWED":"false","ALTERNATE_SOURCES_ALLOWED":"false","SOURCE_POPULATION_CHANGED":"false","CENSUS_RESTART":"false","PERFORMANCE":"false","HOLDOUT_SELECTION":"false","RANKING":"false","TUNING":"false","PROMOTION":"false","LIVE_EXECUTION":"false","REQUEST_SEQUENCE":"2026-10-16T05:36:08Z"}


class DiagnosticError(ValueError):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def git_blob_sha1(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


def canonical_fingerprint(receipt: dict) -> str:
    payload = {key: value for key, value in receipt.items() if key != "receipt_fingerprint"}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> dict:
    try:
        item = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DiagnosticError("Q221_R6_FROZEN_INPUT_READ_FAILED", f"{path}:{type(exc).__name__}") from exc
    if not isinstance(item, dict):
        raise DiagnosticError("Q221_R6_FROZEN_INPUT_SHAPE_INVALID", str(path))
    return item


def _marker(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DiagnosticError("Q221_R6_MARKER_MISSING", type(exc).__name__) from exc
    for line_no, line in enumerate(lines, 1):
        if not line or line.strip() != line or "=" not in line:
            raise DiagnosticError("Q221_R6_MARKER_INVALID", f"line {line_no}")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key) or not value or key in values:
            raise DiagnosticError("Q221_R6_MARKER_INVALID", f"key/value at line {line_no}")
        values[key] = value
    return values


def validate_inputs(root: Path, prereg_path: Path | None = None, request_path: Path | None = None) -> dict:
    root = root.resolve()
    prereg_file = Path(prereg_path) if prereg_path is not None else root / PREREG_PATH
    marker_file = Path(request_path) if request_path is not None else root / REQUEST_PATH
    for actual, expected, code in (
        (prereg_file, PREREG_PATH, "Q221_R6_PREREG_PATH_INVALID"),
        (marker_file, REQUEST_PATH, "Q221_R6_MARKER_PATH_INVALID"),
    ):
        try:
            rel = actual.resolve().relative_to(root).as_posix()
        except ValueError as exc:
            raise DiagnosticError(code, "path outside repository root") from exc
        if rel != expected:
            raise DiagnosticError(code, str(actual))

    prereg = read_json(prereg_file)
    if (prereg.get("schema_version") != 1
            or prereg.get("record_type") != "q221_dod_097_wayback_replay_head_metadata_preregistration"
            or prereg.get("candidate_id") != "Q221"
            or prereg.get("attempt_number") != 6
            or prereg.get("request_sequence") != REQUEST_SEQUENCE):
        raise DiagnosticError("Q221_R6_PREREG_IDENTITY_OR_SEQUENCE_INVALID", "frozen identity differs")
    for field, expected in (
        ("frozen_source_manifest", EXPECTED_MANIFEST),
        ("target_archive", TARGET_ARCHIVE),
        ("prior_evidence", {"r3": EXPECTED_R3, "r5": EXPECTED_R5}),
        ("diagnostic_contract", EXPECTED_CONTRACT),
        ("safety", EXPECTED_SAFETY),
    ):
        if prereg.get(field) != expected:
            raise DiagnosticError("Q221_R6_PREREG_PIN_MISMATCH", field)

    loaded: dict[str, dict] = {}
    for relative, expected_blob, expected_fp, error_code in (
        (MANIFEST_PATH, MANIFEST_BLOB, None, "Q221_R6_MANIFEST_BLOB_MISMATCH"),
        (R3_RECEIPT_PATH, R3_BLOB, R3_FP, "Q221_R6_R3_RECEIPT_PIN_MISMATCH"),
        (R5_RECEIPT_PATH, R5_BLOB, R5_FP, "Q221_R6_R5_RECEIPT_PIN_MISMATCH"),
    ):
        path = root / relative
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise DiagnosticError("Q221_R6_PINNED_INPUT_MISSING", relative) from exc
        if git_blob_sha1(raw) != expected_blob:
            raise DiagnosticError(error_code, relative + ":git_blob_sha1")
        if expected_fp:
            value = read_json(path)
            if canonical_fingerprint(value) != expected_fp or value.get("receipt_fingerprint") != expected_fp:
                raise DiagnosticError(error_code, relative + ":receipt_fingerprint")
            loaded[relative] = value

    r3 = loaded[R3_RECEIPT_PATH]
    r3_probe = r3.get("source_probe", {})
    r3_responses = r3_probe.get("responses", [])
    if (r3.get("status") != EXPECTED_R3["status"]
            or r3_probe.get("request_count") != 2
            or len(r3_responses) != 2
            or r3_responses[1].get("response_bytes") != EXPECTED_R3["archive_replay_response_bytes"]
            or r3_responses[1].get("http_status") != 200
            or r3_responses[1].get("content_type") != "application/zip"
            or r3_probe.get("cdx_inventory", {}).get("pinned_target_capture", {}).get("length") != str(CDX_LENGTH)):
        raise DiagnosticError("Q221_R6_R3_EVIDENCE_SHAPE_MISMATCH", "frozen R3 replay evidence differs")
    if any(k in r3_responses[1] for k in ("content_length", "content_encoding", "transfer_encoding")):
        raise DiagnosticError("Q221_R6_R3_HEADER_GAP_PRECONDITION_CHANGED", "R3 already contains the intended fields")

    r5 = loaded[R5_RECEIPT_PATH]
    r5_probe = r5.get("source_probe", {})
    target_row = r5.get("cdx_inventory", {}).get("target_capture", {})
    if (r5.get("status") != EXPECTED_R5["status"]
            or r5_probe.get("request_count") != 1
            or target_row.get("mimetype") != "application/zip"
            or target_row.get("timestamp") != CAPTURE_TIMESTAMP
            or target_row.get("length") != str(CDX_LENGTH)
            or r5_probe.get("archive_replay_request_count") != 0):
        raise DiagnosticError("Q221_R6_R5_EVIDENCE_SHAPE_MISMATCH", "frozen R5 metadata differs")

    marker = _marker(marker_file)
    if marker != FROZEN_REQUEST:
        raise DiagnosticError("Q221_R6_MARKER_PIN_MISMATCH", "marker differs from frozen request")
    datetime.strptime(marker["REQUEST_SEQUENCE"], "%Y-%m-%dT%H:%M:%SZ")
    parsed = urlparse(REPLAY_URL)
    if (parsed.scheme != "https" or parsed.hostname != "web.archive.org"
            or parsed.path != "/web/20250128184322id_/https://files.usaspending.gov/award_data_archive/FY2025_097_Contracts_Full_20250106.zip"):
        raise DiagnosticError("Q221_R6_REPLAY_URL_NOT_PINNED", REPLAY_URL)
    return {"manifest_blob_sha1": MANIFEST_BLOB, "r3_receipt_fingerprint": R3_FP,
            "r5_receipt_fingerprint": R5_FP, "target_archive": TARGET_ARCHIVE,
            "preregistration_path": PREREG_PATH, "request_marker_path": REQUEST_PATH}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def head_only(url: str, state: dict) -> tuple[int, dict[str, str]]:
    if state["request_count"] >= MAX_REQUESTS:
        raise DiagnosticError("Q221_R6_REQUEST_CAP_EXCEEDED", "one HEAD request maximum")
    if url != REPLAY_URL:
        raise DiagnosticError("Q221_R6_URL_NOT_PINNED", url)
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "web.archive.org" or parsed.username or parsed.password:
        raise DiagnosticError("Q221_R6_HOST_FORBIDDEN", url)
    state["request_count"] += 1
    request = urllib.request.Request(
        url, method="HEAD",
        headers={
            "User-Agent": "DWR-debug/trading-agent-public/Q221-DOD-097-Replay-HEAD-R6/1.0",
            "Accept": "*/*", "Accept-Encoding": "identity",
        },
    )
    opener = urllib.request.build_opener(_NoRedirect())
    status = 0
    headers: dict[str, str] = {}
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            status = int(getattr(response, "status", 200))
            raw_headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
            headers = {key: raw_headers[key] for key in ALLOWED_HEADERS if key in raw_headers}
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw_headers = {str(k).lower(): str(v) for k, v in (exc.headers or {}).items()}
        headers = {key: raw_headers[key] for key in ALLOWED_HEADERS if key in raw_headers}
        exc.close()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        state["transport_errors"].append(type(exc).__name__)
        raise DiagnosticError("Q221_R6_HEAD_TRANSPORT_ERROR", type(exc).__name__) from exc
    state["responses"].append({"method": "HEAD", "url": REPLAY_URL, "http_status": status, "headers": headers, "response_body_read_bytes": 0})
    if 300 <= status < 400:
        raise DiagnosticError("Q221_R6_HEAD_REDIRECT_BLOCKED", str(status))
    if status != 200:
        raise DiagnosticError("Q221_R6_HEAD_HTTP_NOT_200", str(status))
    return status, headers


def _base_receipt() -> dict:
    return {
        "schema_version": 1, "record_type": "q221_dod_097_wayback_replay_head_metadata_diagnostic",
        "candidate_id": "Q221", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_of_truth": "DWR-debug/trading-agent-public", "status": "Q221_R6_NOT_RUN",
        "request": {"request_sequence": REQUEST_SEQUENCE, "preregistration_path": PREREG_PATH,
            "request_marker_path": REQUEST_PATH, "method": "HEAD", "url": REPLAY_URL,
            "timeout_seconds": TIMEOUT_SECONDS, "request_cap": MAX_REQUESTS,
            "archive_replay_get_allowed": False, "archive_payload_download_allowed": False},
        "lineage": {"manifest": EXPECTED_MANIFEST, "r3": EXPECTED_R3, "r5": EXPECTED_R5},
        "http_metadata": {"http_status": None, "headers": {}, "response_body_read_bytes": 0},
        "source_probe": {"request_count": 0, "responses": [], "transport_errors": [],
            "archive_endpoint_request_count": 0, "archive_replay_get_request_count": 0,
            "archive_payload_body_read": False, "archive_payload_persisted": False,
            "response_body_read_bytes": 0},
        "interpretation": {"diagnostic_only": True, "head_headers_describe_current_server_response": True,
            "archived_payload_bytes_verified": False, "cdx_length_explained": False,
            "archive_schema_examined": False, "transaction_row_presence_examined": False,
            "first_public_observation_time_proven": False, "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False},
        "safety": {**EXPECTED_SAFETY, "source_requests_made": 0, "archive_endpoint_request_count": 0,
            "archive_replay_get_request_count": 0, "response_body_read_bytes": 0,
            "archive_payload_body_read": False, "archive_payload_persisted": False},
        "errors": [],
        "next_gate": "HEAD response metadata only. The R3 body/CDX length discrepancy and all historical public-clock gates remain unresolved.",
    }


def run_diagnostic(root: Path, output_path: Path, fetcher=None) -> dict:
    receipt = _base_receipt()
    state = {"request_count": 0, "responses": [], "transport_errors": []}
    try:
        inputs = validate_inputs(root)
        receipt["lineage"]["manifest_blob_sha1_verified"] = inputs["manifest_blob_sha1"]
        status, headers = (fetcher or head_only)(REPLAY_URL, state)
        receipt["http_metadata"] = {"http_status": status, "headers": headers, "response_body_read_bytes": 0}
        receipt["status"] = "Q221_R6_HEAD_METADATA_CAPTURED"
    except DiagnosticError as exc:
        receipt["status"] = exc.status
        receipt["errors"].append({"code": exc.status, "message": exc.message})
    except Exception as exc:
        receipt["status"] = "Q221_R6_UNEXPECTED_FAILURE"
        receipt["errors"].append({"code": "UNEXPECTED_EXCEPTION", "message": type(exc).__name__})
    finally:
        receipt["source_probe"].update({"request_count": state["request_count"], "responses": state["responses"],
            "transport_errors": state["transport_errors"], "archive_endpoint_request_count": state["request_count"],
            "archive_replay_get_request_count": 0, "archive_payload_body_read": False,
            "archive_payload_persisted": False, "response_body_read_bytes": 0})
        receipt["safety"].update({"source_requests_made": state["request_count"],
            "archive_endpoint_request_count": state["request_count"], "archive_replay_get_request_count": 0,
            "response_body_read_bytes": 0, "archive_payload_body_read": False, "archive_payload_persisted": False})
        receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        inputs = validate_inputs(args.repo_root.resolve())
    except DiagnosticError as exc:
        print(json.dumps({"status": exc.status, "message": exc.message}, sort_keys=True))
        return 2
    if args.validate_only:
        print(json.dumps({"status": "Q221_R6_FROZEN_INPUTS_VALID", "manifest_blob_sha1": inputs["manifest_blob_sha1"], "source_requests_made": 0}, sort_keys=True))
        return 0
    receipt = run_diagnostic(args.repo_root.resolve(), args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "Q221_R6_HEAD_METADATA_CAPTURED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
