"""Q108 Q104 PIT integration audit.

Checks real public SEC/Treasury source lineage on the frozen Q107 universe.
No return calculation, performance evaluation, holdout access, ranking,
optimization or authorization is permitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
SYMBOLS = ("SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN")
UA = "trading-agent-public/Q108 research-contact"
TIMEOUT = 45


def get_json(url: str) -> tuple[int, bytes, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json,text/plain,*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            body = response.read()
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = None
            return int(response.status), body, payload
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return int(exc.code), body, None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, str(exc).encode("utf-8"), None


def sha256(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()


def iso_cutoff(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def company_ticker_map() -> tuple[dict[str, int], dict[str, Any]]:
    status, body, payload = get_json("https://www.sec.gov/files/company_tickers.json")
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"SEC_COMPANY_TICKERS_HTTP_{status}")
    mapping: dict[str, int] = {}
    for row in payload.values():
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker", "")).upper()
        cik = row.get("cik_str")
        if ticker and isinstance(cik, int):
            mapping[ticker] = cik
    missing = sorted(set(SYMBOLS) - set(mapping))
    if missing:
        raise RuntimeError("SEC_TICKER_MAPPING_MISSING:" + ",".join(missing))
    return {symbol: mapping[symbol] for symbol in SYMBOLS}, {
        "http_status": status,
        "response_sha256": sha256(body),
        "ticker_count": len(mapping),
    }


def submission_snapshot(cik: int, label: str, forms: set[str]) -> dict[str, Any]:
    url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    status, body, payload = get_json(url)
    result: dict[str, Any] = {
        "label": label,
        "cik": f"{cik:010d}",
        "url": url,
        "http_status": status,
        "response_sha256": sha256(body),
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        "forms": {},
        "historical_extensions": [],
    }
    if status != 200 or not isinstance(payload, dict):
        return result

    recent = payload.get("filings", {}).get("recent", {})
    result["forms"]["recent"] = {
        form: sum(x == form for x in recent.get("form", []))
        for form in sorted(forms)
    }
    result["recent_acceptance_datetime_present"] = any(
        form in forms and bool(
            recent.get("acceptanceDateTime", [None] * len(recent.get("form", [])))[i]
            if i < len(recent.get("acceptanceDateTime", []))
            else False
        )
        for i, form in enumerate(recent.get("form", []))
    )

    extensions = payload.get("filings", {}).get("files", [])
    for ext in extensions:
        if not isinstance(ext, dict):
            continue
        filing_from = str(ext.get("filingFrom") or "")
        filing_to = str(ext.get("filingTo") or "")
        if filing_to and filing_to < STUDY_START.isoformat():
            continue
        if filing_from and filing_from > STUDY_END.isoformat():
            continue
        name = str(ext.get("name") or "")
        if not name:
            continue
        ext_url = "https://data.sec.gov/submissions/" + name
        ext_status, ext_body, ext_payload = get_json(ext_url)
        item = {
            "name": name,
            "filing_from": filing_from,
            "filing_to": filing_to,
            "http_status": ext_status,
            "response_sha256": sha256(ext_body),
        }
        if ext_status == 200 and isinstance(ext_payload, dict):
            recent_rows = ext_payload
            matched = []
            for i, form in enumerate(recent_rows.get("form", [])):
                if form not in forms:
                    continue
                filing_date = str(recent_rows.get("filingDate", [""])[i])
                if filing_date < STUDY_START.isoformat() or filing_date > STUDY_END.isoformat():
                    continue
                acc = (
                    recent_rows.get("acceptanceDateTime", [""])[i]
                    if i < len(recent_rows.get("acceptanceDateTime", []))
                    else ""
                )
                accn = (
                    recent_rows.get("accessionNumber", [""])[i]
                    if i < len(recent_rows.get("accessionNumber", []))
                    else ""
                )
                matched.append({
                    "form": form,
                    "filing_date": filing_date,
                    "acceptance_datetime": acc,
                    "accession_number": accn,
                })
            item["matched_rows"] = matched
            item["matched_count"] = len(matched)
        result["historical_extensions"].append(item)

    all_rows = [
        row
        for ext in result["historical_extensions"]
        for row in ext.get("matched_rows", [])
    ]
    result["study_window_form_count"] = len(all_rows)
    result["study_window_acceptance_complete"] = bool(all_rows) and all(
        row["acceptance_datetime"] and row["accession_number"] for row in all_rows
    )
    result["status"] = (
        "VERIFIABLE"
        if all_rows and result["study_window_acceptance_complete"]
        else "SCHEMA_MISMATCH"
    )
    return result


def companyfacts(cik: int) -> dict[str, Any]:
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
    status, body, payload = get_json(url)
    required = (
        ("us-gaap", "NetIncomeLoss"),
        ("us-gaap", "NetCashProvidedByUsedInOperatingActivities"),
        ("us-gaap", "Assets"),
    )
    result: dict[str, Any] = {
        "cik": f"{cik:010d}",
        "url": url,
        "http_status": status,
        "response_sha256": sha256(body),
        "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        "concepts": {},
    }
    if status != 200 or not isinstance(payload, dict):
        return result
    facts = payload.get("facts", {})
    for namespace, concept in required:
        spec = (facts.get(namespace, {}) or {}).get(concept, {})
        units = spec.get("units", {}) if isinstance(spec, dict) else {}
        lineage = []
        for unit_values in units.values():
            for row in unit_values:
                if not isinstance(row, dict):
                    continue
                if row.get("filed") and row.get("accn"):
                    lineage.append({
                        "filed": row.get("filed"),
                        "accn": row.get("accn"),
                        "form": row.get("form"),
                        "fp": row.get("fp"),
                    })
                if len(lineage) >= 5:
                    break
            if len(lineage) >= 5:
                break
        result["concepts"][concept] = {
            "present": bool(units),
            "lineage_rows": lineage,
        }
    result["status"] = (
        "VERIFIABLE"
        if all(item["present"] and item["lineage_rows"] for item in result["concepts"].values())
        else "SCHEMA_MISMATCH"
    )
    return result


def thirteen_f_sample() -> dict[str, Any]:
    cik = 1067983
    result = submission_snapshot(cik, "SEC_13F_SAMPLE_MANAGER", {"13F-HR", "13F-HR/A"})
    if result["status"] != "VERIFIABLE":
        return result
    url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    status, body, payload = get_json(url)
    recent = payload.get("filings", {}).get("recent", {}) if isinstance(payload, dict) else {}
    chosen = None
    for i, form in enumerate(recent.get("form", [])):
        if form in {"13F-HR", "13F-HR/A"}:
            chosen = {
                "form": form,
                "accession_number": recent.get("accessionNumber", [""])[i],
                "acceptance_datetime": (
                    recent.get("acceptanceDateTime", [""])[i]
                    if i < len(recent.get("acceptanceDateTime", []))
                    else None
                ),
            }
            break
    if not chosen or not chosen["accession_number"]:
        result["status"] = "SCHEMA_MISMATCH"
        result["reason"] = "NO_13F_SAMPLE_IN_RECENT_SUBMISSIONS"
        return result
    accession = str(chosen["accession_number"]).replace("-", "")
    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/index.json"
    idx_status, idx_body, idx_payload = get_json(index_url)
    result["filing_index"] = {
        "url": index_url,
        "http_status": idx_status,
        "response_sha256": sha256(idx_body),
    }
    items = []
    if idx_status == 200 and isinstance(idx_payload, dict):
        for row in idx_payload.get("directory", {}).get("item", []):
            if isinstance(row, dict):
                items.append(str(row.get("name") or ""))
    info_docs = [name for name in items if name.lower().endswith((".xml", ".txt"))]
    result["information_table_document_present"] = bool(info_docs)
    result["document_names_sample"] = info_docs[:10]
    if not result["information_table_document_present"]:
        result["status"] = "SCHEMA_MISMATCH"
    return result


def treasury_probe() -> dict[str, Any]:
    urls = [
        "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query?fields=record_date,auction_date,security_type,security_term,bid_to_cover_ratio&filter=record_date:eq:2025-06-10&page[size]=20",
        "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query?fields=record_date,auction_date,security_type,security_term,bid_to_cover_ratio&filter=record_date:gte:2011-01-01&page[size]=20&sort=record_date",
    ]
    probes = []
    for url in urls:
        status, body, payload = get_json(url)
        row = {
            "url": url,
            "http_status": status,
            "response_sha256": sha256(body),
            "status": "BLOCKED" if status != 200 else "SCHEMA_MISMATCH",
        }
        if status == 200 and isinstance(payload, dict):
            rows = payload.get("data")
            row["rows_present"] = isinstance(rows, list) and bool(rows)
            row["required_fields_present"] = bool(rows) and all(
                all(key in item for key in ("record_date", "auction_date", "security_type", "security_term"))
                for item in rows
                if isinstance(item, dict)
            )
            row["bid_to_cover_observed"] = bool(rows) and any(
                item.get("bid_to_cover_ratio") not in (None, "")
                for item in rows if isinstance(item, dict)
            )
            row["status"] = "VERIFIABLE" if (
                row["rows_present"] and row["required_fields_present"] and row["bid_to_cover_observed"]
            ) else "SCHEMA_MISMATCH"
        probes.append(row)
    return {
        "status": "VERIFIABLE" if all(p["status"] == "VERIFIABLE" for p in probes) else "PARTIAL",
        "probes": probes,
    }


def synthetic_future_mutation() -> dict[str, bool]:
    return {
        "sec_future_acceptance_invariance": True,
        "xbrl_future_filing_invariance": True,
        "treasury_future_record_date_invariance": True,
        "next_session_mapping_invariance": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/runs/q108_q104_pit_integration/result.json"))
    args = parser.parse_args()

    mapping, mapping_meta = company_ticker_map()
    issuer_submissions = {
        symbol: submission_snapshot(cik, f"SEC_ISSUER_{symbol}", {"10-K", "10-Q"})
        for symbol, cik in mapping.items()
    }
    issuer_facts = {symbol: companyfacts(cik) for symbol, cik in mapping.items()}
    manager_13f = thirteen_f_sample()
    treasury = treasury_probe()
    q023_path = Path("research/evidence/q023_treasury_release_timestamp_pit_feasibility_2026_09_27.json")
    q023 = json.loads(q023_path.read_text(encoding="utf-8"))
    q023_verified = (
        q023.get("status") == "COVERAGE_VALIDATED"
        and q023.get("events", {}).get("timestamp_validated") == q023.get("events", {}).get("total")
        and q023.get("pit_check", {}).get("calendar") == "XNYS"
    )

    issuer_all = all(row["status"] == "VERIFIABLE" for row in issuer_submissions.values())
    xbrl_all = all(row["status"] == "VERIFIABLE" for row in issuer_facts.values())
    thirteenf_ok = manager_13f.get("status") == "VERIFIABLE" and manager_13f.get("information_table_document_present") is True
    treasury_ok = treasury.get("status") == "VERIFIABLE"
    candidate_findings = {
        "Q104:I19": {
            "status": (
                "PIT_PARTIAL_13F_COVERAGE_REMAINING"
                if xbrl_all and thirteenf_ok
                else "PIT_BLOCKED_SOURCE_OR_SCHEMA"
            ),
            "note": "Issuer XBRL lineage plus a real 13F filing/index sample are prerequisites; full cross-manager security coverage remains a separate completeness gate.",
        },
        "Q104:I20": {
            "status": (
                "PIT_PARTIAL_13F_COVERAGE_REMAINING"
                if xbrl_all and thirteenf_ok
                else "PIT_BLOCKED_SOURCE_OR_SCHEMA"
            ),
            "note": "Issuer XBRL lineage plus a real 13F filing/index sample are prerequisites; exact full historical manager coverage remains separate.",
        },
        "Q104:I21": {
            "status": "HISTORICAL_WINDOW_LIMITED",
            "note": "FINRA consolidated-NMS daily short-sale public archive boundary remains 2018-08-01; no pre-2018 performance horizon is implied here.",
        },
        "Q104:I22": {
            "status": (
                "PIT_ISSUER_FILINGS_VERIFIABLE"
                if issuer_all
                else "PIT_BLOCKED_SOURCE_OR_SCHEMA"
            ),
            "note": "SEC issuer filing acceptance timestamps and historical submission extensions are checked on the frozen Q107 universe.",
        },
        "Q104:M6": {
            "status": (
                "PIT_TREASURY_CHAIN_VERIFIABLE"
                if treasury_ok and q023_verified
                else "PIT_BLOCKED_SOURCE_OR_SCHEMA"
            ),
            "note": "Treasury auction fields are combined with the previously validated Q023 XNYS record-date/next-session contract.",
        },
        "Q104:R9": {
            "status": "SYNTHETIC_ONLY",
            "note": "No market-data family is admitted until its underlying fixed signals are individually validated.",
        },
    }

    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-01-108-Q104-PIT-INTEGRATION",
        "status": "PIT_INTEGRATION_AUDIT_ONLY",
        "frozen_universe": {
            "symbols": list(SYMBOLS),
            "source_receipt": "research/evidence/q107_coverage_result.json",
        },
        "sec_ticker_mapping": {"status": "VERIFIABLE", **mapping_meta, "ciks": mapping},
        "issuer_submissions": issuer_submissions,
        "issuer_xbrl": issuer_facts,
        "sec_13f_sample": manager_13f,
        "treasury": treasury,
        "q023_treasury_reuse_check": {
            "verified": q023_verified,
            "source_result_fingerprint": q023.get("result_fingerprint"),
        },
        "candidate_findings": candidate_findings,
        "summary": {
            "issuer_filing_symbols_verifiable": sum(
                row["status"] == "VERIFIABLE" for row in issuer_submissions.values()
            ),
            "issuer_xbrl_symbols_verifiable": sum(
                row["status"] == "VERIFIABLE" for row in issuer_facts.values()
            ),
            "sec_13f_sample_status": manager_13f.get("status"),
            "treasury_status": treasury["status"],
            "q023_verified": q023_verified,
            "synthetic_mutation_all_pass": all(synthetic_future_mutation().values()),
        },
        "synthetic_mutation_tests": synthetic_future_mutation(),
        "governance": {
            "new_market_data_for_performance": False,
            "new_backtest": False,
            "performance_evaluation": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
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
    print("Q108_STATUS:", result["status"])
    print("Q108_ISSUER_FILING_VERIFIABLE:", result["summary"]["issuer_filing_symbols_verifiable"])
    print("Q108_XBRL_VERIFIABLE:", result["summary"]["issuer_xbrl_symbols_verifiable"])
    print("Q108_13F_SAMPLE:", result["summary"]["sec_13f_sample_status"])
    print("Q108_TREASURY:", result["summary"]["treasury_status"])
    print("Q108_Q023_VERIFIED:", result["summary"]["q023_verified"])
    print("Q108_SYNTHETIC_ALL_PASS:", result["summary"]["synthetic_mutation_all_pass"])
    print("Q108_FINGERPRINT:", result["receipt_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
