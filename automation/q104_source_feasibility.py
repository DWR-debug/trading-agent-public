"""Q104 source feasibility and public-data channel audit.

This stage probes only source accessibility/schema/PIT metadata. It performs
no return calculation, performance evaluation, ranking, optimization, holdout
selection, or authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

TIMEOUT = 30
UA = "trading-agent-public/Q104-source-feasibility contact=research"


def get(url: str) -> tuple[int, bytes, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            return int(response.status), response.read(), response.headers.get("content-type")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(), None
    except (urllib.error.URLError, TimeoutError, ConnectionResetError, OSError):
        return 599, b"", None


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sec_submission_probe(label: str, cik: str, target_forms: set[str]) -> dict[str, Any]:
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    status, body, content_type = get(url)
    result: dict[str, Any] = {
        "id": f"SEC_{label}",
        "url": url,
        "http_status": status,
        "content_type": content_type,
        "response_sha256": sha256(body),
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        "checks": {},
    }
    if status != 200:
        result["reason"] = f"HTTP_{status}"
        return result
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        result["reason"] = "INVALID_JSON"
        return result

    recent = payload.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    acceptance = recent.get("acceptanceDateTime", [])
    accessions = recent.get("accessionNumber", [])
    n = min(len(forms), len(dates), len(accessions))
    rows = [
        {
            "form": forms[i],
            "filingDate": dates[i],
            "acceptanceDateTime": acceptance[i] if i < len(acceptance) else None,
            "accessionNumber": accessions[i],
        }
        for i in range(n)
    ]
    matched = [r for r in rows if r["form"] in target_forms]
    result["checks"] = {
        "valid_json": True,
        "recent_filings_present": bool(rows),
        "target_forms_present": bool(matched),
        "acceptance_datetime_present": bool(matched) and all(r["acceptanceDateTime"] for r in matched[:5]),
        "accession_numbers_present": bool(matched) and all(r["accessionNumber"] for r in matched[:5]),
    }
    result["target_form_counts"] = {
        form: sum(r["form"] == form for r in rows) for form in sorted(target_forms)
    }
    result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"
    return result


def sec_companyfacts_probe(cik: str) -> dict[str, Any]:
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    status, body, content_type = get(url)
    result: dict[str, Any] = {
        "id": "SEC_COMPANYFACTS",
        "url": url,
        "http_status": status,
        "content_type": content_type,
        "response_sha256": sha256(body),
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        "checks": {},
    }
    if status != 200:
        result["reason"] = f"HTTP_{status}"
        return result
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        result["reason"] = "INVALID_JSON"
        return result
    dei = payload.get("facts", {}).get("dei", {})
    shares = dei.get("EntityCommonStockSharesOutstanding", {}).get("units", {})
    result["checks"] = {
        "valid_json": True,
        "entity_name": bool(payload.get("entityName")),
        "dei_namespace": bool(dei),
        "shares_outstanding_fact": bool(shares),
        "instant_values": any(bool(values) for values in shares.values()),
    }
    result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"
    return result


def page_probe(label: str, url: str, required: list[str]) -> dict[str, Any]:
    status, body, content_type = get(url)
    text = body.decode("utf-8", "replace")
    checks = {term: term.lower() in text.lower() for term in required}
    result = {
        "id": label,
        "url": url,
        "http_status": status,
        "content_type": content_type,
        "response_bytes": len(body),
        "response_sha256": sha256(body),
        "checks": checks,
        "status": "VERIFIABLE" if status == 200 and checks and all(checks.values()) else "SCHEMA_MISMATCH",
    }
    if status != 200:
        result["reason"] = f"HTTP_{status}"
        result["status"] = "BLOCKED"
    return result


def treasury_probe() -> dict[str, Any]:
    url = (
        "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"
        "v1/accounting/od/auctions_query?"
        "fields=record_date,auction_date,security_type,security_term,"
        "bid_to_cover_ratio,total_accepted,total_tendered"
        "&sort=-record_date&page[size]=5"
    )
    status, body, content_type = get(url)
    result: dict[str, Any] = {
        "id": "TREASURY_AUCTIONS_API",
        "url": url,
        "http_status": status,
        "content_type": content_type,
        "response_sha256": sha256(body),
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        "checks": {},
    }
    if status != 200:
        result["reason"] = f"HTTP_{status}"
        return result
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        result["reason"] = "INVALID_JSON"
        return result
    rows = payload.get("data")
    result["checks"] = {
        "valid_json": True,
        "data_rows_present": isinstance(rows, list) and bool(rows),
        "record_date_present": bool(rows) and all(r.get("record_date") for r in rows if isinstance(r, dict)),
        "auction_date_present": bool(rows) and all(r.get("auction_date") for r in rows if isinstance(r, dict)),
        "bid_to_cover_available": bool(rows) and any(r.get("bid_to_cover_ratio") not in (None, "") for r in rows if isinstance(r, dict)),
        "accepted_available": bool(rows) and any(r.get("total_accepted") not in (None, "") for r in rows if isinstance(r, dict)),
        "tendered_available": bool(rows) and any(r.get("total_tendered") not in (None, "") for r in rows if isinstance(r, dict)),
    }
    result["sample_rows"] = rows[:3] if isinstance(rows, list) else []
    result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"
    return result


def candidate_matrix(probes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    def status(*ids: str) -> str:
        values = [probes[i]["status"] for i in ids]
        return "SOURCE_FEASIBLE" if all(v == "VERIFIABLE" for v in values) else "SOURCE_BLOCKED_OR_INCOMPLETE"

    return [
        {
            "id": "Q104:I19",
            "name": "Institutional Demand × Accrual State",
            "required_source_probes": ["SEC_13F", "SEC_COMPANYFACTS"],
            "source_status": status("SEC_13F", "SEC_COMPANYFACTS"),
            "next_gate": "historical 13F archive completeness + PIT XBRL fact selection + mutation tests",
            "performance_authorized": False,
        },
        {
            "id": "Q104:I20",
            "name": "Institutional Demand × Fundamental-Change Surprise",
            "required_source_probes": ["SEC_13F", "SEC_COMPANYFACTS"],
            "source_status": status("SEC_13F", "SEC_COMPANYFACTS"),
            "next_gate": "historical 13F archive completeness + exact XBRL concept freeze + acceptance-time PIT",
            "performance_authorized": False,
        },
        {
            "id": "Q104:I21",
            "name": "Short-Flow Triangulation State",
            "required_source_probes": ["SEC_FTD", "FINRA_SHORT_INTEREST", "FINRA_REGSHO"],
            "source_status": status("SEC_FTD", "FINRA_SHORT_INTEREST", "FINRA_REGSHO"),
            "next_gate": "publication-time alignment + security mapping + cross-source missingness contract",
            "performance_authorized": False,
        },
        {
            "id": "Q104:I22",
            "name": "Filing Arrival Density × Delayed Price Response",
            "required_source_probes": ["SEC_SUBMISSIONS"],
            "source_status": status("SEC_SUBMISSIONS"),
            "next_gate": "historical filing archive/entity mapping + event-order mutation tests",
            "performance_authorized": False,
        },
        {
            "id": "Q104:M6",
            "name": "Treasury Auction Demand Shock",
            "required_source_probes": ["TREASURY_AUCTIONS_API"],
            "source_status": status("TREASURY_AUCTIONS_API"),
            "next_gate": "historical archive depth + publication-time/record-date semantics + field freeze",
            "performance_authorized": False,
        },
        {
            "id": "Q104:R9",
            "name": "Cross-Family Consensus Reliability State",
            "required_source_probes": [],
            "source_status": "SYNTHETIC_ONLY",
            "next_gate": "family-definition freeze + synthetic state-routing PIT integrity",
            "performance_authorized": False,
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/runs/q104_source_feasibility/result.json"))
    args = parser.parse_args()

    probes_list = [
        sec_submission_probe("13F", "0001067983", {"13F-HR", "13F-HR/A"}),
        sec_submission_probe("SUBMISSIONS", "0000320193", {"10-K", "10-Q"}),
        sec_submission_probe("FORM4", "0000789019", {"4", "4/A"}),
        sec_companyfacts_probe("0000320193"),
        page_probe(
            "SEC_FTD",
            "https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data",
            ["February 2004", "fails-to-deliver"],
        ),
        page_probe(
            "FINRA_SHORT_INTEREST",
            "https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest",
            ["Short Interest Reporting", "reporting dates"],
        ),
        page_probe(
            "FINRA_REGSHO",
            "https://developer.finra.org/docs/api-explorer/query_api-equity-reg_sho_daily_short_sale_volume",
            ["Reg SHO", "short sale"],
        ),
        treasury_probe(),
    ]
    probes = {row["id"]: row for row in probes_list}
    matrix = candidate_matrix(probes)
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-01-104-SOURCE-FEASIBILITY",
        "status": "SOURCE_FEASIBILITY_ONLY",
        "probe_count": len(probes_list),
        "probes": probes_list,
        "candidate_matrix": matrix,
        "summary": {
            "source_feasible_count": sum(row["source_status"] == "SOURCE_FEASIBLE" for row in matrix),
            "source_incomplete_count": sum(row["source_status"] not in {"SOURCE_FEASIBLE", "SYNTHETIC_ONLY"} for row in matrix),
            "synthetic_only_count": sum(row["source_status"] == "SYNTHETIC_ONLY" for row in matrix),
        },
        "governance": {
            "new_market_data_for_performance": False,
            "new_backtest": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "performance_authorization": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q104_STATUS:", result["status"])
    print("Q104_SOURCE_FEASIBLE:", result["summary"]["source_feasible_count"])
    print("Q104_SOURCE_INCOMPLETE:", result["summary"]["source_incomplete_count"])
    print("Q104_SYNTHETIC_ONLY:", result["summary"]["synthetic_only_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
