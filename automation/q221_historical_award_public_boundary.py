"""Bounded Q221 USAspending transaction census and public-clock falsification.

The current API can expose transaction/action metadata; it does not itself prove
when a row first became publicly observable. This workpack deliberately keeps
that historical boundary and recipient-to-issuer mapping gates closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
VINTAGE_RECEIPT = ROOT / "research/evidence/q221_historical_source_vintages_latest.json"
OUTPUT_DEFAULT = ROOT / "research/evidence/q221_historical_public_boundary_latest.json"
ENDPOINT = "https://api.usaspending.gov/api/v2/search/spending_by_transaction/"
USER_AGENT = "DWR-debug/trading-agent-public Q221 award boundary feasibility/1.0"
NAICS_PREFIXES = ["541713", "541714", "541715"]
AWARD_TYPES = ["A", "B", "C", "D"]
WINDOWS = [
    ("2019", "2019-01-01", "2019-12-31"),
    ("2020", "2020-01-01", "2020-12-31"),
    ("2021", "2021-01-01", "2021-12-31"),
    ("2022", "2022-01-01", "2022-12-31"),
    ("2023", "2023-01-01", "2023-12-31"),
    ("2024", "2024-01-01", "2024-12-31"),
    ("2025_partial", "2025-01-01", "2025-09-24"),
]
LIMIT_PER_WINDOW = 50
FIELDS = [
    "Award ID", "Mod", "Recipient Name", "Recipient UEI", "recipient_id",
    "Action Date", "Action Type", "Transaction Amount", "Awarding Agency",
    "Awarding Sub Agency", "Funding Agency", "Funding Sub Agency", "NAICS",
    "PSC", "Award Type", "Transaction Description", "generated_internal_id",
    "internal_id", "Issued Date",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_fingerprint(value: dict[str, Any], field: str = "receipt_fingerprint") -> str:
    payload = dict(value)
    payload.pop(field, None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return sha256(raw)


def verify_vintage_receipt(receipt: dict[str, Any]) -> bool:
    required = (
        receipt.get("candidate_id") == "Q221",
        receipt.get("status") == "Q221_HISTORICAL_POLICY_VINTAGES_RECONSTRUCTED",
        receipt.get("all_target_windows_covered") is True,
        receipt.get("policy_markers_consistent_across_vintages") is True,
        receipt.get("historical_policy_vintages_reconstructed") is True,
        receipt.get("lookahead_used") is False,
        len(str(receipt.get("receipt_fingerprint") or "")) == 64,
        canonical_fingerprint(receipt) == receipt.get("receipt_fingerprint"),
    )
    return all(required)


def default_post(url: str, payload: dict[str, Any]) -> tuple[int, bytes]:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    last = "unknown"
    for attempt in range(4):
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Encoding": "identity",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=50) as response:
                raw = response.read(12_000_001)
                if len(raw) > 12_000_000:
                    raise ValueError("USASPENDING_RESPONSE_EXCEEDS_12MB")
                return int(getattr(response, "status", 200)), raw
        except urllib.error.HTTPError as exc:
            # Keep the public API's bounded validation detail in the receipt so
            # malformed requests can be fixed without blind full-window retries.
            detail = " ".join(exc.read(2000).decode("utf-8", errors="replace").split())[:300]
            last = f"HTTP_{exc.code}:{detail}"
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 3:
                raise RuntimeError(f"USASPENDING_HTTP_{exc.code}:{detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = type(exc).__name__
            if attempt == 3:
                raise RuntimeError(f"USASPENDING_TRANSPORT_{last}") from exc
        time.sleep(min(10.0, 2.0 ** attempt))
    raise RuntimeError(f"USASPENDING_TRANSPORT_FAILED:{last}")


def query_payload(start: str, end: str) -> dict[str, Any]:
    return {
        "filters": {
            "award_type_codes": AWARD_TYPES,
            "time_period": [{"start_date": start, "end_date": end}],
            "naics_codes": {"require": NAICS_PREFIXES},
        },
        "fields": FIELDS,
        "page": 1,
        "limit": LIMIT_PER_WINDOW,
        "sort": "Action Date",
        "order": "asc",
    }


def text_field(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    if isinstance(value, dict):
        return " | ".join(f"{k}={text_field(v)}" for k, v in sorted(value.items()))
    if isinstance(value, list):
        return " | ".join(text_field(v) for v in value)
    return str(value)


def agency_class(row: dict[str, Any]) -> str:
    agency = " ".join(text_field(row.get(k)) for k in ("Awarding Agency", "Awarding Sub Agency", "Funding Agency", "Funding Sub Agency")).upper()
    if "UNITED STATES ARMY CORPS OF ENGINEERS" in agency or "U.S. ARMY CORPS OF ENGINEERS" in agency or "USACE" in agency:
        return "USACE_90_DAY_EXCEPTION_CANDIDATE"
    if "DEPARTMENT OF DEFENSE" in agency or "DEPARTMENT OF THE AIR FORCE" in agency or "DEPARTMENT OF THE NAVY" in agency or "DEPARTMENT OF THE ARMY" in agency:
        return "DOD_90_DAY_EXCEPTION_CANDIDATE"
    return "STANDARD_OR_OTHER_AGENCY_CLOCK_CANDIDATE"


def identity_key(row: dict[str, Any]) -> str:
    # USAspending's generated_internal_id/internal_id can repeat across award
    # modifications. Prefer a transaction-level natural key including Mod and
    # Action Date; award-level IDs alone are not unique transaction identities.
    award_id = text_field(row.get("Award ID"))
    mod = text_field(row.get("Mod"))
    action_date = text_field(row.get("Action Date"))
    recipient_id = text_field(row.get("recipient_id"))
    recipient_uei = text_field(row.get("Recipient UEI"))
    if award_id or action_date:
        return "|".join((award_id, mod, action_date, recipient_id, recipient_uei))
    stable = text_field(row.get("generated_internal_id")) or text_field(row.get("internal_id"))
    return stable


def run_gate(
    output: Path,
    policy_receipt: dict[str, Any],
    post: Callable[[str, dict[str, Any]], tuple[int, bytes]] = default_post,
    pause_seconds: float = 0.15,
) -> dict[str, Any]:
    policy_valid = verify_vintage_receipt(policy_receipt)
    queries: list[dict[str, Any]] = []
    query_failures: list[dict[str, str]] = []
    transactions_by_id: dict[str, dict[str, Any]] = {}
    if policy_valid:
        for label, start, end in WINDOWS:
            payload = query_payload(start, end)
            request_fingerprint = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
            try:
                status, raw = post(ENDPOINT, payload)
                parsed = json.loads(raw.decode("utf-8"))
                rows = parsed.get("results")
                if status != 200 or not isinstance(rows, list):
                    raise ValueError(f"INVALID_API_RESPONSE:status={status}:results_type={type(rows).__name__}")
                if not isinstance(parsed.get("page_metadata"), dict):
                    raise ValueError("USASPENDING_PAGE_METADATA_MISSING")
                row_ids: list[str] = []
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    stable_id = identity_key(row)
                    if not stable_id.strip("|"):
                        query_failures.append({"window": label, "error": "ROW_WITHOUT_STABLE_TRANSACTION_ID"})
                        continue
                    row_ids.append(stable_id)
                    transaction = {
                        "transaction_key": stable_id,
                        "window": label,
                        "award_id": text_field(row.get("Award ID")),
                        "modification": text_field(row.get("Mod")),
                        "action_date": text_field(row.get("Action Date")),
                        "action_type": text_field(row.get("Action Type")),
                        "award_type": text_field(row.get("Award Type")),
                        "naics": text_field(row.get("NAICS")),
                        "psc": text_field(row.get("PSC")),
                        "transaction_amount": text_field(row.get("Transaction Amount")),
                        "recipient_name": text_field(row.get("Recipient Name")),
                        "recipient_uei": text_field(row.get("Recipient UEI")),
                        "recipient_id": text_field(row.get("recipient_id")),
                        "awarding_agency": text_field(row.get("Awarding Agency")),
                        "awarding_sub_agency": text_field(row.get("Awarding Sub Agency")),
                        "funding_agency": text_field(row.get("Funding Agency")),
                        "funding_sub_agency": text_field(row.get("Funding Sub Agency")),
                        "issued_date": text_field(row.get("Issued Date")),
                        "last_modified_date": text_field(row.get("Last Modified Date")),
                        "generated_internal_id": text_field(row.get("generated_internal_id")),
                        "internal_id": text_field(row.get("internal_id")),
                        "agency_exception_class": agency_class(row),
                        "far_30_day_exception_status": "APPLICABILITY_UNPROVEN_REQUIRES_CONTRACT_TYPE_AND_HISTORICAL_AUTHORITY",
                        "historical_first_public_observation": None,
                        "historical_public_boundary_status": "NOT_EXPOSED_BY_CURRENT_SEARCH_RESPONSE",
                        "recipient_to_issuer_status": "UNMAPPED_NO_FROZEN_PRE_EVENT_IDENTITY_RECEIPT",
                        "issuer_symbol": None,
                        "mapping_authority": None,
                    }
                    existing = transactions_by_id.get(stable_id)
                    if existing is not None and existing.get("action_date") != transaction.get("action_date"):
                        query_failures.append({"window": label, "error": f"IDENTITY_COLLISION:{stable_id}"})
                        continue
                    transactions_by_id[stable_id] = transaction
                metadata = parsed.get("page_metadata") or {}
                queries.append({
                    "window": label,
                    "start_date": start,
                    "end_date": end,
                    "endpoint": ENDPOINT,
                    "request_fingerprint": request_fingerprint,
                    "http_status": status,
                    "response_sha256": sha256(raw),
                    "response_bytes": len(raw),
                    "result_count": len(rows),
                    "selected_transaction_keys": sorted(set(row_ids)),
                    "has_next": metadata.get("hasNext"),
                    "last_record_unique_id": metadata.get("last_record_unique_id"),
                    "last_record_sort_value": text_field(metadata.get("last_record_sort_value")),
                    "status": "SOURCE_SAMPLE_CAPTURED",
                })
            except Exception as exc:
                query_failures.append({"window": label, "error": f"{type(exc).__name__}:{exc}"[:500]})
                queries.append({
                    "window": label, "start_date": start, "end_date": end,
                    "endpoint": ENDPOINT, "request_fingerprint": request_fingerprint,
                    "status": "QUERY_FAILED", "error": f"{type(exc).__name__}:{exc}"[:500],
                })
            if pause_seconds > 0:
                time.sleep(pause_seconds)

    transactions = sorted(transactions_by_id.values(), key=lambda x: (x["action_date"], x["transaction_key"]))
    recipient_map: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in transactions:
        identity = (row["recipient_id"], row["recipient_uei"], row["recipient_name"])
        if not any(identity):
            continue
        recipient_map[identity] = {
            "recipient_id": row["recipient_id"],
            "recipient_uei": row["recipient_uei"],
            "recipient_name": row["recipient_name"],
            "observed_transaction_count": sum(1 for x in transactions if (x["recipient_id"], x["recipient_uei"], x["recipient_name"]) == identity),
            "issuer_symbol": None,
            "mapping_status": "UNMAPPED",
            "mapping_source": None,
            "pre_event_identity_provenance": None,
            "reason": "No issuer mapping is inferred from recipient name similarity; freeze only after independently sourced pre-event entity evidence.",
        }

    all_queries_complete = policy_valid and len(queries) == len(WINDOWS) and not query_failures and all(q.get("status") == "SOURCE_SAMPLE_CAPTURED" for q in queries)
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q221_historical_award_public_boundary_falsification",
        "candidate_id": "Q221",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "policy_vintage_receipt_fingerprint": policy_receipt.get("receipt_fingerprint"),
        "policy_vintage_receipt_verified": policy_valid,
        "sampling_contract": {
            "years": [x[0] for x in WINDOWS],
            "windows": [{"label": x[0], "start": x[1], "end": x[2]} for x in WINDOWS],
            "award_type_codes": AWARD_TYPES,
            "naics_require_prefix": NAICS_PREFIXES,
            "sort": ["Action Date", "asc"],
            "page": 1,
            "limit_per_window": LIMIT_PER_WINDOW,
            "selection_rule": "First 50 API transactions per fixed calendar window after ascending Action Date sort; no award-amount sorting and no market outcomes.",
        },
        "endpoint": ENDPOINT,
        "queries": queries,
        "query_failure_count": len(query_failures),
        "query_failures": query_failures,
        "sampled_transaction_count": len(transactions),
        "transactions": transactions,
        "unique_recipient_identity_count": len(recipient_map),
        "recipient_identity_candidates": sorted(recipient_map.values(), key=lambda x: (x["recipient_name"], x["recipient_uei"], x["recipient_id"])),
        "source_sample_complete": all_queries_complete and bool(transactions),
        "historical_policy_vintages_reconstructed": policy_valid,
        "action_date_is_not_public_observation_time": True,
        "last_modified_date_is_not_assumed_to_be_first_public_observation": True,
        "historical_first_public_observation_proven": False,
        "exact_transaction_class_applicability_proven": False,
        "dod_usace_exception_applicability_classified": False,
        "far_30_day_exception_applicability_classified": False,
        "recipient_to_issuer_mapping_frozen": False,
        "revision_lineage_frozen": False,
        "gate_positive": False,
        "status": (
            "Q221_HISTORICAL_AWARD_SAMPLE_CAPTURED_PUBLIC_BOUNDARY_UNPROVEN"
            if all_queries_complete and transactions
            else "Q221_HISTORICAL_AWARD_SOURCE_SAMPLE_BLOCKED"
        ),
        "next_gate": (
            "retrieve a reproducible historical USAspending publication/vintage record for these fixed transaction keys; document applicable award/modification clock and then freeze recipient-to-issuer mapping"
            if all_queries_complete and transactions
            else "repair the fixed-window source query/transport; do not treat incomplete coverage as a negative economic finding"
        ),
        "interpretation": "The current USAspending search API returns transaction/action metadata, not the first public-observation timestamp for each historical transaction. No historical PIT boundary is inferred from Action Date, Issued Date, or Last Modified Date.",
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy-receipt", type=Path, default=VINTAGE_RECEIPT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    policy = json.loads(args.policy_receipt.read_text(encoding="utf-8"))
    result = run_gate(args.output, policy)
    summary = {k: v for k, v in result.items() if k not in {"transactions", "recipient_identity_candidates"}}
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if result["source_sample_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
