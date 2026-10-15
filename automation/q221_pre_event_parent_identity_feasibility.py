"""Bounded Q221 pre-event parent-identity source-feasibility audit.

This is a five-document SEC EDGAR audit, not a mapping gate. Four frozen
transactions are checked against pre-event parent subsidiary-list filings. A
fifth case is a post-event successor-name chronology control. No award data is
changed and no issuer mapping is authorized.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

PREREG_PATH = "research/preregistrations/q221_pre_event_parent_identity_feasibility_2026_10_15.json"
BOUNDARY_PATH = "research/evidence/q221_historical_public_boundary_latest.json"
BOUNDARY_FP = "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
BOUNDARY_BLOB_SHA = "b78cf6f7b48af3f914ee7c6d06a38f6485b0438f"
PARENT_MAP_FP = "ae3a3263d5e7d2545dbdaed7ba7ff1cfe3d4cd00e0403352096dcce4d4797602"
PARENT_MAP_RUN_ID = 38305074104
PARENT_MAP_ARTIFACT_ID = 11772786096
PARENT_MAP_ARTIFACT_NAME = "q221-current-parent-identity-map-38305074104-1"
EXPECTED_RECORD_IDS = (
    "CACI_2019_PRE_EVENT",
    "BOOZ_ALLEN_2020_PRE_EVENT",
    "OSI_AS_E_2023_PRE_EVENT",
    "NORTHROP_2024_PRE_EVENT",
    "RTX_SUCCESSOR_NAME_TEMPORAL_CONTROL",
)
MAX_REQUESTS = 5
MAX_BYTES_EACH = 250_000
MAX_TOTAL_BYTES = 1_000_000
TIMEOUT_SECONDS = 30
REQUEST_GAP_SECONDS = 1.0
ALLOWED_HOST = "www.sec.gov"
USER_AGENT = "DWR-debug Trading Agent OS Q221 research; research@example.invalid"


class FeasibilityError(ValueError):
    """A frozen source identity, bounded download, or interpretation contract failed."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_fingerprint(payload: dict[str, Any], field: str = "receipt_fingerprint") -> str:
    value = dict(payload)
    value.pop(field, None)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(raw)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FeasibilityError(f"JSON_INPUT_UNREADABLE:{path.name}:{type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise FeasibilityError(f"JSON_INPUT_NOT_OBJECT:{path.name}")
    return value


def find_one_json(path: Path) -> Path:
    if path.is_file():
        return path
    found = sorted(path.rglob("*.json"))
    if len(found) != 1:
        raise FeasibilityError(f"PINNED_ARTIFACT_JSON_COUNT_INVALID:{len(found)}")
    return found[0]


def text_key(value: str) -> str:
    """ASCII alphanumeric key used only for literal legal-name matching."""
    return re.sub(r"[^A-Z0-9]", "", html.unescape(value).upper())


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)


def visible_text(raw: bytes) -> str:
    parser = VisibleText()
    parser.feed(raw.decode("utf-8", errors="replace"))
    return " ".join(parser.parts)


def validate_preregistration(prereg: dict[str, Any], prereg_path: Path) -> None:
    if prereg.get("record_type") != "q221_pre_event_parent_identity_feasibility_preregistration":
        raise FeasibilityError("PREREG_RECORD_TYPE_MISMATCH")
    if prereg.get("candidate_id") != "Q221" or prereg.get("study_mode") != "BOUNDED_SOURCE_FEASIBILITY_DESK_AUDIT":
        raise FeasibilityError("PREREG_IDENTITY_MISMATCH")
    if len(prereg.get("records", [])) != len(EXPECTED_RECORD_IDS):
        raise FeasibilityError("PREREG_RECORD_COUNT_MISMATCH")
    if tuple(str(row.get("record_id")) for row in prereg["records"]) != EXPECTED_RECORD_IDS:
        raise FeasibilityError("PREREG_RECORD_ORDER_OR_ID_MISMATCH")
    limits = prereg.get("execution_limits", {})
    expected_limits = {
        "maximum_sec_requests": MAX_REQUESTS,
        "requests_per_fixed_url": 1,
        "automatic_retries": False,
        "maximum_response_bytes_each": MAX_BYTES_EACH,
        "maximum_aggregate_response_bytes": MAX_TOTAL_BYTES,
        "request_timeout_seconds": TIMEOUT_SECONDS,
        "minimum_gap_between_requests_seconds": REQUEST_GAP_SECONDS,
        "source_domain_allowlist": [ALLOWED_HOST],
        "paid_data_budget_usd": 0,
        "no_other_network_fetches": True,
    }
    for key, expected in expected_limits.items():
        if limits.get(key) != expected:
            raise FeasibilityError(f"PREREG_LIMIT_DRIFT:{key}")
    if prereg_path.name != Path(PREREG_PATH).name:
        raise FeasibilityError("PREREG_PATH_NAME_MISMATCH")
    for spec in prereg["records"]:
        parsed = urlparse(str(spec.get("document_url") or ""))
        if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
            raise FeasibilityError("PREREG_SOURCE_URL_OUTSIDE_ALLOWLIST:" + str(spec.get("record_id")))
        path_parts = parsed.path.split("/Archives/edgar/data/", 1)
        if len(path_parts) != 2:
            raise FeasibilityError("PREREG_SOURCE_URL_NOT_EDGAR_ARCHIVE:" + str(spec.get("record_id")))
        path_cik = path_parts[1].split("/", 1)[0].zfill(10)
        if path_cik != str(spec.get("filing_filer_cik") or ""):
            raise FeasibilityError("PREREG_URL_FILER_CIK_MISMATCH:" + str(spec.get("record_id")))
        if spec.get("role") == "pre_event_parent_subsidiary_list":
            if spec.get("expected_parent_cik") != spec.get("filing_filer_cik"):
                raise FeasibilityError("PREREG_PARENT_AND_FILER_CIK_MISMATCH:" + str(spec.get("record_id")))
        elif spec.get("role") == "post_event_successor_name_control":
            if spec.get("expected_parent_cik") is not None:
                raise FeasibilityError("TEMPORAL_CONTROL_MUST_NOT_CLAIM_PARENT_CIK")
        else:
            raise FeasibilityError("PREREG_ROLE_UNKNOWN:" + str(spec.get("record_id")))
        try:
            event_date = datetime.fromisoformat(str(spec.get("transaction_date")))
            filing_date = datetime.fromisoformat(str(spec.get("filing_date")))
        except ValueError as exc:
            raise FeasibilityError("PREREG_DATE_INVALID:" + str(spec.get("record_id"))) from exc
        if spec.get("role") == "pre_event_parent_subsidiary_list" and not filing_date.date() < event_date.date():
            raise FeasibilityError("PREREG_PARENT_FILING_DATE_NOT_PRE_EVENT:" + str(spec.get("record_id")))
        if spec.get("role") == "post_event_successor_name_control" and not filing_date.date() > event_date.date():
            raise FeasibilityError("PREREG_TEMPORAL_CONTROL_DATE_NOT_POST_EVENT:" + str(spec.get("record_id")))
    safety = prereg.get("safety", {})
    if safety != {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "paid_api_budget_usd": 0,
    }:
        raise FeasibilityError("PREREG_SAFETY_CONTRACT_MISMATCH")
    for k, expected in (
        ("historical_parent_lineage_proven", False),
        ("historical_first_public_observation_proven", False),
        ("recipient_to_issuer_mapping_frozen", False),
        ("q221_gate_positive", False),
        ("performance_authorization", False),
        ("promotion", False),
        ("live_execution", False),
    ):
        if prereg.get("required_assertions", {}).get(k) is not expected:
            raise FeasibilityError(f"PREREG_AUTHORITY_CONTRACT_MISMATCH:{k}")


def validate_frozen_inputs(
    repo_root: Path,
    parent_map_artifact_dir: Path,
    prereg: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    boundary_path = repo_root / BOUNDARY_PATH
    raw_boundary = boundary_path.read_bytes()
    if sha256(raw_boundary) == "":
        raise FeasibilityError("UNREACHABLE_EMPTY_BOUNDARY_HASH")
    boundary = json.loads(raw_boundary.decode("utf-8"))
    if not isinstance(boundary, dict):
        raise FeasibilityError("BOUNDARY_NOT_OBJECT")
    if boundary.get("receipt_fingerprint") != BOUNDARY_FP or canonical_fingerprint(boundary) != BOUNDARY_FP:
        raise FeasibilityError("BOUNDARY_RECEIPT_FINGERPRINT_MISMATCH")
    if len(boundary.get("transactions", [])) != 348:
        raise FeasibilityError("BOUNDARY_TRANSACTION_COUNT_MISMATCH")

    parent_map_path = find_one_json(parent_map_artifact_dir)
    parent_map = read_json(parent_map_path)
    if parent_map.get("record_type") != "q221_current_parent_identity_lead_map":
        raise FeasibilityError("PARENT_MAP_RECORD_TYPE_MISMATCH")
    if parent_map.get("receipt_fingerprint") != PARENT_MAP_FP or canonical_fingerprint(parent_map) != PARENT_MAP_FP:
        raise FeasibilityError("PARENT_MAP_RECEIPT_FINGERPRINT_MISMATCH")
    if parent_map.get("source_receipt_fingerprint") != BOUNDARY_FP:
        raise FeasibilityError("PARENT_MAP_BOUNDARY_UPSTREAM_MISMATCH")
    if parent_map.get("verified_profile_count") != 247 or len(parent_map.get("recipients", [])) != 247:
        raise FeasibilityError("PARENT_MAP_PROFILE_COUNT_MISMATCH")
    if parent_map.get("historical_parent_lineage_proven") is not False:
        raise FeasibilityError("PARENT_MAP_AUTHORITY_DRIFT")
    if parent_map.get("recipient_to_issuer_mapping_frozen") is not False:
        raise FeasibilityError("PARENT_MAP_MAPPING_ALREADY_AUTHORIZED")

    expected_upstream = prereg.get("frozen_population", {})
    if (
        expected_upstream.get("receipt_fingerprint") != BOUNDARY_FP
        or expected_upstream.get("git_blob_sha1") != BOUNDARY_BLOB_SHA
        or expected_upstream.get("source_map_receipt_fingerprint") != PARENT_MAP_FP
        or expected_upstream.get("source_map_run_id") != PARENT_MAP_RUN_ID
        or expected_upstream.get("source_map_artifact_id") != PARENT_MAP_ARTIFACT_ID
    ):
        raise FeasibilityError("PREREG_FROZEN_UPSTREAM_MISMATCH")

    boundary_by_key = {str(row.get("transaction_key")): row for row in boundary.get("transactions", [])}
    profile_by_uei = {str(row.get("recipient_uei")): row for row in parent_map.get("recipients", [])}
    for spec in prereg["records"]:
        tx = boundary_by_key.get(spec["transaction_key"])
        if tx is None:
            raise FeasibilityError("FROZEN_TRANSACTION_KEY_MISSING:" + spec["record_id"])
        for key in ("transaction_date", "recipient_name", "recipient_uei", "recipient_id"):
            source_key = "action_date" if key == "transaction_date" else key
            if str(tx.get(source_key) or "") != str(spec.get(key) or ""):
                raise FeasibilityError(f"FROZEN_BOUNDARY_FIELD_MISMATCH:{spec['record_id']}:{key}")
        if tx.get("recipient_to_issuer_status") != spec.get("recipient_to_issuer_status") or tx.get("recipient_to_issuer_status") != "UNMAPPED_NO_FROZEN_PRE_EVENT_IDENTITY_RECEIPT":
            raise FeasibilityError("FROZEN_ROW_MAPPING_STATUS_DRIFT:" + spec["record_id"])
        if tx.get("issuer_symbol") != spec.get("issuer_symbol") or tx.get("mapping_authority") != spec.get("mapping_authority"):
            raise FeasibilityError("FROZEN_ROW_MAPPING_AUTHORITY_DRIFT:" + spec["record_id"])

        map_row = profile_by_uei.get(str(spec["recipient_uei"]))
        if map_row is None:
            raise FeasibilityError("CURRENT_PARENT_ROW_MISSING:" + spec["record_id"])
        profile = map_row.get("current_profile_observation", {}).get("profile", {})
        for key, expected in (
            ("recipient_id", spec["recipient_id"]),
            ("parent_name", spec["current_parent_name"]),
            ("parent_uei", spec["current_parent_uei"]),
        ):
            if str(profile.get(key) or "") != str(expected):
                raise FeasibilityError(f"CURRENT_PARENT_PROFILE_PIN_MISMATCH:{spec['record_id']}:{key}")
        if map_row.get("current_parent_classification") != "CURRENT_PARENT_ENTITY_LEAD":
            raise FeasibilityError("CURRENT_PARENT_CLASSIFICATION_MISMATCH:" + spec["record_id"])
        if map_row.get("recipient_to_issuer_mapping_frozen") is not False:
            raise FeasibilityError("CURRENT_PARENT_MAP_ROW_AUTHORITY_DRIFT:" + spec["record_id"])
    return boundary, parent_map, {
        "boundary_path": BOUNDARY_PATH,
        "boundary_blob_sha1": BOUNDARY_BLOB_SHA,
        "boundary_receipt_fingerprint": BOUNDARY_FP,
        "parent_map_run_id": PARENT_MAP_RUN_ID,
        "parent_map_artifact_id": PARENT_MAP_ARTIFACT_ID,
        "parent_map_artifact_name": PARENT_MAP_ARTIFACT_NAME,
        "parent_map_receipt_fingerprint": PARENT_MAP_FP,
        "preregistration_path": PREREG_PATH,
        "preregistration_sha256": sha256((repo_root / PREREG_PATH).read_bytes()),
    }


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Treat redirects as source failures so no unpinned URL is ever requested."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _read_one_source(spec: dict[str, Any], source_dir: Path, aggregate_before: int) -> tuple[dict[str, Any], int]:
    url = str(spec.get("document_url") or "")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
        raise FeasibilityError("SOURCE_URL_OUTSIDE_ALLOWLIST:" + str(spec.get("record_id")))
    remaining = MAX_TOTAL_BYTES - aggregate_before
    if remaining <= 0:
        raise FeasibilityError("SEC_SOURCE_AGGREGATE_BUDGET_EXHAUSTED_BEFORE_REQUEST")
    read_limit = min(MAX_BYTES_EACH, remaining)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
    )
    opener = urllib.request.build_opener(NoRedirectHandler())
    try:
        with opener.open(req, timeout=TIMEOUT_SECONDS) as response:
            status = int(response.status)
            final_url = str(response.geturl())
            headers = response.headers
            content_length_header = headers.get("Content-Length")
            declared_length = int(content_length_header) if content_length_header and content_length_header.isdigit() else None
            if declared_length is not None and declared_length > read_limit:
                raise FeasibilityError(f"SEC_SOURCE_DECLARED_BYTES_EXCEED_REMAINING_BUDGET:{spec['record_id']}:{declared_length}:{read_limit}")
            body = response.read(read_limit)
            # If length is unknown and we consumed the whole allowance, we cannot
            # distinguish an exact-size document from a truncated one without an
            # extra byte read, which would violate the aggregate budget. Fail closed.
            if len(body) == read_limit and declared_length is None:
                raise FeasibilityError(f"SEC_SOURCE_LENGTH_UNKNOWN_AT_HARD_LIMIT:{spec['record_id']}:{read_limit}")
            if declared_length is not None and len(body) != declared_length:
                raise FeasibilityError(f"SEC_SOURCE_CONTENT_LENGTH_MISMATCH:{spec['record_id']}:{len(body)}:{declared_length}")
    except FeasibilityError:
        raise
    except Exception as exc:
        raise FeasibilityError(f"SEC_SOURCE_FETCH_FAILED:{spec['record_id']}:{type(exc).__name__}") from exc
    if status != 200:
        raise FeasibilityError(f"SEC_SOURCE_HTTP_STATUS_INVALID:{spec['record_id']}:{status}")
    if final_url != url:
        raise FeasibilityError(f"SEC_SOURCE_FINAL_URL_MISMATCH:{spec['record_id']}")
    if len(body) == 0 or len(body) > MAX_BYTES_EACH:
        raise FeasibilityError(f"SEC_SOURCE_RESPONSE_BYTES_INVALID:{spec['record_id']}:{len(body)}")
    total = aggregate_before + len(body)
    if total > MAX_TOTAL_BYTES:
        raise FeasibilityError(f"SEC_SOURCE_AGGREGATE_BUDGET_EXCEEDED:{total}")
    content_type = str(headers.get("Content-Type") or "")
    if "html" not in content_type.lower():
        raise FeasibilityError(f"SEC_SOURCE_CONTENT_TYPE_INVALID:{spec['record_id']}:{content_type[:80]}")
    meta = {
        "record_id": spec["record_id"],
        "requested_url": url,
        "final_url": final_url,
        "http_status": status,
        "content_type": content_type,
        "content_length_header": headers.get("Content-Length"),
        "last_modified_header": headers.get("Last-Modified"),
        "etag_header": headers.get("ETag"),
        "response_bytes": len(body),
        "response_sha256": sha256(body),
        "file_name": str(spec["record_id"]) + ".html",
    }
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / meta["file_name"]).write_bytes(body)
    (source_dir / (str(spec["record_id"]) + ".meta.json")).write_text(
        json.dumps(meta, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return meta, total


def fetch_sources(prereg: dict[str, Any], source_dir: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"attempted_request_count": 0, "source_download_bytes": 0, "sources": []}
    last_index = -1
    for index, spec in enumerate(prereg["records"]):
        if index > 0:
            time.sleep(REQUEST_GAP_SECONDS)
        result["attempted_request_count"] += 1
        meta, total = _read_one_source(spec, source_dir, int(result["source_download_bytes"]))
        result["source_download_bytes"] = total
        result["sources"].append(meta)
        last_index = index
    if result["attempted_request_count"] != MAX_REQUESTS or last_index != MAX_REQUESTS - 1:
        raise FeasibilityError("SEC_SOURCE_REQUEST_COUNT_CONTRACT_MISMATCH")
    return result


def read_downloaded_sources(prereg: dict[str, Any], source_dir: Path) -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    total = 0
    allowed_files = set()
    for spec in prereg["records"]:
        stem = str(spec["record_id"])
        body_path = source_dir / (stem + ".html")
        meta_path = source_dir / (stem + ".meta.json")
        allowed_files.update({body_path.name, meta_path.name})
        if not body_path.is_file() or not meta_path.is_file():
            raise FeasibilityError("PINNED_SEC_SOURCE_FILE_MISSING:" + stem)
        meta = read_json(meta_path)
        body = body_path.read_bytes()
        if meta.get("record_id") != stem or meta.get("requested_url") != spec["document_url"]:
            raise FeasibilityError("SEC_SOURCE_META_IDENTITY_MISMATCH:" + stem)
        if meta.get("http_status") != 200 or meta.get("final_url") != spec["document_url"]:
            raise FeasibilityError("SEC_SOURCE_META_STATUS_OR_URL_MISMATCH:" + stem)
        if meta.get("response_bytes") != len(body) or meta.get("response_sha256") != sha256(body):
            raise FeasibilityError("SEC_SOURCE_BODY_HASH_OR_SIZE_MISMATCH:" + stem)
        if len(body) == 0 or len(body) > MAX_BYTES_EACH:
            raise FeasibilityError("SEC_SOURCE_BODY_SIZE_LIMIT_INVALID:" + stem)
        if "html" not in str(meta.get("content_type", "")).lower():
            raise FeasibilityError("SEC_SOURCE_BODY_CONTENT_TYPE_INVALID:" + stem)
        total += len(body)
        sources.append(meta)
    existing = {p.name for p in source_dir.iterdir() if p.is_file()}
    if existing != allowed_files:
        raise FeasibilityError("SEC_SOURCE_DIR_FILE_SET_MISMATCH")
    if total > MAX_TOTAL_BYTES:
        raise FeasibilityError("SEC_SOURCE_AGGREGATE_BUDGET_EXCEEDED")
    return {"attempted_request_count": MAX_REQUESTS, "source_download_bytes": total, "sources": sources}


def build_analysis(
    prereg: dict[str, Any],
    frozen_inputs: dict[str, Any],
    source_dir: Path,
) -> dict[str, Any]:
    acquired = read_downloaded_sources(prereg, source_dir)
    source_by_id = {str(row["record_id"]): row for row in acquired["sources"]}
    analyses: list[dict[str, Any]] = []
    positive_rows = 0
    temporal_controls = 0
    for spec in prereg["records"]:
        src = source_by_id[str(spec["record_id"])]
        body = (source_dir / src["file_name"]).read_bytes()
        visible = visible_text(body)
        normalized = text_key(visible)
        source_date = str(spec["filing_date"])
        event_date = str(spec["transaction_date"])
        source_meta = {
            "document_url": src["requested_url"],
            "filing_index_url": spec.get("filing_index_url"),
            "accession": spec.get("accession"),
            "expected_parent_cik": spec.get("expected_parent_cik"),
        "filing_filer_cik": spec.get("filing_filer_cik"),
            "declared_filing_date": source_date,
            "document_sha256": src["response_sha256"],
            "document_bytes": src["response_bytes"],
            "content_type": src["content_type"],
            "http_status": src["http_status"],
            "last_modified_header": src.get("last_modified_header"),
            "etag_header": src.get("etag_header"),
        }
        if spec["role"] == "pre_event_parent_subsidiary_list":
            if not source_date < event_date:
                raise FeasibilityError("PARENT_FILING_NOT_STRICTLY_PRE_EVENT:" + spec["record_id"])
            child_key = text_key(str(spec["required_child_legal_name"]))
            if not child_key or child_key not in normalized:
                raise FeasibilityError("PRE_EVENT_PARENT_EXHIBIT_CHILD_NAME_NOT_FOUND:" + spec["record_id"])
            if len(str(spec.get("expected_parent_cik") or "").strip()) != 10:
                raise FeasibilityError("PARENT_CIK_NOT_FROZEN:" + spec["record_id"])
            positive_rows += 1
            analyses.append({
                "record_id": spec["record_id"],
                "role": spec["role"],
                "transaction_key": spec["transaction_key"],
                "transaction_date": event_date,
                "recipient_name": spec["recipient_name"],
                "recipient_uei": spec["recipient_uei"],
                "recipient_id": spec["recipient_id"],
                "recipient_to_issuer_status": spec["recipient_to_issuer_status"],
                "issuer_symbol": spec["issuer_symbol"],
                "mapping_authority": spec["mapping_authority"],
                "current_parent_name": spec["current_parent_name"],
                "current_parent_uei": spec["current_parent_uei"],
                "pre_event_parent_filing_contains_child": True,
                "matched_child_legal_name": spec["required_child_legal_name"],
                "child_identifier_bridge_to_frozen_uei_proven": False,
                "parent_relation_as_of_transaction_date_proven": False,
                "recipient_to_issuer_mapping_frozen": False,
                "historical_first_public_observation_proven": False,
                "mapping_authority": None,
                "source": source_meta,
                "classification": "PRE_EVENT_PARENT_REPORT_NAMES_CHILD_LEGAL_ENTITY",
            })
        else:
            if not source_date > event_date:
                raise FeasibilityError("TEMPORAL_CONTROL_NOT_POST_EVENT:" + spec["record_id"])
            missing = [marker for marker in spec["required_markers"] if text_key(marker) not in normalized]
            if missing:
                raise FeasibilityError("TEMPORAL_CONTROL_REQUIRED_MARKER_MISSING:" + spec["record_id"] + ":" + "|".join(missing))
            temporal_controls += 1
            analyses.append({
                "record_id": spec["record_id"],
                "role": spec["role"],
                "transaction_key": spec["transaction_key"],
                "transaction_date": event_date,
                "recipient_name": spec["recipient_name"],
                "recipient_uei": spec["recipient_uei"],
                "recipient_id": spec["recipient_id"],
                "recipient_to_issuer_status": spec["recipient_to_issuer_status"],
                "issuer_symbol": spec["issuer_symbol"],
                "mapping_authority": spec["mapping_authority"],
                "current_parent_name": spec["current_parent_name"],
                "current_parent_uei": spec["current_parent_uei"],
                "control_filing_date": source_date,
                "successor_name_event_date": "2020-04-03",
                "successor_name_event_postdates_transaction": True,
                "pre_event_parent_filing_contains_child": False,
                "child_identifier_bridge_to_frozen_uei_proven": False,
                "parent_relation_as_of_transaction_date_proven": False,
                "recipient_to_issuer_mapping_frozen": False,
                "historical_first_public_observation_proven": False,
                "mapping_authority": None,
                "source": source_meta,
                "classification": "CURRENT_PARENT_SUCCESSOR_NAME_POSTDATES_TRANSACTION_NOT_HISTORICAL_PROOF",
            })

    if positive_rows != 4 or temporal_controls != 1 or len(analyses) != MAX_REQUESTS:
        raise FeasibilityError("ANALYSIS_SAMPLE_COUNTS_INVALID")

    core = {
        "schema_version": 1,
        "record_type": "q221_pre_event_parent_identity_feasibility",
        "candidate_id": "Q221",
        "status": "Q221_PRE_EVENT_PARENT_SOURCE_FEASIBILITY_COMPLETE_LINEAGE_UNRESOLVED",
        "preregistration_path": PREREG_PATH,
        "preregistration_sha256": frozen_inputs["preregistration_sha256"],
        "frozen_inputs": frozen_inputs,
        "source_fetch": {
            "fixed_request_count": MAX_REQUESTS,
            "attempted_request_count": acquired["attempted_request_count"],
            "source_download_bytes": acquired["source_download_bytes"],
            "max_bytes_each": MAX_BYTES_EACH,
            "max_aggregate_bytes": MAX_TOTAL_BYTES,
            "requests_retried": False,
            "only_sec_domain_used": True,
        },
        "sample_counts": {
            "pre_event_parent_exhibit_cases": positive_rows,
            "post_event_successor_name_controls": temporal_controls,
            "total_frozen_cases": len(analyses),
        },
        "observations": analyses,
        "interpretation": {
            "four_parent_filings_name_exact_child_legal_entity": True,
            "finding_scope": "fixed purposeful source-feasibility sample only",
            "not_a_random_or_prevalence_sample": True,
            "historical_parent_lineage_proven": False,
            "parent_relation_as_of_transaction_date_proven": False,
            "child_identifier_bridge_to_frozen_uei_proven": False,
            "historical_first_public_observation_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "current_profile_alone_is_historical_evidence": False,
            "q221_gate_positive": False,
            "scientific_evidence": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
        "next_gate": (
            "Find an independent contemporaneous identifier bridge connecting each frozen UEI/recipient_id to the legal entity; "
            "a parent filing that names a child does not prove that the contract row's UEI identified that child as of the transaction date."
        ),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "paid_api_budget_usd": 0,
        },
    }
    core["analysis_fingerprint"] = sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    )
    return core


def run(
    repo_root: Path,
    parent_map_artifact: Path,
    source_dir: Path,
    output_path: Path,
    *,
    fetch: bool = False,
    expected_analysis_fingerprint: str | None = None,
) -> dict[str, Any]:
    prereg_path = repo_root / PREREG_PATH
    prereg = read_json(prereg_path)
    validate_preregistration(prereg, prereg_path)
    boundary, parent_map, frozen_inputs = validate_frozen_inputs(repo_root, parent_map_artifact, prereg)
    if fetch:
        try:
            fetch_meta = fetch_sources(prereg, source_dir)
        except Exception as exc:
            fail = {
                "schema_version": 1,
                "record_type": "q221_pre_event_parent_identity_feasibility",
                "candidate_id": "Q221",
                "status": "Q221_PRE_EVENT_SOURCE_FETCH_INCOMPLETE",
                "error": f"{type(exc).__name__}:{str(exc)}"[:700],
                "gate_positive": False,
                "historical_parent_lineage_proven": False,
                "recipient_to_issuer_mapping_frozen": False,
                "safety": {
                    "paper_only": True,
                    "live_trading_enabled": False,
                    "orders_enabled": False,
                    "automatic_promotion": False,
                    "paid_api_budget_usd": 0,
                },
            }
            fail["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
            fail["receipt_fingerprint"] = canonical_fingerprint(fail)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(fail, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return fail
    core = build_analysis(prereg, frozen_inputs, source_dir)
    if expected_analysis_fingerprint and core["analysis_fingerprint"] != expected_analysis_fingerprint:
        raise FeasibilityError("CROSS_ARCH_ANALYSIS_FINGERPRINT_MISMATCH")
    result = {**core, "generated_at_utc": datetime.now(timezone.utc).isoformat()}
    result["receipt_fingerprint"] = canonical_fingerprint(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "analysis_fingerprint": result["analysis_fingerprint"],
        "receipt_fingerprint": result["receipt_fingerprint"],
        "parent_exhibit_hits": result["sample_counts"]["pre_event_parent_exhibit_cases"],
        "mapping_frozen": result["interpretation"]["recipient_to_issuer_mapping_frozen"],
        "source_download_bytes": result["source_fetch"]["source_download_bytes"],
    }, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--parent-map-artifact", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fetch-sources", action="store_true")
    parser.add_argument("--expected-analysis-fingerprint", default=None)
    args = parser.parse_args()
    result = run(
        args.repo_root,
        args.parent_map_artifact,
        args.source_dir,
        args.output,
        fetch=args.fetch_sources,
        expected_analysis_fingerprint=args.expected_analysis_fingerprint,
    )
    return 0 if result.get("status") == "Q221_PRE_EVENT_PARENT_SOURCE_FEASIBILITY_COMPLETE_LINEAGE_UNRESOLVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
