"""One-shot, bounded Q221 DoD 097 Wayback archive schema/row-presence probe."""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

MANIFEST_PATH = "research/evidence/q221_historical_public_boundary_latest.json"
MANIFEST_BLOB = "b78cf6f7b48af3f914ee7c6d06a38f6485b0438f"
MANIFEST_FP = "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
PREREG_PATH = "research/preregistrations/q221_dod_097_wayback_archive_presence_2026_10_15.json"
REQUEST_PATH = "research/run_requests/q221_dod_097_wayback_archive_presence.trigger"
CDX_ENDPOINT = "https://web.archive.org/cdx/search/cdx"
ARCHIVE_FILENAME = "FY2025_097_Contracts_Full_20250106.zip"
ARCHIVE_URL = "https://files.usaspending.gov/award_data_archive/" + ARCHIVE_FILENAME
CAPTURE_TIMESTAMP = "20250128184322"
CAPTURE_UTC = "2025-01-28T18:43:22Z"
CDX_SHA1_BASE32 = "IYPLEC2VXYNMEA2CUHSSPVKPEJRKBJQB"
CDX_LENGTH = 13_605_284
REPLAY_URL = "https://web.archive.org/web/" + CAPTURE_TIMESTAMP + "id_/" + ARCHIVE_URL
TARGET_COUNT = 28
MANIFEST_COUNT = 348
MAX_REQUESTS, MAX_CDX_BYTES, MAX_ARCHIVE_BYTES, MAX_TOTAL_BYTES = 2, 5_000_000, 20_000_000, 25_000_000
MAX_UNCOMPRESSED_BYTES, MAX_ZIP_MEMBERS, MAX_CSV_FILES, MAX_CSV_ROWS = 250_000_000, 512, 128, 2_000_000
FROZEN_REQUEST = {
    "RUN_Q221_DOD_097_WAYBACK_ARCHIVE_PRESENCE": "true",
    "REASON": "BOUNDED_WAYBACK_ARCHIVE_097_SCHEMA_AND_FROZEN_ROW_PRESENCE",
    "SOURCE_MANIFEST_PATH": MANIFEST_PATH,
    "SOURCE_MANIFEST_GIT_BLOB_SHA": MANIFEST_BLOB,
    "SOURCE_MANIFEST_RECEIPT_FINGERPRINT": MANIFEST_FP,
    "TARGET_ARCHIVE_FILENAME": ARCHIVE_FILENAME,
    "TARGET_ARCHIVE_CAPTURE": CAPTURE_TIMESTAMP,
    "TARGET_ARCHIVE_CDX_SHA1_BASE32": CDX_SHA1_BASE32,
    "TARGET_ARCHIVE_BYTES": str(CDX_LENGTH),
    "MAX_REQUESTS": str(MAX_REQUESTS),
    "MAX_CDX_RESPONSE_BYTES": str(MAX_CDX_BYTES),
    "MAX_ARCHIVE_RESPONSE_BYTES": str(MAX_ARCHIVE_BYTES),
    "MAX_TOTAL_RESPONSE_BYTES": str(MAX_TOTAL_BYTES),
    "MAX_UNCOMPRESSED_ARCHIVE_BYTES": str(MAX_UNCOMPRESSED_BYTES),
    "MAX_ZIP_MEMBERS": str(MAX_ZIP_MEMBERS),
    "CENSUS_RESTART": "false",
    "PERFORMANCE": "false", "HOLDOUT_SELECTION": "false", "RANKING": "false",
    "TUNING": "false", "PROMOTION": "false", "LIVE_EXECUTION": "false",
    "REQUEST_SEQUENCE": "2026-10-15T18:53:34Z",
}

# R2 is a distinct reviewed recovery. The original one-shot marker and
# preregistration remain byte-for-byte unchanged and cannot authorize this run.
PREREG_PATH_R2 = "research/preregistrations/q221_dod_097_wayback_archive_presence_r2_2026_10_15.json"
REQUEST_PATH_R2 = "research/run_requests/q221_dod_097_wayback_archive_presence_r2.trigger"
R2_REQUEST_SEQUENCE = "2026-10-15T19:35:11Z"
FROZEN_REQUEST_R2 = {
    **{key: value for key, value in FROZEN_REQUEST.items()
       if key != "RUN_Q221_DOD_097_WAYBACK_ARCHIVE_PRESENCE"},
    "RUN_Q221_DOD_097_WAYBACK_ARCHIVE_PRESENCE_R2": "true",
    "REQUEST_SEQUENCE": R2_REQUEST_SEQUENCE,
}

# R3 is separately preregistered after R2's first CDX request timed out at 25 s.
# The only acquisition-method change is a single-request timeout of 60 s.
PREREG_PATH_R3 = "research/preregistrations/q221_dod_097_wayback_archive_presence_r3_2026_10_15.json"
REQUEST_PATH_R3 = "research/run_requests/q221_dod_097_wayback_archive_presence_r3.trigger"
R3_REQUEST_SEQUENCE = "2026-10-15T19:55:24Z"
R3_REQUEST_TIMEOUT_SECONDS = 60
FROZEN_REQUEST_R3 = {
    **{key: value for key, value in FROZEN_REQUEST.items()
       if key != "RUN_Q221_DOD_097_WAYBACK_ARCHIVE_PRESENCE"},
    "RUN_Q221_DOD_097_WAYBACK_ARCHIVE_PRESENCE_R3": "true",
    "REQUEST_SEQUENCE": R3_REQUEST_SEQUENCE,
    "PER_REQUEST_TIMEOUT_SECONDS": str(R3_REQUEST_TIMEOUT_SECONDS),
}
ALIASES = {
    "piid": ("award_id_piid", "piid"),
    "modification": ("modification_number", "modification", "mod_number"),
    "action_date": ("action_date", "transaction_action_date"),
    "recipient_uei": ("recipient_uei", "uei"),
}
AGENCY_CODE_ALIASES = ("awarding_agency_code", "awarding_agency_identifier", "awarding_agency_id")


class ProbeError(ValueError):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status, self.message = status, message


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _fingerprint(value: dict[str, Any]) -> str:
    """Return the canonical receipt fingerprint, excluding its own field."""
    payload = {key: item for key, item in value.items() if key != "receipt_fingerprint"}
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return _sha256(canonical)


def _blob_sha1(body: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(body)).encode("ascii") + b"\0" + body).hexdigest()


def _json(path: Path) -> dict:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProbeError("Q221_DOD_097_FROZEN_INPUT_READ_FAILED", type(exc).__name__) from exc
    if not isinstance(obj, dict):
        raise ProbeError("Q221_DOD_097_FROZEN_INPUT_SHAPE_INVALID", str(path))
    return obj


def _marker(path: Path, expected_request: dict[str, str] = FROZEN_REQUEST) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ProbeError("Q221_DOD_097_REQUEST_MARKER_MISSING", type(exc).__name__) from exc
    out = {}
    for i, line in enumerate(lines, 1):
        if not line or line.strip() != line or "=" not in line:
            raise ProbeError("Q221_DOD_097_REQUEST_MARKER_INVALID", "line " + str(i))
        key, val = line.split("=", 1)
        if not re.fullmatch(r"[A-Z0-9_]+", key) or not val or key in out:
            raise ProbeError("Q221_DOD_097_REQUEST_MARKER_INVALID", "key/value at line " + str(i))
        out[key] = val
    if out != expected_request:
        raise ProbeError("Q221_DOD_097_REQUEST_MARKER_PIN_MISMATCH", "marker differs from frozen request profile")
    datetime.strptime(out["REQUEST_SEQUENCE"], "%Y-%m-%dT%H:%M:%SZ")
    return out


def _validate_prereg(
    p: dict, expected_request: dict[str, str] = FROZEN_REQUEST
) -> None:
    profile = (
        "R3" if expected_request.get("RUN_Q221_DOD_097_WAYBACK_ARCHIVE_PRESENCE_R3") == "true"
        else "R2" if expected_request.get("RUN_Q221_DOD_097_WAYBACK_ARCHIVE_PRESENCE_R2") == "true"
        else "R1"
    )
    expected_type = (
        "q221_dod_097_wayback_archive_presence_preregistration"
        if profile == "R1" else "q221_dod_097_wayback_archive_presence_recovery_preregistration"
    )
    if p.get("schema_version") != 1 or p.get("record_type") != expected_type:
        raise ProbeError("Q221_DOD_097_PREREGISTRATION_TYPE_INVALID", "type/version differs")
    if profile == "R2":
        expected_recovery = {
            "prior_workflow_run_id": 38791554425,
            "prior_attempt_status": "Q221_DOD_097_ONE_SHOT_ATTEMPT_FAILED_RECEIPT_NOT_PERSISTED_NO_ROW_RESULT",
            "source_request_count_known": False,
            "archive_outcome_known": False,
            "original_marker_reuse_authorized": False,
            "reason": "The first probe failed while serializing its receipt. Its source request count and archive outcome are unknown; this R2 attempt has a separate preregistration and marker.",
        }
        if p.get("attempt_number") != 2 or p.get("recovery") != expected_recovery:
            raise ProbeError("Q221_DOD_097_RECOVERY_PREREGISTRATION_INVALID", "R2 recovery lineage differs")
    elif profile == "R3":
        expected_recovery = {
            "prior_workflow_run_id": 38797148893,
            "prior_attempt_status": "Q221_DOD_097_WAYBACK_TRANSPORT_ERROR",
            "prior_source_request_count": 1,
            "prior_source_request_count_known": True,
            "prior_response_bytes": 0,
            "prior_archive_outcome_known": False,
            "original_marker_reuse_authorized": False,
            "reason": "R2 made one CDX request with zero response bytes and recorded TimeoutError at the frozen 25-second timeout. R3 uses a distinct preregistration and marker and changes only the per-request timeout to 60 seconds; the source, selected keys, request-count ceiling, byte/ZIP/CSV caps, interpretation, and scientific gates remain unchanged.",
        }
        expected_transport = {
            "previous_per_request_timeout_seconds": 25,
            "per_request_timeout_seconds": 60,
            "max_source_requests": 2,
            "automatic_retries": 0,
            "alternate_sources_allowed": False,
            "scope_or_caps_changed": False,
        }
        if p.get("attempt_number") != 3 or p.get("recovery") != expected_recovery:
            raise ProbeError("Q221_DOD_097_RECOVERY_PREREGISTRATION_INVALID", "R3 recovery lineage differs")
        if p.get("transport_contract") != expected_transport:
            raise ProbeError("Q221_DOD_097_TRANSPORT_CONTRACT_MISMATCH", "R3 timeout or invariants differ")
    if p.get("frozen_source_manifest") != {
        "path": MANIFEST_PATH, "git_blob_sha1": MANIFEST_BLOB, "receipt_fingerprint": MANIFEST_FP,
        "expected_transaction_count": MANIFEST_COUNT,
    }:
        raise ProbeError("Q221_DOD_097_PREREGISTRATION_SOURCE_PIN_MISMATCH", "manifest pins differ")
    arch = p.get("archive_capture", {})
    expected = {
        "filename": ARCHIVE_FILENAME, "original_url": ARCHIVE_URL,
        "wayback_capture_timestamp": CAPTURE_TIMESTAMP, "capture_timestamp_utc": CAPTURE_UTC,
        "cdx_sha1_base32": CDX_SHA1_BASE32, "length_bytes": CDX_LENGTH,
    }
    if any(arch.get(k) != v for k, v in expected.items()):
        raise ProbeError("Q221_DOD_097_PREREGISTRATION_ARCHIVE_PIN_MISMATCH", "archive pins differ")
    sel = p.get("frozen_row_selection", {})
    if (sel.get("fiscal_year") != 2025 or sel.get("awarding_agency") != "Department of Defense"
        or sel.get("agency_exception_class") != "DOD_90_DAY_EXCEPTION_CANDIDATE"
        or sel.get("expected_row_count") != TARGET_COUNT
        or sel.get("match_fields") != ["PIID", "modification", "action_date", "recipient_uei"]):
        raise ProbeError("Q221_DOD_097_PREREGISTRATION_SELECTION_MISMATCH", "selection differs")
    if p.get("caps") != {
        "source_requests": MAX_REQUESTS, "cdx_response_bytes": MAX_CDX_BYTES,
        "archive_response_bytes": MAX_ARCHIVE_BYTES, "total_response_bytes": MAX_TOTAL_BYTES,
        "uncompressed_archive_bytes": MAX_UNCOMPRESSED_BYTES, "zip_members": MAX_ZIP_MEMBERS,
        "csv_files": MAX_CSV_FILES, "csv_rows": MAX_CSV_ROWS,
    }:
        raise ProbeError("Q221_DOD_097_PREREGISTRATION_CAP_MISMATCH", "caps differ")
    safety = p.get("safety_contract", {})
    for k in (
        "source_population_changes", "census_restart", "historical_first_public_observation_proven",
        "event_level_public_boundary_proven", "recipient_to_issuer_mapping_frozen", "scientific_evidence",
        "performance_authorization", "holdout_selection", "ranking", "tuning", "promotion", "live_execution",
    ):
        if safety.get(k) is not False:
            raise ProbeError("Q221_DOD_097_PREREGISTRATION_SAFETY_MISMATCH", k)
    if p.get("request_sequence") != expected_request["REQUEST_SEQUENCE"]:
        raise ProbeError("Q221_DOD_097_PREREGISTRATION_SEQUENCE_MISMATCH", "request sequence differs")


def _fy(date_text: str) -> int:
    try:
        d = datetime.strptime(str(date_text)[:10], "%Y-%m-%d").date()
    except ValueError as exc:
        raise ProbeError("Q221_DOD_097_FROZEN_ACTION_DATE_INVALID", str(date_text)) from exc
    return d.year + int(d.month >= 10)


def _composite_from_key(key: str) -> tuple[str, str, str, str]:
    parts = key.split("|")
    if len(parts) != 5:
        raise ProbeError("Q221_DOD_097_FROZEN_TRANSACTION_KEY_INVALID", key)
    return parts[0].strip().upper(), parts[1].strip().upper(), parts[2].strip()[:10], parts[4].strip().upper()


def select_frozen_targets(manifest: dict) -> list[dict]:
    rows, queries = manifest.get("transactions"), manifest.get("queries")
    if not isinstance(rows, list) or not isinstance(queries, list) or len(rows) != MANIFEST_COUNT:
        raise ProbeError("Q221_DOD_097_MANIFEST_SHAPE_OR_COUNT_INVALID", "expected 348 transactions")
    query_keys = {key for q in queries if isinstance(q, dict) for key in q.get("selected_transaction_keys", []) if isinstance(key, str)}
    if len(query_keys) != MANIFEST_COUNT:
        raise ProbeError("Q221_DOD_097_MANIFEST_QUERY_KEY_COUNT_MISMATCH", str(len(query_keys)))
    seen, composites, targets = set(), set(), []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("transaction_key"), str):
            raise ProbeError("Q221_DOD_097_MANIFEST_TRANSACTION_SHAPE_INVALID", "invalid row")
        key = row["transaction_key"]
        if key not in query_keys or key in seen:
            raise ProbeError("Q221_DOD_097_MANIFEST_KEY_NOT_UNIQUELY_FROZEN", key)
        seen.add(key)
        if _fy(str(row.get("action_date", ""))) != 2025:
            continue
        if row.get("awarding_agency") != "Department of Defense" or row.get("agency_exception_class") != "DOD_90_DAY_EXCEPTION_CANDIDATE":
            continue
        piid, mod, action_date, uei = _composite_from_key(key)
        composite = (piid, mod, action_date, uei)
        if composite in composites:
            raise ProbeError("Q221_DOD_097_FROZEN_COMPOSITE_KEY_COLLISION", "duplicate target composite")
        composites.add(composite)
        targets.append({
            "transaction_key": key, "piid": piid, "modification": mod, "action_date": action_date,
            "recipient_uei": uei, "awarding_agency": row["awarding_agency"],
            "agency_exception_class": row["agency_exception_class"],
        })
    targets.sort(key=lambda x: x["transaction_key"])
    if len(targets) != TARGET_COUNT:
        raise ProbeError("Q221_DOD_097_FROZEN_TARGET_COUNT_MISMATCH", str(len(targets)))
    return targets


def validate_frozen_inputs(root: Path, prereg_path: Path | None = None, request_path: Path | None = None) -> dict:
    root = root.resolve()
    request_file = Path(request_path) if request_path is not None else root / REQUEST_PATH
    try:
        request_rel = request_file.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise ProbeError("Q221_DOD_097_REQUEST_PROFILE_PATH_INVALID", "request path is outside repo root") from exc
    profiles = {
        REQUEST_PATH: ("R1", FROZEN_REQUEST, PREREG_PATH, 1),
        REQUEST_PATH_R2: ("R2", FROZEN_REQUEST_R2, PREREG_PATH_R2, 2),
        REQUEST_PATH_R3: ("R3", FROZEN_REQUEST_R3, PREREG_PATH_R3, 3),
    }
    if request_rel not in profiles:
        raise ProbeError("Q221_DOD_097_REQUEST_PROFILE_NOT_ALLOWED", request_rel)
    request_profile, expected_request, expected_prereg_rel, attempt_number = profiles[request_rel]
    prereg_file = Path(prereg_path) if prereg_path is not None else root / expected_prereg_rel
    try:
        prereg_rel = prereg_file.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise ProbeError("Q221_DOD_097_PREREGISTRATION_PATH_INVALID", "preregistration path is outside repo root") from exc
    if prereg_rel != expected_prereg_rel:
        raise ProbeError("Q221_DOD_097_PREREGISTRATION_PROFILE_MISMATCH", prereg_rel)
    prereg = _json(prereg_file)
    _validate_prereg(prereg, expected_request)
    request = _marker(request_file, expected_request)
    request_timeout_seconds = prereg.get("transport_contract", {}).get("per_request_timeout_seconds", 25)
    expected_timeout = R3_REQUEST_TIMEOUT_SECONDS if request_profile == "R3" else 25
    if isinstance(request_timeout_seconds, bool) or request_timeout_seconds != expected_timeout:
        raise ProbeError("Q221_DOD_097_REQUEST_TIMEOUT_PROFILE_MISMATCH", str(request_timeout_seconds))
    path = root / MANIFEST_PATH
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ProbeError("Q221_DOD_097_MANIFEST_MISSING", type(exc).__name__) from exc
    blob = _blob_sha1(raw)
    if blob != MANIFEST_BLOB:
        raise ProbeError("Q221_DOD_097_MANIFEST_BLOB_SHA_MISMATCH", blob)
    manifest = _json(path)
    if manifest.get("candidate_id") != "Q221" or manifest.get("receipt_fingerprint") != MANIFEST_FP:
        raise ProbeError("Q221_DOD_097_MANIFEST_RECEIPT_FP_MISMATCH", "candidate/receipt differs")
    return {
        "preregistration": prereg, "request": request, "manifest_blob_sha1": blob,
        "targets": select_frozen_targets(manifest), "request_profile": request_profile,
        "attempt_number": attempt_number, "preregistration_path": prereg_rel, "request_marker_path": request_rel,
        "request_timeout_seconds": request_timeout_seconds,
    }


def build_cdx_query_url() -> str:
    params = [
        ("url", "files.usaspending.gov/award_data_archive/"), ("matchType", "prefix"), ("output", "json"),
        ("filter", "statuscode:200"), ("filter", "original:.*097.*Contracts.*zip"),
        ("fl", "timestamp,original,statuscode,digest,length"), ("from", "2019"), ("to", "2026"),
        ("limit", "100"), ("gzip", "false"),
    ]
    return CDX_ENDPOINT + "?" + urllib.parse.urlencode(params)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_wayback_bounded(url: str, state: dict, cap: int) -> tuple[int, bytes, dict[str, str]]:
    if state.get("request_count", 0) >= MAX_REQUESTS:
        raise ProbeError("Q221_DOD_097_REQUEST_COUNT_CAP_EXCEEDED", "two requests is the hard cap")
    u = urlparse(url)
    if u.scheme != "https" or u.hostname != "web.archive.org" or u.username or u.password or u.port not in (None, 443):
        raise ProbeError("Q221_DOD_097_NON_WAYBACK_URL_FORBIDDEN", url)
    request_timeout = state.get("request_timeout_seconds", 25)
    if isinstance(request_timeout, bool) or not isinstance(request_timeout, int) or not 1 <= request_timeout <= 60:
        raise ProbeError("Q221_DOD_097_REQUEST_TIMEOUT_INVALID", str(request_timeout))
    state["request_count"] += 1
    req = urllib.request.Request(url, headers={"User-Agent": "DWR-debug/trading-agent-public/Q221-DOD-097-wayback-probe/1.0",
                                             "Accept": "application/json,application/zip,*/*",
                                             "Accept-Encoding": "identity"})
    opener = urllib.request.build_opener(_NoRedirect())
    status, headers, body = 0, {}, b""
    try:
        with opener.open(req, timeout=request_timeout) as resp:
            status = int(getattr(resp, "status", 200))
            headers = {str(k).lower(): str(v) for k, v in resp.headers.items()}
            body = resp.read(cap + 1)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        headers = {str(k).lower(): str(v) for k, v in (exc.headers or {}).items()}
        body = exc.read(cap + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        state["transport_errors"].append(type(exc).__name__)
        raise ProbeError("Q221_DOD_097_WAYBACK_TRANSPORT_ERROR", type(exc).__name__) from exc
    state["response_bytes"] += len(body)
    state["responses"].append({"url": url, "http_status": status, "content_type": headers.get("content-type", ""),
                               "response_bytes": len(body), "response_sha256": _sha256(body)})
    if len(body) > cap:
        raise ProbeError("Q221_DOD_097_PER_RESPONSE_BYTE_CAP_EXCEEDED", str(len(body)))
    if state["response_bytes"] > MAX_TOTAL_BYTES:
        raise ProbeError("Q221_DOD_097_TOTAL_RESPONSE_BYTE_CAP_EXCEEDED", str(state["response_bytes"]))
    if 300 <= status < 400:
        raise ProbeError("Q221_DOD_097_REDIRECT_BLOCKED", "HTTP " + str(status))
    if status != 200:
        raise ProbeError("Q221_DOD_097_WAYBACK_HTTP_NOT_200", "HTTP " + str(status))
    return status, body, headers


def parse_cdx_rows(body: bytes) -> list[dict[str, str]]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProbeError("Q221_DOD_097_CDX_NOT_JSON", type(exc).__name__) from exc
    if payload == []:
        return []
    if not isinstance(payload, list) or not payload or not all(isinstance(row, list) for row in payload):
        raise ProbeError("Q221_DOD_097_CDX_SHAPE_INVALID", "expected header and rows")
    fields = ("timestamp", "original", "statuscode", "digest", "length")
    head = payload[0]
    if not isinstance(head, list) or not set(fields).issubset(set(head)):
        raise ProbeError("Q221_DOD_097_CDX_HEADER_INVALID", "required fields missing")
    indices = {field: head.index(field) for field in fields}
    out = []
    for number, raw in enumerate(payload[1:], 1):
        if len(raw) != len(head):
            raise ProbeError("Q221_DOD_097_CDX_ROW_WIDTH_INVALID", str(number))
        row = {field: str(raw[indices[field]]) for field in fields}
        if (not re.fullmatch(r"\d{14}", row["timestamp"])
            or not row["original"].startswith("https://files.usaspending.gov/award_data_archive/")
            or row["statuscode"] != "200" or not row["digest"] or not row["length"].isdigit()):
            raise ProbeError("Q221_DOD_097_CDX_ROW_INVALID", str(number))
        out.append(row)
    if len(out) >= 100:
        raise ProbeError("Q221_DOD_097_CDX_RESULT_CAP_REACHED", "possibly truncated")
    return out


def verify_pinned_capture(rows: list[dict[str, str]]) -> dict[str, str]:
    matches = [r for r in rows if r["original"] == ARCHIVE_URL and r["timestamp"] == CAPTURE_TIMESTAMP]
    if len(matches) != 1:
        raise ProbeError("Q221_DOD_097_PINNED_CDX_CAPTURE_COUNT_MISMATCH", str(len(matches)))
    row = matches[0]
    if row["digest"] != CDX_SHA1_BASE32 or int(row["length"]) != CDX_LENGTH:
        raise ProbeError("Q221_DOD_097_PINNED_CDX_METADATA_MISMATCH", "digest/length differs")
    return row


def _header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.replace("\ufeff", "").strip().lower()).strip("_")


def _id(value: Any) -> str:
    return str(value or "").strip().upper()


def inspect_archive_bytes(body: bytes, targets: list[dict[str, Any]]) -> dict[str, Any]:
    if not body.startswith(b"PK") or not zipfile.is_zipfile(io.BytesIO(body)):
        raise ProbeError("Q221_DOD_097_ARCHIVE_ZIP_INVALID", "not a valid ZIP")
    try:
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            infos = z.infolist()
            if len(infos) > MAX_ZIP_MEMBERS:
                raise ProbeError("Q221_DOD_097_ZIP_MEMBER_COUNT_CAP_EXCEEDED", str(len(infos)))
            expanded = sum(i.file_size for i in infos if not i.is_dir())
            if expanded > MAX_UNCOMPRESSED_BYTES:
                raise ProbeError("Q221_DOD_097_UNCOMPRESSED_BYTE_CAP_EXCEEDED", str(expanded))
            if any(i.flag_bits & 1 for i in infos if not i.is_dir()):
                raise ProbeError("Q221_DOD_097_ENCRYPTED_ZIP_MEMBER_FORBIDDEN", "encrypted member")
            csv_infos = [i for i in infos if not i.is_dir() and i.filename.lower().endswith(".csv")]
            if len(csv_infos) > MAX_CSV_FILES:
                raise ProbeError("Q221_DOD_097_CSV_FILE_COUNT_CAP_EXCEEDED", str(len(csv_infos)))
            lookup = {(t["piid"], t["modification"], t["action_date"], t["recipient_uei"]): t["transaction_key"] for t in targets}
            if len(lookup) != len(targets):
                raise ProbeError("Q221_DOD_097_FROZEN_COMPOSITE_KEY_COLLISION", "non-unique targets")
            found, wrong_code = Counter(), Counter()
            summaries, total_rows, compatible = [], 0, 0
            for info in csv_infos:
                summary = {"member_name": info.filename, "compressed_bytes": info.compress_size,
                           "uncompressed_bytes": info.file_size, "schema_recognized": False,
                           "data_rows_scanned": 0, "matched_target_row_count": 0, "headers_preview": []}
                summaries.append(summary)
                try:
                    stream = io.TextIOWrapper(z.open(info), encoding="utf-8-sig", errors="replace", newline="")
                    reader = csv.DictReader(stream)
                    fields = reader.fieldnames or []
                    if len(fields) > 300:
                        raise ProbeError("Q221_DOD_097_CSV_COLUMN_CAP_EXCEEDED", info.filename)
                    normalized = [_header(str(f)) for f in fields]
                    summary["headers_preview"] = normalized
                    if any(n > 1 for n in Counter(normalized).values()):
                        summary["schema_error"] = "DUPLICATE_NORMALIZED_HEADERS"
                        stream.close()
                        continue
                    raw_by_norm = {n: str(raw) for n, raw in zip(normalized, fields)}
                    columns = {}
                    for field, aliases in ALIASES.items():
                        found_alias = next((a for a in aliases if a in raw_by_norm), None)
                        if found_alias is None:
                            columns = {}
                            break
                        columns[field] = raw_by_norm[found_alias]
                    if not columns:
                        stream.close()
                        continue
                    agency_col = next((raw_by_norm[n] for n in AGENCY_CODE_ALIASES if n in raw_by_norm), None)
                    summary["schema_recognized"], summary["agency_code_column"] = True, agency_col
                    compatible += 1
                    for row in reader:
                        total_rows += 1
                        summary["data_rows_scanned"] += 1
                        if total_rows > MAX_CSV_ROWS:
                            raise ProbeError("Q221_DOD_097_CSV_ROW_CAP_EXCEEDED", str(total_rows))
                        composite = (_id(row.get(columns["piid"])), _id(row.get(columns["modification"])),
                                     str(row.get(columns["action_date"], "") or "").strip()[:10],
                                     _id(row.get(columns["recipient_uei"])))
                        key = lookup.get(composite)
                        if key is None:
                            continue
                        if agency_col is not None and _id(row.get(agency_col)) != "097":
                            wrong_code[key] += 1
                        else:
                            found[key] += 1
                            summary["matched_target_row_count"] += 1
                    stream.close()
                except ProbeError:
                    raise
                except (OSError, UnicodeError, csv.Error, zipfile.BadZipFile) as exc:
                    raise ProbeError("Q221_DOD_097_CSV_READ_FAILED", info.filename + ":" + type(exc).__name__) from exc
            if compatible == 0:
                return {"schema_recognized": False, "schema_status": "Q221_DOD_097_ARCHIVE_CSV_SCHEMA_UNRECOGNIZED",
                        "archive_member_count": len(infos), "csv_member_count": len(csv_infos),
                        "uncompressed_archive_bytes": expanded, "total_csv_rows_scanned": total_rows,
                        "csv_members": summaries, "row_presence": [], "agency_code_validation": "NOT_AVAILABLE"}
            presence = []
            for t in targets:
                key = t["transaction_key"]
                count, wrong = int(found[key]), int(wrong_code[key])
                obs = ("AMBIGUOUS_DUPLICATE_MATCH_IN_ARCHIVE_SNAPSHOT" if count > 1 else
                       "PRESENT_IN_ARCHIVE_SNAPSHOT" if count == 1 else
                       "IDENTITY_MATCH_BUT_AGENCY_CODE_MISMATCH" if wrong else
                       "NOT_FOUND_IN_THIS_ARCHIVE_SNAPSHOT_ONLY")
                presence.append({"transaction_key": key, "piid": t["piid"], "modification": t["modification"],
                                 "action_date": t["action_date"], "recipient_uei": t["recipient_uei"],
                                 "matching_rows": count, "rows_with_wrong_agency_code": wrong, "observation_status": obs})
            counts = {
                "present": sum(r["observation_status"] == "PRESENT_IN_ARCHIVE_SNAPSHOT" for r in presence),
                "absent_from_this_snapshot_only": sum(r["observation_status"] == "NOT_FOUND_IN_THIS_ARCHIVE_SNAPSHOT_ONLY" for r in presence),
                "ambiguous": sum(r["observation_status"] == "AMBIGUOUS_DUPLICATE_MATCH_IN_ARCHIVE_SNAPSHOT" for r in presence),
                "agency_code_mismatch": sum(r["observation_status"] == "IDENTITY_MATCH_BUT_AGENCY_CODE_MISMATCH" for r in presence),
            }
            agency_check = "ARCHIVE_PARTITION_ONLY" if all(s.get("agency_code_column") is None for s in summaries if s["schema_recognized"]) else "MATCHED_ROWS_CHECKED_AGAINST_097"
            return {"schema_recognized": True, "schema_status": "Q221_DOD_097_ARCHIVE_CSV_SCHEMA_RECOGNIZED",
                    "archive_member_count": len(infos), "csv_member_count": len(csv_infos),
                    "matchable_csv_member_count": compatible, "uncompressed_archive_bytes": expanded,
                    "total_csv_rows_scanned": total_rows, "csv_members": summaries,
                    "row_presence": presence, "presence_counts": counts, "agency_code_validation": agency_check}
    except ProbeError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError, ValueError) as exc:
        raise ProbeError("Q221_DOD_097_ARCHIVE_ZIP_INSPECTION_FAILED", type(exc).__name__) from exc


def _base_receipt() -> dict[str, Any]:
    return {
        "schema_version": 1, "record_type": "q221_dod_097_wayback_archive_presence_probe", "candidate_id": "Q221",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "source_of_truth": "DWR-debug/trading-agent-public",
        "status": "Q221_DOD_097_PROBE_NOT_COMPLETED",
        "frozen_source_manifest": {"path": MANIFEST_PATH, "git_blob_sha1": MANIFEST_BLOB,
                                   "receipt_fingerprint": MANIFEST_FP, "expected_transaction_count": MANIFEST_COUNT},
        "archive_capture": {"filename": ARCHIVE_FILENAME, "original_url": ARCHIVE_URL, "wayback_replay_url": REPLAY_URL,
                            "wayback_capture_timestamp": CAPTURE_TIMESTAMP, "capture_timestamp_utc": CAPTURE_UTC,
                            "cdx_sha1_base32": CDX_SHA1_BASE32, "length_bytes": CDX_LENGTH},
        "source_probe": {"request_cap": MAX_REQUESTS, "request_count": 0, "response_bytes": 0,
                         "response_cap_total_bytes": MAX_TOTAL_BYTES, "responses": [], "transport_errors": []},
        "frozen_row_selection": {"fiscal_year": 2025, "awarding_agency": "Department of Defense",
                                 "agency_exception_class": "DOD_90_DAY_EXCEPTION_CANDIDATE",
                                 "expected_transaction_count": TARGET_COUNT,
                                 "match_fields": ["PIID", "modification", "action_date", "recipient_uei"], "target_keys": []},
        "interpretation": {
            "first_public_observation_time_proven": False, "event_level_public_boundary_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "positive_row_presence_meaning": "Present in this exact archive as captured by Wayback; not first-public time.",
            "negative_row_presence_meaning": "Not found in this exact snapshot only; not evidence of historical absence from another channel.",
            "archive_filename_date_is_not_publication_clock": True, "action_date_and_issued_date_are_not_public_observation_time": True,
            "no_name_similarity_mapping": True,
        },
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "source_requests_made": 0,
                   "source_receipts_modified": False, "source_population_changed": False, "census_restarted": False,
                   "historical_first_public_observation_proven": False, "event_level_public_boundary_proven": False,
                   "recipient_to_issuer_mapping_frozen": False, "scientific_evidence": False, "performance_authorization": False,
                   "holdout_selection": False, "ranking": False, "tuning": False, "promotion": False, "live_execution": False},
        "errors": [],
    }


def _write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    receipt.pop("receipt_fingerprint", None)
    receipt["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    receipt["receipt_fingerprint"] = _fingerprint(receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def run_probe(root: Path, prereg_path: Path | None = None, request_path: Path | None = None,
              output_path: Path | None = None, fetcher: Callable | None = None) -> dict[str, Any]:
    output = output_path or (root / "q221-dod-097-wayback-presence-receipt.json")
    receipt, state = _base_receipt(), {"request_count": 0, "response_bytes": 0, "responses": [], "transport_errors": [], "request_timeout_seconds": 25}
    fetch = fetcher or fetch_wayback_bounded
    try:
        inputs = validate_frozen_inputs(root, prereg_path, request_path)
        state["request_timeout_seconds"] = inputs["request_timeout_seconds"]
        targets = inputs["targets"]
        receipt["frozen_row_selection"]["target_keys"] = [t["transaction_key"] for t in targets]
        receipt["source_probe"].update({
            "request_sequence": inputs["request"]["REQUEST_SEQUENCE"],
            "manifest_blob_sha1_verified": inputs["manifest_blob_sha1"],
            "request_marker_validated": True, "preregistration_validated": True,
            "request_profile": inputs["request_profile"], "one_shot_attempt": inputs["attempt_number"],
            "preregistration_path": inputs["preregistration_path"],
            "request_marker_path": inputs["request_marker_path"],
            "request_timeout_seconds": inputs["request_timeout_seconds"],
        })
        status, cdx, headers = fetch(build_cdx_query_url(), state, MAX_CDX_BYTES)
        rows = parse_cdx_rows(cdx)
        pin = verify_pinned_capture(rows)
        receipt["source_probe"]["cdx_inventory"] = {
            "http_status": status, "content_type": headers.get("content-type", ""),
            "response_sha256": state["responses"][-1]["response_sha256"], "response_bytes": len(cdx),
            "captured_record_count": len(rows), "unique_original_url_count": len({r["original"] for r in rows}),
            "unique_capture_days": sorted({r["timestamp"][:8] for r in rows}),
            "unique_filename_date_stamps": sorted({m.group(1) for r in rows if (m := re.search(r"_(\d{8})\.zip$", r["original"]))}),
            "pinned_target_capture": pin, "pinned_target_verified": True,
            "scope": "bounded CDX prefix inventory; not proof of complete capture history",
        }
        status, archive_body, headers = fetch(REPLAY_URL, state, MAX_ARCHIVE_BYTES)
        digest = base64.b32encode(hashlib.sha1(archive_body).digest()).decode("ascii").rstrip("=")
        if len(archive_body) != CDX_LENGTH:
            raise ProbeError("Q221_DOD_097_ARCHIVE_REPLAY_LENGTH_MISMATCH", "archive bytes differ from CDX")
        if digest != CDX_SHA1_BASE32:
            raise ProbeError("Q221_DOD_097_ARCHIVE_REPLAY_DIGEST_MISMATCH", "SHA-1/Base32 differs from CDX")
        receipt["archive_capture"].update({"replay_http_status": status, "replay_content_type": headers.get("content-type", ""),
                                           "observed_length_bytes": len(archive_body), "observed_sha1_base32": digest,
                                           "observed_sha256": _sha256(archive_body), "cdx_length_match": True,
                                           "cdx_digest_match": True, "archive_body_persisted": False})
        observed = inspect_archive_bytes(archive_body, targets)
        receipt["archive_schema_and_row_presence"] = observed
        if not observed["schema_recognized"]:
            raise ProbeError("Q221_DOD_097_ARCHIVE_CSV_SCHEMA_UNRECOGNIZED", "transaction identifier columns absent")
        if observed["presence_counts"]["agency_code_mismatch"]:
            raise ProbeError("Q221_DOD_097_ARCHIVE_AGENCY_CODE_MISMATCH", "identity matched but agency code contradicted 097")
        receipt["status"] = "Q221_DOD_097_ARCHIVE_SCHEMA_AND_ROW_PRESENCE_INSPECTED_PUBLIC_CLOCK_UNPROVEN"
        receipt["next_gate"] = "Review snapshot evidence; independently obtain transaction-level public version history and pre-event issuer mapping. Do not clear Q221 gates."
    except ProbeError as exc:
        receipt["status"] = exc.status
        receipt["errors"].append({"code": exc.status, "message": exc.message})
        receipt.setdefault("next_gate", "Retain blocker; this one-shot authorizes no retry or archive expansion.")
    except Exception as exc:
        receipt["status"] = "Q221_DOD_097_UNEXPECTED_PROBE_FAILURE"
        receipt["errors"].append({"code": "UNEXPECTED_EXCEPTION", "message": type(exc).__name__})
        receipt.setdefault("next_gate", "Inspect receipt and code; no automatic retry is authorized.")
    finally:
        receipt["source_probe"].update({"request_count": state["request_count"], "response_bytes": state["response_bytes"],
                                        "responses": state["responses"], "transport_errors": state["transport_errors"]})
        receipt["safety"].update({"source_requests_made": state["request_count"], "source_receipts_modified": False,
                                  "source_population_changed": False, "census_restarted": False,
                                  "historical_first_public_observation_proven": False, "event_level_public_boundary_proven": False,
                                  "recipient_to_issuer_mapping_frozen": False, "scientific_evidence": False,
                                  "performance_authorization": False, "holdout_selection": False, "ranking": False,
                                  "tuning": False, "promotion": False, "live_execution": False})
        _write_receipt(output, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--prereg", type=Path, default=None)
    parser.add_argument("--request", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        validated = validate_frozen_inputs(args.repo_root.resolve(), args.prereg, args.request)
    except ProbeError as exc:
        print(json.dumps({"status": exc.status, "message": exc.message, "source_requests_made": 0}, sort_keys=True))
        return 2
    if args.validate_only:
        print(json.dumps({"status": "Q221_DOD_097_FROZEN_INPUTS_VALID",
                          "manifest_blob_sha1": validated["manifest_blob_sha1"],
                          "target_count": len(validated["targets"]), "source_requests_made": 0}, sort_keys=True))
        return 0
    receipt = run_probe(args.repo_root.resolve(), args.prereg, args.request, args.output)
    print(json.dumps(receipt, sort_keys=True, ensure_ascii=False))
    return 0 if receipt["status"] == "Q221_DOD_097_ARCHIVE_SCHEMA_AND_ROW_PRESENCE_INSPECTED_PUBLIC_CLOCK_UNPROVEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
