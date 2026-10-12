"""Bounded current-parent identity lead map for all frozen Q221 recipients.

Current parent profiles are leads only. This does not establish historical parent
lineage or recipient-to-issuer identity at any transaction event date.
"""
from __future__ import annotations

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

SOURCE_RECEIPT_PATH = "research/evidence/q221_historical_public_boundary_latest.json"
SOURCE_RECEIPT_GIT_BLOB_SHA = "b78cf6f7b48af3f914ee7c6d06a38f6485b0438f"
SOURCE_RECEIPT_FINGERPRINT = "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
FEASIBILITY_RUN_ID = "38303469112"
FEASIBILITY_RECEIPT_FINGERPRINT = "d4f5819f51849d7ba037ec0fa610f5e6e47b74b9353a0c534b6e2e666842509e"
FEASIBILITY_ARTIFACT_NAME = "q221-recipient-parent-identity-probe-38303469112-1"
ENDPOINT = "https://api.usaspending.gov/api/v2/recipient/"
USER_AGENT = "DWR-debug/trading-agent-public Q221 current-parent lead map/1.0"
MAX_RESPONSE_BYTES = 100_000
MAX_TOTAL_BYTES = 25_000_000
REQUEST_GAP_SECONDS = 1.0
TIMEOUT_SECONDS = 30

FROZEN_REQUEST_VALUES = {
    "RUN_Q221_CURRENT_PARENT_MAP_PROBE": "true",
    "REASON": "BOUNDED_CURRENT_PARENT_IDENTITY_LEADS_FOR_FROZEN_247_RECIPIENTS",
    "SOURCE_RECEIPT_PATH": SOURCE_RECEIPT_PATH,
    "SOURCE_RECEIPT_GIT_BLOB_SHA": SOURCE_RECEIPT_GIT_BLOB_SHA,
    "SOURCE_RECEIPT_FINGERPRINT": SOURCE_RECEIPT_FINGERPRINT,
    "FEASIBILITY_RUN_ID": FEASIBILITY_RUN_ID,
    "FEASIBILITY_RECEIPT_FINGERPRINT": FEASIBILITY_RECEIPT_FINGERPRINT,
    "RECIPIENT_COUNT": "247",
    "QUERY_COUNT": "247",
    "MAX_RESPONSE_BYTES": str(MAX_RESPONSE_BYTES),
    "MAX_TOTAL_BYTES": str(MAX_TOTAL_BYTES),
    "REQUEST_GAP_SECONDS": "1",
    "HISTORICAL_IDENTITY_CLAIM": "false",
    "RECIPIENT_TO_ISSUER_MAPPING": "false",
    "PERFORMANCE": "false",
    "HOLDOUT_SELECTION": "false",
    "RANKING": "false",
    "TUNING": "false",
    "PROMOTION": "false",
    "LIVE_EXECUTION": "false",
}
REQUEST_KEYS = set(FROZEN_REQUEST_VALUES) | {"REQUEST_SEQUENCE"}


class ProbeError(ValueError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def canonical_fingerprint(payload: dict[str, Any]) -> str:
    value = dict(payload)
    value.pop("receipt_fingerprint", None)
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def read_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.strip() != line or "=" not in line:
            raise ProbeError(f"Q221_PARENT_MAP_REQUEST_INVALID_LINE:{number}")
        key, value = line.split("=", 1)
        if not key or not value or key in values:
            raise ProbeError(f"Q221_PARENT_MAP_REQUEST_INVALID_KEY_VALUE:{number}")
        values[key] = value
    if set(values) != REQUEST_KEYS:
        raise ProbeError("Q221_PARENT_MAP_REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN_REQUEST_VALUES.items():
        if values[key] != expected:
            raise ProbeError("Q221_PARENT_MAP_REQUEST_VALUE_MISMATCH:" + key)
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", values["REQUEST_SEQUENCE"]):
        raise ProbeError("Q221_PARENT_MAP_REQUEST_SEQUENCE_INVALID")
    return values


def validate_source(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw = path.read_bytes()
    if git_blob_sha1(raw) != SOURCE_RECEIPT_GIT_BLOB_SHA:
        raise ProbeError("Q221_PARENT_MAP_SOURCE_GIT_BLOB_SHA_MISMATCH")
    source = json.loads(raw.decode("utf-8"))
    if source.get("receipt_fingerprint") != SOURCE_RECEIPT_FINGERPRINT or canonical_fingerprint(source) != SOURCE_RECEIPT_FINGERPRINT:
        raise ProbeError("Q221_PARENT_MAP_SOURCE_FINGERPRINT_MISMATCH")
    candidates = source.get("recipient_identity_candidates", [])
    if source.get("unique_recipient_identity_count") != 247 or source.get("historical_first_public_observation_proven") is not False or source.get("recipient_to_issuer_mapping_frozen") is not False:
        raise ProbeError("Q221_PARENT_MAP_SOURCE_GATE_STATE_CHANGED")
    if len(candidates) != 247 or len({x.get("recipient_id") for x in candidates}) != 247:
        raise ProbeError("Q221_PARENT_MAP_CANDIDATE_COUNT_OR_IDENTITY_INVALID")
    for candidate in candidates:
        if not candidate.get("recipient_id") or not candidate.get("recipient_uei"):
            raise ProbeError("Q221_PARENT_MAP_CANDIDATE_IDENTITY_MISSING")
        if candidate.get("mapping_status") != "UNMAPPED" or candidate.get("issuer_symbol") is not None:
            raise ProbeError("Q221_PARENT_MAP_SOURCE_MAPPING_STATE_CHANGED")
    return source, sorted(candidates, key=lambda x: x["recipient_id"])


def validate_feasibility(path: Path) -> dict[str, Any]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if receipt.get("record_type") != "q221_recipient_parent_identity_probe":
        raise ProbeError("Q221_PARENT_MAP_FEASIBILITY_RECEIPT_TYPE_MISMATCH")
    if receipt.get("status") != "CURRENT_PROFILE_PROBE_COMPLETE_HISTORY_UNPROVEN":
        raise ProbeError("Q221_PARENT_MAP_FEASIBILITY_NOT_COMPLETE")
    if receipt.get("receipt_fingerprint") != FEASIBILITY_RECEIPT_FINGERPRINT or canonical_fingerprint(receipt) != FEASIBILITY_RECEIPT_FINGERPRINT:
        raise ProbeError("Q221_PARENT_MAP_FEASIBILITY_FINGERPRINT_MISMATCH")
    if receipt.get("sample_count") != 7 or receipt.get("query_count") != 14:
        raise ProbeError("Q221_PARENT_MAP_FEASIBILITY_COUNTS_MISMATCH")
    if receipt.get("source_receipt_git_blob_sha") != SOURCE_RECEIPT_GIT_BLOB_SHA or receipt.get("source_receipt_fingerprint") != SOURCE_RECEIPT_FINGERPRINT:
        raise ProbeError("Q221_PARENT_MAP_FEASIBILITY_SOURCE_MISMATCH")
    if receipt.get("historical_parent_lineage_proven") is not False or receipt.get("recipient_to_issuer_mapping_frozen") is not False:
        raise ProbeError("Q221_PARENT_MAP_FEASIBILITY_OVERCLAIM")
    return receipt


def classify_parent(recipient_uei: str, parent_uei: str | None, parent_id: str | None) -> str:
    if not parent_uei:
        return "PARENT_UEI_MISSING"
    if parent_uei == recipient_uei:
        return "CURRENT_PROFILE_SELF_OR_NO_SEPARATE_PARENT"
    if parent_id:
        return "CURRENT_PARENT_ENTITY_LEAD"
    return "PARENT_UEI_DIFFERS_PARENT_ID_MISSING"


class Budget:
    def __init__(self):
        self.used = 0
        self.next_request_at = 0.0

    def wait(self):
        delay = self.next_request_at - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        self.next_request_at = time.monotonic() + REQUEST_GAP_SECONDS

    def add(self, size: int):
        if size < 0 or self.used + size > MAX_TOTAL_BYTES:
            raise ProbeError("Q221_PARENT_MAP_TOTAL_RESPONSE_BUDGET_EXCEEDED")
        self.used += size


def fetch_profile(candidate: dict[str, Any], budget: Budget) -> dict[str, Any]:
    recipient_id = candidate["recipient_id"]
    url = ENDPOINT + urllib.parse.quote(recipient_id, safe="") + "/?year=all"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json", "Accept-Encoding": "identity", "Connection": "close"}, method="GET")
    budget.wait()
    result: dict[str, Any] = {"requested_url": url, "http_status": None, "content_type": "", "response_bytes": 0, "response_sha256": None}
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            result.update({"http_status": int(getattr(response, "status", 200)), "content_type": str(response.headers.get("Content-Type", ""))})
            if len(raw) > MAX_RESPONSE_BYTES:
                result["status"] = "RESPONSE_OVER_LIMIT"
                return result
            budget.add(len(raw))
            result.update({"response_bytes": len(raw), "response_sha256": sha256(raw)})
            if result["http_status"] != 200:
                result["status"] = "HTTP_NON_200"
                return result
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                result["status"] = "JSON_INVALID"
                return result
            if not isinstance(payload, dict):
                result["status"] = "JSON_INVALID"
                return result
            profile = {
                "recipient_id": payload.get("recipient_id"),
                "recipient_level": payload.get("recipient_level"),
                "uei": payload.get("uei"),
                "parent_id": payload.get("parent_id"),
                "parent_uei": payload.get("parent_uei"),
                "parent_name": payload.get("parent_name"),
                "parents": payload.get("parents"),
                "business_types": payload.get("business_types"),
            }
            if profile["recipient_id"] != recipient_id:
                result["status"] = "RECIPIENT_ID_MISMATCH"
            elif profile["uei"] != candidate["recipient_uei"]:
                result["status"] = "RECIPIENT_UEI_MISMATCH"
            else:
                result["status"] = "PROFILE_CAPTURED"
            result["profile"] = profile
            return result
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            result["status"] = "HTTP_ERROR_BODY_OVER_LIMIT"
            return result
        budget.add(len(raw))
        result.update({"status": "HTTP_ERROR", "http_status": int(exc.code), "content_type": str(exc.headers.get("Content-Type", "")), "response_bytes": len(raw), "response_sha256": sha256(raw), "error_excerpt": " ".join(raw.decode("utf-8", errors="replace").split())[:200]})
        return result
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result.update({"status": "TRANSPORT_ERROR", "error_type": type(exc).__name__})
        return result


def run_probe(request: dict[str, str], source_path: Path, feasibility_path: Path, output: Path) -> dict[str, Any]:
    source, candidates = validate_source(source_path)
    feasibility = validate_feasibility(feasibility_path)
    budget = Budget()
    rows = []
    complete = True
    for candidate in candidates:
        observed = fetch_profile(candidate, budget)
        profile = observed.get("profile") or {}
        if observed.get("status") != "PROFILE_CAPTURED":
            complete = False
        parent_uei = profile.get("parent_uei")
        parent_id = profile.get("parent_id")
        rows.append({
            "recipient_id": candidate["recipient_id"],
            "recipient_uei": candidate["recipient_uei"],
            "recipient_name_from_frozen_sample": candidate.get("recipient_name"),
            "observed_transaction_count": candidate.get("observed_transaction_count"),
            "current_profile_observation": observed,
            "current_parent_classification": classify_parent(candidate["recipient_uei"], parent_uei, parent_id) if observed.get("status") == "PROFILE_CAPTURED" else "PROFILE_NOT_VERIFIED",
            "historical_parent_lineage_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
        })
    classes = {}
    for row in rows:
        key = row["current_parent_classification"]
        classes[key] = classes.get(key, 0) + 1
    receipt = {
        "schema_version": 1,
        "record_type": "q221_current_parent_identity_lead_map",
        "candidate_id": "Q221",
        "status": "CURRENT_PARENT_MAP_COMPLETE_HISTORY_UNPROVEN" if complete and len(rows) == 247 else "CURRENT_PARENT_MAP_INCOMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_receipt_path": SOURCE_RECEIPT_PATH,
        "source_receipt_git_blob_sha": SOURCE_RECEIPT_GIT_BLOB_SHA,
        "source_receipt_fingerprint": SOURCE_RECEIPT_FINGERPRINT,
        "feasibility_run_id": FEASIBILITY_RUN_ID,
        "feasibility_receipt_fingerprint": FEASIBILITY_RECEIPT_FINGERPRINT,
        "endpoint": ENDPOINT,
        "source_contract_url": "https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/api_contracts/contracts/v2/recipient/recipient_id.md",
        "recipient_count_expected": 247,
        "recipient_count_captured": len(rows),
        "query_count_expected": 247,
        "query_count_captured": sum(1 for x in rows if x["current_profile_observation"].get("status") in {"PROFILE_CAPTURED", "HTTP_ERROR"}),
        "verified_profile_count": sum(1 for x in rows if x["current_profile_observation"].get("status") == "PROFILE_CAPTURED"),
        "current_parent_classification_counts": classes,
        "response_bytes": budget.used,
        "response_budget_bytes": MAX_TOTAL_BYTES,
        "recipients": rows,
        "current_parent_identity_leads_only": True,
        "historical_parent_lineage_proven": False,
        "recipient_to_issuer_mapping_frozen": False,
        "historical_first_public_observation_proven": False,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "next_gate": "For any non-self parent UEI lead, obtain independent pre-event entity evidence and verify the parent relationship as of the transaction date; do not map issuers by name similarity.",
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "receipt_fingerprint": receipt["receipt_fingerprint"], "recipient_count_captured": receipt["recipient_count_captured"], "verified_profile_count": receipt["verified_profile_count"], "query_count_captured": receipt["query_count_captured"], "current_parent_classification_counts": classes, "response_bytes": receipt["response_bytes"]}, sort_keys=True))
    if receipt["status"] != "CURRENT_PARENT_MAP_COMPLETE_HISTORY_UNPROVEN":
        raise ProbeError("Q221_CURRENT_PARENT_MAP_INCOMPLETE")
    return receipt


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--feasibility", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = read_request(args.request)
    run_probe(request, args.source, args.feasibility, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
