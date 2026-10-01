"""Q105 historical archive/PIT feasibility gate for Q104.

Only source history, publication-time semantics, identifier lineage and
synthetic mutation invariants are assessed. No performance/backtest/selection.
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
UA = "trading-agent-public/Q105-historical-pit contact=research"


def get(url: str) -> tuple[int, bytes, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            return int(response.status), response.read(), response.headers.get("content-type")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(), None
    except (urllib.error.URLError, TimeoutError, ConnectionResetError, OSError):
        return 599, b"", None


def fp(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sec_submission_archive_probe(cik: str, forms: set[str], label: str) -> dict[str, Any]:
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    status, body, content_type = get(url)
    result: dict[str, Any] = {
        "id": f"SEC_ARCHIVE_{label}",
        "url": url,
        "http_status": status,
        "content_type": content_type,
        "response_sha256": fp(body),
        "checks": {},
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
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
    rows = [
        {
            "form": form,
            "filingDate": recent.get("filingDate", [])[i],
            "accessionNumber": recent.get("accessionNumber", [])[i],
            "acceptanceDateTime": recent.get("acceptanceDateTime", [])[i]
            if i < len(recent.get("acceptanceDateTime", [])) else None,
        }
        for i, form in enumerate(recent.get("form", []))
        if i < len(recent.get("filingDate", [])) and i < len(recent.get("accessionNumber", []))
    ]
    matching = [r for r in rows if r["form"] in forms]
    extensions = payload.get("filings", {}).get("files", [])
    result["checks"] = {
        "valid_json": True,
        "target_form_recent": bool(matching),
        "acceptance_datetime_present": bool(matching) and all(
            r["acceptanceDateTime"] for r in matching[:5]
        ),
        "accession_present": bool(matching) and all(
            r["accessionNumber"] for r in matching[:5]
        ),
        "historical_extension_metadata": bool(extensions),
    }
    result["extension_count"] = len(extensions)
    if extensions:
        oldest = sorted(
            extensions,
            key=lambda x: str(x.get("filingFrom") or x.get("from") or "")
        )[0]
        result["oldest_extension"] = {
            "name": oldest.get("name"),
            "filingFrom": oldest.get("filingFrom"),
            "filingTo": oldest.get("filingTo"),
        }
    result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"
    return result


def companyfacts_lineage_probe(cik: str) -> dict[str, Any]:
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    status, body, content_type = get(url)
    result: dict[str, Any] = {
        "id": "SEC_COMPANYFACTS_LINEAGE",
        "url": url,
        "http_status": status,
        "content_type": content_type,
        "response_sha256": fp(body),
        "checks": {},
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
    }
    if status != 200:
        result["reason"] = f"HTTP_{status}"
        return result
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        result["reason"] = "INVALID_JSON"
        return result
    found = []
    for namespace, facts in payload.get("facts", {}).items():
        if not isinstance(facts, dict):
            continue
        for concept, spec in facts.items():
            for unit, entries in (spec.get("units") or {}).items():
                for row in entries[:20]:
                    if isinstance(row, dict) and row.get("filed") and row.get("accn"):
                        found.append({
                            "namespace": namespace,
                            "concept": concept,
                            "unit": unit,
                            "filed": row.get("filed"),
                            "accn": row.get("accn"),
                            "form": row.get("form"),
                        })
                        if len(found) >= 10:
                            break
                if len(found) >= 10:
                    break
            if len(found) >= 10:
                break
        if len(found) >= 10:
            break
    result["checks"] = {
        "valid_json": True,
        "fact_lineage_rows_found": len(found) > 0,
        "filed_and_accession_present": bool(found) and all(x["filed"] and x["accn"] for x in found),
    }
    result["sample_lineage_rows"] = found
    result["status"] = "VERIFIABLE" if all(result["checks"].values()) else "SCHEMA_MISMATCH"
    return result


def page_probe(label: str, url: str, checks: list[str]) -> dict[str, Any]:
    status, body, content_type = get(url)
    text = body.decode("utf-8", "replace")
    check_map = {x: x.lower() in text.lower() for x in checks}
    result = {
        "id": label,
        "url": url,
        "http_status": status,
        "content_type": content_type,
        "response_sha256": fp(body),
        "checks": check_map,
        "status": "VERIFIABLE" if status == 200 and check_map and all(check_map.values()) else "SCHEMA_MISMATCH",
    }
    if status != 200:
        result["status"] = "BLOCKED"
        result["reason"] = f"HTTP_{status}"
    return result


def treasury_historical_probe() -> dict[str, Any]:
    urls = [
        "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query?fields=record_date,auction_date,security_type,security_term,bid_to_cover_ratio,total_accepted,total_tendered&sort=-record_date&page[size]=5",
        "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query?fields=record_date,auction_date,security_type,security_term,bid_to_cover_ratio,total_accepted,total_tendered&filter=record_date:eq:2025-06-10&page[size]=5",
    ]
    probes = []
    for url in urls:
        status, body, content_type = get(url)
        row = {
            "url": url,
            "http_status": status,
            "content_type": content_type,
            "response_sha256": fp(body),
            "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
            "checks": {},
        }
        if status == 200:
            try:
                payload = json.loads(body)
                rows = payload.get("data")
                row["checks"] = {
                    "valid_json": True,
                    "rows_present": isinstance(rows, list) and bool(rows),
                    "record_date_present": bool(rows) and all(r.get("record_date") for r in rows),
                    "auction_date_present": bool(rows) and all(r.get("auction_date") for r in rows),
                }
                row["sample_rows"] = rows[:2] if isinstance(rows, list) else []
                row["status"] = "VERIFIABLE" if all(row["checks"].values()) else "SCHEMA_MISMATCH"
            except json.JSONDecodeError:
                row["checks"] = {"valid_json": False}
        else:
            row["reason"] = f"HTTP_{status}"
        probes.append(row)
    return {
        "id": "TREASURY_HISTORICAL_AUCTION_PROBE",
        "status": "VERIFIABLE" if all(p["status"] == "VERIFIABLE" for p in probes) else "PARTIAL",
        "probes": probes,
    }


def synthetic_sec_future_mutation() -> bool:
    filings = [
        {"accepted": "2025-01-10T14:00:00Z", "value": 10},
        {"accepted": "2025-04-10T14:00:00Z", "value": 12},
    ]
    future = {"accepted": "2025-07-10T14:00:00Z", "value": 50}

    def state(rows: list[dict[str, Any]], cutoff: str) -> float | None:
        eligible = [x for x in rows if x["accepted"] <= cutoff]
        return eligible[-1]["value"] if eligible else None

    cutoff = "2025-05-01T00:00:00Z"
    return state(filings, cutoff) == state(filings + [future], cutoff)


def synthetic_multi_source_clock() -> bool:
    sec = {"available": "2025-01-10T15:00:00Z"}
    finra = {"available": "2025-01-10T22:00:00Z"}
    decision = "2025-01-10T20:00:00Z"
    sec_seen = sec["available"] <= decision
    finra_seen = finra["available"] <= decision
    return sec_seen and not finra_seen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/runs/q105_q104_historical_pit/result.json"))
    args = parser.parse_args()

    probes = [
        sec_submission_archive_probe("0001067983", {"13F-HR", "13F-HR/A"}, "13F"),
        sec_submission_archive_probe("0000320193", {"10-K", "10-Q"}, "FILINGS"),
        sec_submission_archive_probe("0000789019", {"4", "4/A"}, "FORM4"),
        companyfacts_lineage_probe("0000320193"),
        page_probe(
            "SEC_FTD_HISTORY",
            "https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data",
            ["February 2004", "September 2026"],
        ),
        page_probe(
            "FINRA_SHORT_INTEREST_HISTORY",
            "https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest",
            ["2026 Short Interest Reporting Dates", "Historical files available for download"],
        ),
        page_probe(
            "FINRA_REGSHO_HISTORY",
            "https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files",
            ["August 1, 2018", "Daily Short Sale Volume Files"],
        ),
    ]
    treasury = treasury_historical_probe()
    synthetic = {
        "sec_future_filing_invariance": synthetic_sec_future_mutation(),
        "cross_source_clock_alignment": synthetic_multi_source_clock(),
    }

    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-01-105-Q104-HISTORICAL-PIT-GATE",
        "status": "HISTORICAL_PIT_FEASIBILITY_ONLY",
        "probes": probes,
        "treasury": treasury,
        "synthetic_mutation_tests": synthetic,
        "candidate_findings": [
            {
                "id": "Q104:I19",
                "status": "PIT_ARCHIVE_GATE_REQUIRED",
                "blocking_issue": "complete 13F archive/security mapping and XBRL concept selection remain unproven on a fresh universe",
            },
            {
                "id": "Q104:I20",
                "status": "PIT_ARCHIVE_GATE_REQUIRED",
                "blocking_issue": "complete 13F archive/security mapping and XBRL concept selection remain unproven on a fresh universe",
            },
            {
                "id": "Q104:I21",
                "status": "PARTIAL_HISTORICAL_WINDOW",
                "blocking_issue": "FINRA Reg SHO public daily files have a documented earliest consolidated NMS date of 2018-08-01; a pre-2018 full-history study would require a separate verified source or a new ex-ante horizon definition",
            },
            {
                "id": "Q104:I22",
                "status": "PIT_ARCHIVE_GATE_REQUIRED",
                "blocking_issue": "SEC historical extension/entity mapping and event-form freeze still need fresh-universe validation",
            },
            {
                "id": "Q104:M6",
                "status": "PIT_ARCHIVE_GATE_REQUIRED",
                "blocking_issue": "Treasury record_date/publication semantics and historical field completeness require frozen validation on the intended study window",
            },
            {
                "id": "Q104:R9",
                "status": "SYNTHETIC_PIT_FEASIBILITY_ONLY",
                "blocking_issue": "requires frozen validated family set before any market-data use",
            },
        ],
        "summary": {
            "source_probes_verifiable": sum(p["status"] == "VERIFIABLE" for p in probes),
            "treasury_status": treasury["status"],
            "synthetic_tests_all_pass": all(synthetic.values()),
        },
        "governance": {
            "new_backtest": False,
            "performance_evaluation": False,
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
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q105_STATUS:", result["status"])
    print("Q105_SOURCE_PROBES_VERIFIABLE:", result["summary"]["source_probes_verifiable"])
    print("Q105_TREASURY_STATUS:", result["summary"]["treasury_status"])
    print("Q105_SYNTHETIC_ALL_PASS:", result["summary"]["synthetic_tests_all_pass"])
    print("Q105_FINGERPRINT:", result["receipt_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
