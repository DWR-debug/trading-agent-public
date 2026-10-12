"""Bounded USAspending recipient-profile probe for Q221 identity-gate feasibility.

This is current-state metadata discovery only. A parent UEI or recipient profile
returned today does not establish the historical parent relationship at a
transaction's action/publication date and does not map the recipient to a
public issuer. The probe never promotes a mapping.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RECEIPT_PATH = "research/evidence/q221_historical_public_boundary_latest.json"
SOURCE_RECEIPT_GIT_BLOB_SHA = "b78cf6f7b48af3f914ee7c6d06a38f6485b0438f"
SOURCE_RECEIPT_FINGERPRINT = "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
ENDPOINT = "https://api.usaspending.gov/api/v2/recipient/"
USER_AGENT = "DWR-debug/trading-agent-public Q221 recipient parent identity probe/1.0"
SAMPLES = [
    {
        "window": "2019",
        "year": "2019",
        "transaction_key": "0001|29|2019-01-02|3903ae3c-2661-60bb-cdd3-1f26ad214167-C|DMHDNDCPWUD1",
        "recipient_id": "3903ae3c-2661-60bb-cdd3-1f26ad214167-C",
        "recipient_uei": "DMHDNDCPWUD1"
    },
    {
        "window": "2020",
        "year": "2020",
        "transaction_key": "36C26320C0038|0|2020-01-01|4aba5b9a-b1b9-2fe8-5ca8-f597fd6214a0-C|PQ4BPVMFDKG3",
        "recipient_id": "4aba5b9a-b1b9-2fe8-5ca8-f597fd6214a0-C",
        "recipient_uei": "PQ4BPVMFDKG3"
    },
    {
        "window": "2021",
        "year": "2021",
        "transaction_key": "140G0121P0059|0|2021-01-01|ad5aec73-5842-3439-b118-0ceed81bd508-C|KVNTFXNE5BP4",
        "recipient_id": "ad5aec73-5842-3439-b118-0ceed81bd508-C",
        "recipient_uei": "KVNTFXNE5BP4"
    },
    {
        "window": "2022",
        "year": "2022",
        "transaction_key": "36C24620P0456|P00003|2022-01-01|79f0de1d-ba0f-6f34-00e2-1bb261ab23f2-C|LE6ZHUAJLEF6",
        "recipient_id": "79f0de1d-ba0f-6f34-00e2-1bb261ab23f2-C",
        "recipient_uei": "LE6ZHUAJLEF6"
    },
    {
        "window": "2023",
        "year": "2023",
        "transaction_key": "FA881820F0102|P00023|2023-01-01|20af0683-f17d-1f8f-38ee-2f11bd124559-C|MMLKPW9JLX64",
        "recipient_id": "20af0683-f17d-1f8f-38ee-2f11bd124559-C",
        "recipient_uei": "MMLKPW9JLX64"
    },
    {
        "window": "2024",
        "year": "2024",
        "transaction_key": "140G0124F0040|0|2024-01-01|dc86b1b7-121c-4683-ba12-4101b6be98a8-C|K5L5KR3MZ538",
        "recipient_id": "dc86b1b7-121c-4683-ba12-4101b6be98a8-C",
        "recipient_uei": "K5L5KR3MZ538"
    },
    {
        "window": "2025_partial",
        "year": "2025",
        "transaction_key": "HHSN275201800216P|P00001|2025-01-01|560d59f5-9f0b-62e4-b1d9-56fac81634d2-C|WW17SJDENJ16",
        "recipient_id": "560d59f5-9f0b-62e4-b1d9-56fac81634d2-C",
        "recipient_uei": "WW17SJDENJ16"
    }
]
MAX_RESPONSE_BYTES = 1_000_000
MAX_TOTAL_BYTES = 14_000_000
REQUEST_GAP_SECONDS = 1.0
TIMEOUT_SECONDS = 30

FROZEN_REQUEST_VALUES = {
    "RUN_Q221_RECIPIENT_PARENT_IDENTITY_PROBE": "true",
    "REASON": "BOUNDED_CURRENT_PROFILE_PARENT_UEI_FEASIBILITY_PROBE",
    "SOURCE_RECEIPT_PATH": SOURCE_RECEIPT_PATH,
    "SOURCE_RECEIPT_GIT_BLOB_SHA": SOURCE_RECEIPT_GIT_BLOB_SHA,
    "SOURCE_RECEIPT_FINGERPRINT": SOURCE_RECEIPT_FINGERPRINT,
    "SAMPLE_COUNT": str(len(SAMPLES)),
    "QUERY_COUNT": str(len(SAMPLES) * 2),
    "MAX_RESPONSE_BYTES": str(MAX_RESPONSE_BYTES),
    "MAX_TOTAL_BYTES": str(MAX_TOTAL_BYTES),
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
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(raw)


def read_request(path: Path) -> dict[str, str]:
    values = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.strip() != line or "=" not in line:
            raise ProbeError(f"Q221_RECIPIENT_REQUEST_INVALID_LINE:{number}")
        key, value = line.split("=", 1)
        if not key or not value or key in values:
            raise ProbeError(f"Q221_RECIPIENT_REQUEST_INVALID_KEY_VALUE:{number}")
        values[key] = value
    if set(values) != REQUEST_KEYS:
        raise ProbeError("Q221_RECIPIENT_REQUEST_KEY_SET_MISMATCH")
    for key, expected in FROZEN_REQUEST_VALUES.items():
        if values[key] != expected:
            raise ProbeError("Q221_RECIPIENT_REQUEST_VALUE_MISMATCH:" + key)
    if len(values["REQUEST_SEQUENCE"]) != 20 or not values["REQUEST_SEQUENCE"].endswith("Z"):
        raise ProbeError("Q221_RECIPIENT_REQUEST_SEQUENCE_INVALID")
    return values


def validate_source(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if git_blob_sha1(raw) != SOURCE_RECEIPT_GIT_BLOB_SHA:
        raise ProbeError("Q221_RECIPIENT_SOURCE_GIT_BLOB_SHA_MISMATCH")
    payload = json.loads(raw.decode("utf-8"))
    if payload.get("receipt_fingerprint") != SOURCE_RECEIPT_FINGERPRINT:
        raise ProbeError("Q221_RECIPIENT_SOURCE_RECEIPT_FINGERPRINT_MISMATCH")
    if canonical_fingerprint(payload) != SOURCE_RECEIPT_FINGERPRINT:
        raise ProbeError("Q221_RECIPIENT_SOURCE_CANONICAL_FINGERPRINT_INVALID")
    by_key = {x.get("transaction_key"): x for x in payload.get("transactions", [])}
    for sample in SAMPLES:
        row = by_key.get(sample["transaction_key"])
        if not row:
            raise ProbeError("Q221_RECIPIENT_SAMPLE_KEY_MISSING:" + sample["transaction_key"])
        for field in ("recipient_id", "recipient_uei", "window"):
            if str(row.get(field) or "") != str(sample[field]):
                raise ProbeError("Q221_RECIPIENT_SAMPLE_FIELD_MISMATCH:" + sample["transaction_key"] + ":" + field)
    return payload


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
            raise ProbeError("Q221_RECIPIENT_TOTAL_RESPONSE_BUDGET_EXCEEDED")
        self.used += size


def fetch_profile(recipient_id: str, year: str, budget: Budget) -> dict[str, Any]:
    encoded = urllib.parse.quote(recipient_id, safe="")
    url = ENDPOINT + encoded + "/?year=" + urllib.parse.quote(year, safe="")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json", "Accept-Encoding": "identity", "Connection": "close"},
        method="GET",
    )
    budget.wait()
    result: dict[str, Any] = {"requested_url": url, "http_status": None, "content_type": "", "response_bytes": 0, "response_sha256": None}
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            result["http_status"] = int(getattr(response, "status", 200))
            result["content_type"] = str(response.headers.get("Content-Type", ""))
            if len(raw) > MAX_RESPONSE_BYTES:
                result["status"] = "RESPONSE_OVER_LIMIT"
                return result
            budget.add(len(raw))
            result["response_bytes"] = len(raw)
            result["response_sha256"] = sha256(raw)
            if result["http_status"] != 200:
                result["status"] = "HTTP_NON_200"
                return result
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                result["status"] = "JSON_INVALID"
                return result
            result["status"] = "PROFILE_CAPTURED"
            result["profile"] = {
                "recipient_id": payload.get("recipient_id"),
                "recipient_level": payload.get("recipient_level"),
                "uei": payload.get("uei"),
                "parent_id": payload.get("parent_id"),
                "parent_uei": payload.get("parent_uei"),
                "parent_name": payload.get("parent_name"),
                "parents": payload.get("parents"),
                "business_types": payload.get("business_types"),
            }
            return result
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            result["status"] = "HTTP_ERROR_BODY_OVER_LIMIT"
            return result
        budget.add(len(raw))
        result.update({"http_status": int(exc.code), "content_type": str(exc.headers.get("Content-Type", "")), "response_bytes": len(raw), "response_sha256": sha256(raw), "status": "HTTP_ERROR"})
        result["error_excerpt"] = " ".join(raw.decode("utf-8", errors="replace").split())[:300]
        return result
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result.update({"status": "TRANSPORT_ERROR", "error_type": type(exc).__name__})
        return result


def run_probe(request: dict[str, str], source_path: Path, output: Path) -> dict[str, Any]:
    source = validate_source(source_path)
    budget = Budget()
    rows = []
    all_profiles = True
    for sample in SAMPLES:
        sample_result = {**sample, "queries": []}
        for year in ("all", sample["year"]):
            result = fetch_profile(sample["recipient_id"], year, budget)
            profile = result.get("profile")
            if result.get("status") != "PROFILE_CAPTURED" or not profile:
                all_profiles = False
            else:
                if profile.get("recipient_id") != sample["recipient_id"]:
                    result["identity_check"] = "RECIPIENT_ID_MISMATCH"
                    all_profiles = False
                elif profile.get("uei") and profile.get("uei") != sample["recipient_uei"]:
                    result["identity_check"] = "CURRENT_UEI_DIFFERS_FROM_FROZEN_SAMPLE"
                    all_profiles = False
                elif not profile.get("uei"):
                    result["identity_check"] = "PROFILE_UEI_MISSING"
                    all_profiles = False
                else:
                    result["identity_check"] = "EXACT_RECIPIENT_ID_AND_UEI_MATCH"
            sample_result["queries"].append({"year_query": year, **result})
        profiles = [x.get("profile") for x in sample_result["queries"]]
        if len(profiles) == 2 and all(isinstance(x, dict) for x in profiles):
            a, b = profiles
            sample_result["parent_metadata_comparison"] = {
                "all_vs_fiscal_year_parent_id_equal": a.get("parent_id") == b.get("parent_id"),
                "all_vs_fiscal_year_parent_uei_equal": a.get("parent_uei") == b.get("parent_uei"),
                "interpretation": "CURRENT_PROFILE_QUERY_CONSISTENCY_ONLY_NOT_HISTORICAL_LINEAGE",
            }
        else:
            sample_result["parent_metadata_comparison"] = None
    receipt = {
        "schema_version": 1,
        "record_type": "q221_recipient_parent_identity_probe",
        "candidate_id": "Q221",
        "status": "CURRENT_PROFILE_PROBE_COMPLETE_HISTORY_UNPROVEN" if all_profiles else "CURRENT_PROFILE_PROBE_INCOMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_receipt_path": SOURCE_RECEIPT_PATH,
        "source_receipt_git_blob_sha": SOURCE_RECEIPT_GIT_BLOB_SHA,
        "source_receipt_fingerprint": SOURCE_RECEIPT_FINGERPRINT,
        "endpoint": ENDPOINT,
        "source_contract_url": "https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/api_contracts/contracts/v2/recipient/recipient_id.md",
        "sample_count": len(SAMPLES),
        "query_count": sum(len(x["queries"]) for x in rows),
        "response_bytes": budget.used,
        "response_budget_bytes": MAX_TOTAL_BYTES,
        "samples": rows,
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
        "next_gate": "If profile responses expose useful parent UEI data, validate parent identity against an independent pre-event source; never treat the profile endpoint's current parent record as historical mapping.",
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "receipt_fingerprint": receipt["receipt_fingerprint"], "sample_count": receipt["sample_count"], "query_count": receipt["query_count"], "response_bytes": receipt["response_bytes"]}, sort_keys=True))
    if receipt["status"] != "CURRENT_PROFILE_PROBE_COMPLETE_HISTORY_UNPROVEN":
        raise ProbeError("Q221_RECIPIENT_PROFILE_PROBE_INCOMPLETE")
    return receipt


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = read_request(args.request)
    run_probe(request, args.source, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
