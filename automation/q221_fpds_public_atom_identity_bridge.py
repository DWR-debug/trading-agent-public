"""Bounded public FPDS Atom identity-bridge probe for four frozen Q221 records.

Only one PIID-scoped public-feed request is made per preregistered record. Redirects
are blocked, retries are prohibited, and response bodies are parsed in memory and
never persisted. This is diagnostic-only; it cannot prove the complete Q221 gate.
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
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REQUEST_PATH = "research/run_requests/q221_fpds_public_atom_identity_bridge.trigger"
PREREG_PATH = "research/preregistrations/q221_fpds_public_atom_identity_bridge_2026_10_15.json"
BOUNDARY_PATH = "research/evidence/q221_historical_public_boundary_latest.json"
PRE_EVENT_PATH = "research/evidence/q221_pre_event_parent_identity_feasibility_latest.json"
BOUNDARY_BLOB_SHA1 = "b78cf6f7b48af3f914ee7c6d06a38f6485b0438f"
BOUNDARY_FP = "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
PRE_EVENT_FP = "7b969cc7dd0a5c5e94050c9e99b797e59b77d20712e51661b1b281fb170dd953"
ENDPOINT = "https://www.fpds.gov/dbsight/FEEDS/ATOM"
ALLOWED_HOST = "www.fpds.gov"
FEEDNAME = "PUBLIC"
MAX_REQUESTS = 4
MAX_RESPONSE_BYTES_EACH = 1_000_000
MAX_TOTAL_RESPONSE_BYTES = 4_000_000
MAX_ATOM_ENTRIES_EACH = 250
TIMEOUT_SECONDS = 25
REQUEST_GAP_SECONDS = 1.0
TRANSITION_DATE = "2022-04-04"

FROZEN_REQUEST_VALUES = {
    "RUN_Q221_FPDS_PUBLIC_ATOM_IDENTITY_BRIDGE": "true",
    "REASON": "BOUNDED_PUBLIC_FPDS_IDENTITY_BRIDGE_FEASIBILITY_FOR_FOUR_FROZEN_Q221_TRANSACTIONS",
    "SOURCE_MANIFEST_PATH": BOUNDARY_PATH,
    "SOURCE_MANIFEST_GIT_BLOB_SHA": BOUNDARY_BLOB_SHA1,
    "SOURCE_MANIFEST_RECEIPT_FINGERPRINT": BOUNDARY_FP,
    "PRE_EVENT_RECEIPT_PATH": PRE_EVENT_PATH,
    "PRE_EVENT_RECEIPT_FINGERPRINT": PRE_EVENT_FP,
    "TARGET_RECORD_COUNT": str(MAX_REQUESTS),
    "FPDS_PUBLIC_ENDPOINT": ENDPOINT,
    "FEEDNAME": FEEDNAME,
    "MAX_RESPONSE_BYTES_EACH": str(MAX_RESPONSE_BYTES_EACH),
    "MAX_TOTAL_RESPONSE_BYTES": str(MAX_TOTAL_RESPONSE_BYTES),
    "MAX_ATOM_ENTRIES_EACH": str(MAX_ATOM_ENTRIES_EACH),
    "REQUEST_TIMEOUT_SECONDS": str(TIMEOUT_SECONDS),
    "REQUEST_GAP_SECONDS": "1",
    "RETRIES": "0",
    "FOLLOW_REDIRECTS": "false",
    "NO_SAM_API_REQUESTS": "true",
    "NO_NEW_USASPENDING_REQUESTS": "true",
    "NO_SEC_REQUESTS": "true",
    "NO_ARCHIVE_DOWNLOADS": "true",
    "NO_SOURCE_ROW_OR_HASH_CHANGES": "true",
    "PAPER_ONLY": "true",
    "LIVE_TRADING_ENABLED": "false",
    "ORDERS_ENABLED": "false",
    "AUTOMATIC_PROMOTION": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}
REQUEST_KEYS = set(FROZEN_REQUEST_VALUES) | {"REQUEST_SEQUENCE"}

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
    },
)


class BridgeError(ValueError):
    """A frozen input, response boundary, or diagnostic contract is invalid."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def canonical_fingerprint(value: dict[str, Any], field: str = "receipt_fingerprint") -> str:
    payload = dict(value)
    payload.pop(field, None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(raw)


def canonical_analysis_fingerprint(value: dict[str, Any]) -> str:
    payload = dict(value)
    for key in ("analysis_fingerprint", "receipt_fingerprint", "generated_at_utc", "workflow_run_id"):
        payload.pop(key, None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(raw)


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw or raw.strip() != raw or "=" not in raw:
            raise BridgeError(f"Q221_FPDS_REQUEST_INVALID_LINE:{number}")
        key, value = raw.split("=", 1)
        if not key or not value or key in values:
            raise BridgeError(f"Q221_FPDS_REQUEST_INVALID_KEY_VALUE:{number}")
        values[key] = value
    if set(values) != REQUEST_KEYS:
        raise BridgeError("Q221_FPDS_REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN_REQUEST_VALUES.items():
        if values[key] != expected:
            raise BridgeError("Q221_FPDS_REQUEST_VALUE_MISMATCH:" + key)
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values["REQUEST_SEQUENCE"]):
        raise BridgeError("Q221_FPDS_REQUEST_SEQUENCE_INVALID")
    datetime.fromisoformat(values["REQUEST_SEQUENCE"].replace("Z", "+00:00"))
    return values


def validate_frozen_inputs(repo_root: Path, request: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    boundary_raw = (repo_root / BOUNDARY_PATH).read_bytes()
    if git_blob_sha1(boundary_raw) != BOUNDARY_BLOB_SHA1:
        raise BridgeError("Q221_FPDS_BOUNDARY_GIT_BLOB_SHA_MISMATCH")
    boundary = json.loads(boundary_raw.decode("utf-8"))
    if not isinstance(boundary, dict) or boundary.get("receipt_fingerprint") != BOUNDARY_FP:
        raise BridgeError("Q221_FPDS_BOUNDARY_RECEIPT_FINGERPRINT_MISMATCH")
    if canonical_fingerprint(boundary) != BOUNDARY_FP:
        raise BridgeError("Q221_FPDS_BOUNDARY_CANONICAL_FINGERPRINT_MISMATCH")
    if boundary.get("candidate_id") != "Q221" or boundary.get("historical_first_public_observation_proven") is not False:
        raise BridgeError("Q221_FPDS_BOUNDARY_GATE_STATE_CHANGED")
    boundary_by_key = {str(row.get("transaction_key")): row for row in boundary.get("transactions", [])}
    if len(boundary.get("transactions", [])) != 348:
        raise BridgeError("Q221_FPDS_BOUNDARY_ROW_COUNT_MISMATCH")

    prereg = json.loads((repo_root / PREREG_PATH).read_text(encoding="utf-8"))
    if not isinstance(prereg, dict) or prereg.get("record_type") != "q221_fpds_public_atom_identity_bridge_preregistration":
        raise BridgeError("Q221_FPDS_PREREG_RECORD_TYPE_MISMATCH")
    if prereg.get("candidate_id") != "Q221" or prereg.get("study_mode") != "BOUNDED_PUBLIC_SOURCE_FEASIBILITY":
        raise BridgeError("Q221_FPDS_PREREG_IDENTITY_MISMATCH")
    if prereg.get("frozen_inputs", {}).get("boundary_receipt_fingerprint") != BOUNDARY_FP:
        raise BridgeError("Q221_FPDS_PREREG_BOUNDARY_MISMATCH")
    if prereg.get("frozen_inputs", {}).get("pre_event_feasibility_receipt_fingerprint") != PRE_EVENT_FP:
        raise BridgeError("Q221_FPDS_PREREG_PRE_EVENT_FP_MISMATCH")
    if request.get("REQUEST_SEQUENCE") != prereg.get("preregistered_at_utc"):
        raise BridgeError("Q221_FPDS_REQUEST_SEQUENCE_DIFFERS_FROM_PREREGISTRATION")
    limits = prereg.get("execution_limits", {})
    expected_limits = {
        "exact_record_queries": MAX_REQUESTS,
        "requests_per_fixed_piid": 1,
        "automatic_retries": 0,
        "follow_redirects": False,
        "max_response_bytes_each": MAX_RESPONSE_BYTES_EACH,
        "max_total_response_bytes": MAX_TOTAL_RESPONSE_BYTES,
        "max_atom_entries_each": MAX_ATOM_ENTRIES_EACH,
        "request_timeout_seconds": TIMEOUT_SECONDS,
        "minimum_gap_between_requests_seconds": REQUEST_GAP_SECONDS,
        "allowed_initial_host": ALLOWED_HOST,
        "no_sam_api_requests": True,
        "no_new_usaspending_requests": True,
        "no_sec_requests": True,
        "no_archive_downloads": True,
        "no_source_row_or_hash_changes": True,
        "paid_data_budget_usd": 0,
    }
    for key, expected in expected_limits.items():
        if limits.get(key) != expected:
            raise BridgeError("Q221_FPDS_PREREG_LIMIT_MISMATCH:" + key)
    records = prereg.get("records")
    if not isinstance(records, list) or len(records) != MAX_REQUESTS:
        raise BridgeError("Q221_FPDS_PREREG_RECORD_COUNT_MISMATCH")
    if [x.get("record_id") for x in records] != [x["record_id"] for x in EXPECTED_RECORDS]:
        raise BridgeError("Q221_FPDS_PREREG_RECORD_ORDER_MISMATCH")
    for expected, spec in zip(EXPECTED_RECORDS, records):
        for key in ("transaction_key", "piid", "modification_number", "action_date", "recipient_uei", "recipient_id", "accepted_legal_names", "pre_event_accession", "identifier_regime_at_action"):
            if spec.get(key) != expected[key]:
                raise BridgeError(f"Q221_FPDS_PREREG_RECORD_PIN_MISMATCH:{expected['record_id']}:{key}")
        tx = boundary_by_key.get(expected["transaction_key"])
        if not isinstance(tx, dict):
            raise BridgeError("Q221_FPDS_FROZEN_TRANSACTION_MISSING:" + expected["record_id"])
        for field, want in (("action_date", expected["action_date"]), ("recipient_uei", expected["recipient_uei"]), ("recipient_id", expected["recipient_id"])):
            if str(tx.get(field) or "") != want:
                raise BridgeError(f"Q221_FPDS_BOUNDARY_ROW_PIN_MISMATCH:{expected['record_id']}:{field}")
        if tx.get("recipient_to_issuer_status") != "UNMAPPED_NO_FROZEN_PRE_EVENT_IDENTITY_RECEIPT":
            raise BridgeError("Q221_FPDS_UPSTREAM_MAPPING_STATUS_CHANGED:" + expected["record_id"])

    pre_event = json.loads((repo_root / PRE_EVENT_PATH).read_text(encoding="utf-8"))
    if (
        not isinstance(pre_event, dict)
        or pre_event.get("record_type") != "q221_pre_event_parent_identity_feasibility"
        or pre_event.get("receipt_fingerprint") != PRE_EVENT_FP
        or canonical_fingerprint(pre_event) != PRE_EVENT_FP
        or pre_event.get("status") != "Q221_PRE_EVENT_PARENT_SOURCE_FEASIBILITY_COMPLETE_LINEAGE_UNRESOLVED"
        or pre_event.get("interpretation", {}).get("recipient_to_issuer_mapping_frozen") is not False
        or pre_event.get("interpretation", {}).get("q221_gate_positive") is not False
    ):
        raise BridgeError("Q221_FPDS_PRE_EVENT_RECEIPT_STATE_MISMATCH")
    if pre_event.get("analysis_fingerprint") != "75a9818d18436dbf24beb877b00431c0c46015cad4a35efc66a07e2d9c69832f":
        raise BridgeError("Q221_FPDS_PRE_EVENT_ANALYSIS_FINGERPRINT_MISMATCH")
    return boundary, prereg, pre_event


def _tag_name(tag: str) -> str:
    return re.sub(r"[^a-z0-9]", "", tag.rsplit("}", 1)[-1].lower())


def _text_values(entry: ET.Element) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for node in entry.iter():
        name = _tag_name(str(node.tag))
        value = " ".join("".join(node.itertext()).split())
        if not name or not value:
            continue
        bucket = result.setdefault(name, [])
        if value not in bucket:
            bucket.append(value)
    return result


def _get(values: dict[str, list[str]], *keys: str) -> list[str]:
    output: list[str] = []
    for key in keys:
        for value in values.get(key, []):
            if value not in output:
                output.append(value)
    return output


def _normalize_name(value: str) -> str:
    value = value.replace("&", " AND ")
    value = unicodedata.normalize("NFKD", value)
    ascii_value = value.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Z0-9]", "", ascii_value.upper())


def _date_prefix(value: str) -> str | None:
    candidate = value.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(candidate[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_atom(body: bytes) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise BridgeError("Q221_FPDS_ATOM_XML_INVALID") from exc
    entries = [node for node in root.iter() if _tag_name(str(node.tag)) == "entry"]
    if not entries:
        raise BridgeError("Q221_FPDS_ATOM_HAS_NO_ENTRIES")
    parsed = []
    for entry in entries:
        values = _text_values(entry)
        piids = _get(values, "piid")
        mods = _get(values, "modificationnumber", "modnumber", "modificationnum")
        signed_dates = _get(values, "signeddate", "datesigned")
        uei_values = _get(values, "uei", "uniqueentityid", "uniqueentityidentifier", "genericstring02")
        duns_values = _get(values, "dunsnumber", "vendordunsnumber", "uniqueentityidduns")
        names = _get(
            values,
            "ueilegalbusinessname",
            "vendornamefromcontract",
            "awardeeNameFromContract",
            "awardeeName",
            "vendorname",
            "legalbusinessname",
        )
        cage_values = _get(values, "cagecode")
        entity_sources = _get(values, "entitydatasource")
        parsed.append({
            "piid_values": piids,
            "modification_number_values": mods,
            "signed_date_values": signed_dates,
            "uei_values": uei_values,
            "duns_values": duns_values,
            "awardee_name_values": names,
            "cage_code_values": cage_values,
            "entity_data_source_values": entity_sources,
        })
    return parsed


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class _Budget:
    def __init__(self) -> None:
        self.used = 0
        self.last_start = 0.0

    def wait(self) -> None:
        delay = REQUEST_GAP_SECONDS - (time.monotonic() - self.last_start)
        if delay > 0:
            time.sleep(delay)
        self.last_start = time.monotonic()

    def add(self, count: int) -> None:
        if count < 0 or self.used + count > MAX_TOTAL_RESPONSE_BYTES:
            raise BridgeError("Q221_FPDS_TOTAL_RESPONSE_BUDGET_EXCEEDED")
        self.used += count


def _request_url(piid: str) -> str:
    q = f'PIID:"{piid}"'
    return ENDPOINT + "?" + urllib.parse.urlencode({"FEEDNAME": FEEDNAME, "q": q})


def _read_limited(stream: Any, limit: int) -> bytes:
    body = stream.read(limit + 1)
    if len(body) > limit:
        raise BridgeError("Q221_FPDS_RESPONSE_OVER_LIMIT")
    return body


def fetch_one(spec: dict[str, Any], budget: _Budget) -> dict[str, Any]:
    url = _request_url(str(spec["piid"]))
    parsed_url = urlparse(url)
    if parsed_url.scheme != "https" or parsed_url.hostname != ALLOWED_HOST or parsed_url.path != "/dbsight/FEEDS/ATOM":
        raise BridgeError("Q221_FPDS_REQUEST_URL_OUTSIDE_PINNED_ENDPOINT")
    budget.wait()
    observation: dict[str, Any] = {
        "record_id": spec["record_id"],
        "transaction_key": spec["transaction_key"],
        "requested_url": url,
        "method": "GET",
        "requested_host": parsed_url.hostname,
        "http_status": None,
        "content_type": "",
        "response_bytes": 0,
        "response_sha256": None,
        "response_persisted": False,
        "entry_count": 0,
        "piid_entry_count": 0,
        "piid_modification_candidate_count": 0,
        "exact_tuple_count": 0,
        "observed_records": [],
        "status": "NOT_ATTEMPTED",
    }
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DWR-debug/trading-agent-public Q221 FPDS bounded identity bridge/1.0",
            "Accept": "application/atom+xml, application/xml;q=0.9, text/xml;q=0.8",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
        method="GET",
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=TIMEOUT_SECONDS) as response:
            status = int(getattr(response, "status", 200))
            content_type = str(response.headers.get("Content-Type", ""))
            body = _read_limited(response, MAX_RESPONSE_BYTES_EACH)
            budget.add(len(body))
            observation.update({
                "http_status": status,
                "content_type": content_type,
                "response_bytes": len(body),
                "response_sha256": sha256(body),
            })
    except BridgeError as exc:
        observation["status"] = "RESPONSE_OVER_LIMIT" if "OVER_LIMIT" in str(exc) else "FETCH_CONTRACT_ERROR"
        observation["error_code"] = str(exc)[:180]
        return observation
    except urllib.error.HTTPError as exc:
        location = str(exc.headers.get("Location") or "")
        location_host = urlparse(location).hostname if location else None
        try:
            body = _read_limited(exc, MAX_RESPONSE_BYTES_EACH)
            budget.add(len(body))
            observation.update({
                "http_status": int(exc.code),
                "content_type": str(exc.headers.get("Content-Type", "")),
                "response_bytes": len(body),
                "response_sha256": sha256(body),
                "redirect_location_host": location_host,
            })
            if exc.code in {301, 302, 303, 307, 308}:
                observation["status"] = "REDIRECT_BLOCKED"
            else:
                observation["status"] = "HTTP_NON_200"
        except BridgeError as limit_exc:
            observation["http_status"] = int(exc.code)
            observation["redirect_location_host"] = location_host
            observation["status"] = "ERROR_RESPONSE_OVER_LIMIT"
            observation["error_code"] = str(limit_exc)[:180]
        return observation
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        observation.update({"status": "NETWORK_ERROR", "error_type": type(exc).__name__})
        return observation

    if status != 200:
        observation["status"] = "HTTP_NON_200"
        return observation
    if not any(token in content_type.lower() for token in ("atom", "xml")):
        observation["status"] = "UNEXPECTED_CONTENT_TYPE"
        return observation
    try:
        entries = parse_atom(body)
    except BridgeError as exc:
        observation.update({"status": "ATOM_PARSE_FAILED", "error_code": str(exc)})
        return observation
    observation["entry_count"] = len(entries)
    if len(entries) > MAX_ATOM_ENTRIES_EACH:
        observation.update({"status": "ATOM_ENTRY_COUNT_OVER_LIMIT", "entry_count": len(entries)})
        return observation

    piid_candidates = []
    mod_candidates = []
    exact = []
    for entry in entries:
        if spec["piid"] not in entry["piid_values"]:
            continue
        piid_candidates.append(entry)
        if spec["modification_number"] not in entry["modification_number_values"]:
            continue
        mod_candidates.append(entry)
        if spec["action_date"] not in {
            parsed for raw in entry["signed_date_values"] if (parsed := _date_prefix(raw)) is not None
        }:
            continue
        exact.append(entry)
    observation["piid_entry_count"] = len(piid_candidates)
    observation["piid_modification_candidate_count"] = len(mod_candidates)
    observation["exact_tuple_count"] = len(exact)

    for entry in exact:
        record = {
            "piid_values": entry["piid_values"],
            "modification_number_values": entry["modification_number_values"],
            "signed_date_values": entry["signed_date_values"],
            "uei_values": entry["uei_values"],
            "duns_values": entry["duns_values"],
            "awardee_name_values": entry["awardee_name_values"],
            "cage_code_values": entry["cage_code_values"],
            "entity_data_source_values": entry["entity_data_source_values"],
        }
        uei_match = spec["recipient_uei"] in entry["uei_values"]
        name_keys = {_normalize_name(x) for x in spec["accepted_legal_names"]}
        observed_name_keys = {_normalize_name(x) for x in entry["awardee_name_values"]}
        name_match = bool(name_keys & observed_name_keys)
        record["frozen_uei_match"] = uei_match
        record["accepted_legal_name_match"] = name_match
        record["duns_present"] = bool(entry["duns_values"])
        record["identifier_regime_at_action"] = spec["identifier_regime_at_action"]
        if not uei_match:
            record["row_interpretation"] = "EXACT_CONTRACT_TUPLE_UEI_MISMATCH_OR_UEI_NOT_EXPOSED"
        elif not name_match:
            record["row_interpretation"] = "EXACT_CONTRACT_TUPLE_UEI_MATCH_NAME_NOT_CONFIRMED"
        elif spec["identifier_regime_at_action"] == "DUNS_AUTHORITATIVE_UEI_NOT_YET_AUTHORITATIVE":
            record["row_interpretation"] = "UEI_AND_NAME_MATCH_ON_CURRENT_RECORD_POST_HOC_CROSSWALK_NOT_CONTEMPORANEOUS_UEI_PROOF"
        else:
            record["row_interpretation"] = "CONTEMPORANEOUS_UEI_REGIME_RECORD_AND_NAME_MATCH"
        observation["observed_records"].append(record)

    if len(exact) > 1:
        observation["status"] = "EXACT_TUPLE_AMBIGUOUS"
    elif len(exact) == 1:
        only = observation["observed_records"][0]
        if only["frozen_uei_match"] and only["accepted_legal_name_match"]:
            observation["status"] = "EXACT_RECORD_UEI_AND_LEGAL_NAME_MATCH"
        else:
            observation["status"] = "EXACT_TUPLE_IDENTIFIER_OR_NAME_INCOMPLETE"
    elif mod_candidates:
        observation["status"] = "PIID_AND_MODIFICATION_FOUND_ACTION_DATE_NOT_EXACT"
    elif piid_candidates:
        observation["status"] = "PIID_FOUND_NO_EXACT_MODIFICATION"
    else:
        observation["status"] = "NO_MATCHING_PIID_ENTRY"
    return observation


def build_receipt(
    repo_root: Path,
    request: dict[str, str],
    observations: list[dict[str, Any]],
    total_bytes: int,
) -> dict[str, Any]:
    exact_match_count = sum(x.get("status") == "EXACT_RECORD_UEI_AND_LEGAL_NAME_MATCH" for x in observations)
    redirects = sum(x.get("status") == "REDIRECT_BLOCKED" for x in observations)
    if exact_match_count == MAX_REQUESTS:
        status = "Q221_FPDS_PUBLIC_ATOM_FOUR_RECORD_IDENTITY_LEADS_COMPLETE"
    elif redirects or all(x.get("status") in {"HTTP_NON_200", "UNEXPECTED_CONTENT_TYPE", "ATOM_PARSE_FAILED", "NO_MATCHING_PIID_ENTRY"} for x in observations):
        status = "Q221_FPDS_PUBLIC_ATOM_ROUTE_UNAVAILABLE_OR_NO_EXACT_RECORDS"
    else:
        status = "Q221_FPDS_PUBLIC_ATOM_IDENTITY_BRIDGE_INCOMPLETE"
    boundary = json.loads((repo_root / BOUNDARY_PATH).read_text(encoding="utf-8"))
    prereg = json.loads((repo_root / PREREG_PATH).read_text(encoding="utf-8"))
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q221_fpds_public_atom_identity_bridge_feasibility",
        "candidate_id": "Q221",
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_run_id": int(__import__("os").environ.get("GITHUB_RUN_ID", "0") or 0),
        "source_contract": {
            "endpoint": ENDPOINT,
            "feedname": FEEDNAME,
            "initial_host_allowlist": [ALLOWED_HOST],
            "redirects_followed": False,
            "sam_contract_awards_api_called": False,
            "source_bodies_persisted": False,
        },
        "frozen_inputs": {
            "boundary_path": BOUNDARY_PATH,
            "boundary_git_blob_sha1": BOUNDARY_BLOB_SHA1,
            "boundary_receipt_fingerprint": BOUNDARY_FP,
            "pre_event_receipt_path": PRE_EVENT_PATH,
            "pre_event_receipt_fingerprint": PRE_EVENT_FP,
            "preregistration_path": PREREG_PATH,
            "record_count": len(prereg["records"]),
        },
        "request_contract": {
            "request_sequence": request["REQUEST_SEQUENCE"],
            "requests_allowed": MAX_REQUESTS,
            "requests_attempted": len(observations),
            "total_response_bytes": total_bytes,
            "max_total_response_bytes": MAX_TOTAL_RESPONSE_BYTES,
            "automatic_retries": 0,
            "redirects_followed": False,
            "query_scope": "one PIID-scoped public Atom request per frozen record; exact modification/date matched locally",
        },
        "observations": observations,
        "aggregate": {
            "sample_size": MAX_REQUESTS,
            "exact_record_uei_and_name_match_count": exact_match_count,
            "historical_record_tuple_unique_count": sum(x.get("exact_tuple_count") == 1 for x in observations),
            "redirect_blocked_count": redirects,
            "response_body_persisted_count": 0,
            "recipient_to_issuer_mapping_frozen": False,
            "historical_parent_lineage_proven": False,
            "historical_first_public_observation_proven": False,
            "q221_gate_positive": False,
        },
        "interpretation": {
            "source_feasibility_only": True,
            "purposeful_fixed_sample_not_prevalence_sample": True,
            "post_hoc_uei_attachment_is_not_treated_as_event_date_uei_proof": True,
            "current_feed_state_is_not_assumed_historically_available": True,
            "scientific_evidence": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
        "next_gate": (
            "Review the four fixed rows individually. Any pre-2022 UEI on a current FPDS record is a post-hoc crosswalk lead, not contemporaneous UEI proof; no row-level positive clears the 348-row public-clock or issuer-mapping gate."
            if exact_match_count else
            "If the public Atom route is redirected, retired, or returns no exact rows, stop this route. Do not follow redirects or call the SAM.gov API without an explicitly available API key."
        ),
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
            "paid_api_budget_usd": 0,
        },
    }
    receipt["analysis_fingerprint"] = canonical_analysis_fingerprint(receipt)
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    return receipt


def capture(repo_root: Path, output: Path) -> dict[str, Any]:
    request = read_request(repo_root / REQUEST_PATH)
    validate_frozen_inputs(repo_root, request)
    budget = _Budget()
    observations = []
    for spec in EXPECTED_RECORDS:
        observations.append(fetch_one(spec, budget))
    receipt = build_receipt(repo_root, request, observations, budget.used)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def verify(repo_root: Path, input_path: Path, output: Path) -> dict[str, Any]:
    request = read_request(repo_root / REQUEST_PATH)
    validate_frozen_inputs(repo_root, request)
    receipt = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(receipt, dict) or receipt.get("record_type") != "q221_fpds_public_atom_identity_bridge_feasibility":
        raise BridgeError("Q221_FPDS_CAPTURE_RECEIPT_TYPE_MISMATCH")
    if receipt.get("frozen_inputs", {}).get("boundary_receipt_fingerprint") != BOUNDARY_FP:
        raise BridgeError("Q221_FPDS_CAPTURE_BOUNDARY_PIN_MISMATCH")
    if receipt.get("frozen_inputs", {}).get("pre_event_receipt_fingerprint") != PRE_EVENT_FP:
        raise BridgeError("Q221_FPDS_CAPTURE_PRE_EVENT_PIN_MISMATCH")
    if receipt.get("request_contract", {}).get("requests_attempted") != MAX_REQUESTS:
        raise BridgeError("Q221_FPDS_CAPTURE_REQUEST_COUNT_MISMATCH")
    if receipt.get("request_contract", {}).get("total_response_bytes", MAX_TOTAL_RESPONSE_BYTES + 1) > MAX_TOTAL_RESPONSE_BYTES:
        raise BridgeError("Q221_FPDS_CAPTURE_BUDGET_MISMATCH")
    if len(receipt.get("observations", [])) != MAX_REQUESTS:
        raise BridgeError("Q221_FPDS_CAPTURE_OBSERVATION_COUNT_MISMATCH")
    for spec, observation in zip(EXPECTED_RECORDS, receipt["observations"]):
        if observation.get("record_id") != spec["record_id"] or observation.get("transaction_key") != spec["transaction_key"]:
            raise BridgeError("Q221_FPDS_CAPTURE_SAMPLE_IDENTITY_MISMATCH")
        if observation.get("requested_host") != ALLOWED_HOST:
            raise BridgeError("Q221_FPDS_CAPTURE_HOST_MISMATCH")
        if observation.get("response_persisted") is not False:
            raise BridgeError("Q221_FPDS_CAPTURE_BODY_PERSISTENCE_FLAG_INVALID")
        if observation.get("http_status") in {301, 302, 303, 307, 308} and observation.get("status") != "REDIRECT_BLOCKED":
            raise BridgeError("Q221_FPDS_CAPTURE_REDIRECT_POLICY_MISMATCH")
        if observation.get("status") == "EXACT_RECORD_UEI_AND_LEGAL_NAME_MATCH":
            if observation.get("exact_tuple_count") != 1 or len(observation.get("observed_records", [])) != 1:
                raise BridgeError("Q221_FPDS_CAPTURE_MATCH_CARDINALITY_MISMATCH")
            row = observation["observed_records"][0]
            if row.get("frozen_uei_match") is not True or row.get("accepted_legal_name_match") is not True:
                raise BridgeError("Q221_FPDS_CAPTURE_MATCH_ASSERTION_MISMATCH")
    calculated_analysis = canonical_analysis_fingerprint(receipt)
    if receipt.get("analysis_fingerprint") != calculated_analysis:
        raise BridgeError("Q221_FPDS_CAPTURE_ANALYSIS_FINGERPRINT_MISMATCH")
    if receipt.get("receipt_fingerprint") != canonical_fingerprint(receipt):
        raise BridgeError("Q221_FPDS_CAPTURE_RECEIPT_FINGERPRINT_MISMATCH")
    if receipt.get("aggregate", {}).get("recipient_to_issuer_mapping_frozen") is not False or receipt.get("aggregate", {}).get("q221_gate_positive") is not False:
        raise BridgeError("Q221_FPDS_CAPTURE_AUTHORITY_DRIFT")
    validation = {
        "schema_version": 1,
        "record_type": "q221_fpds_public_atom_identity_bridge_offline_validation",
        "status": "DETERMINISTIC_CAPTURE_RECEIPT_VALIDATED",
        "analysis_fingerprint": receipt["analysis_fingerprint"],
        "capture_receipt_fingerprint": receipt["receipt_fingerprint"],
        "workflow_run_id": receipt.get("workflow_run_id"),
        "sample_size": len(receipt["observations"]),
        "validated_observation_count": MAX_REQUESTS,
        "source_responses_replayed": False,
        "network_requests_made": 0,
        "source_gate_positive": False,
        "recipient_to_issuer_mapping_frozen": False,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    validation["receipt_fingerprint"] = canonical_fingerprint(validation)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(validation, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return validation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("capture", "verify"), required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = capture(args.repo_root, args.output) if args.mode == "capture" else verify(
        args.repo_root,
        args.input if args.input is not None else Path("/missing/capture-receipt.json"),
        args.output,
    )
    print(json.dumps({
        "status": result.get("status"),
        "analysis_fingerprint": result.get("analysis_fingerprint"),
        "receipt_fingerprint": result.get("receipt_fingerprint"),
        "request_count": result.get("request_contract", {}).get("requests_attempted"),
        "exact_record_uei_and_name_match_count": result.get("aggregate", {}).get("exact_record_uei_and_name_match_count"),
        "network_requests_made": result.get("network_requests_made"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
