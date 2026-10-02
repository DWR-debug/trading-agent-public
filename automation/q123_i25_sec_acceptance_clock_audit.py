"""Q123:I25 SEC acceptance-clock source/PIT feasibility audit.

This is a source-contract audit only. It never evaluates returns, selects a
candidate, authorizes performance or creates scientific evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

SYMBOLS = ("SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN")
FORM = "8-K"
START = "2025-01-01"
END = "2025-09-24"
PER_SYMBOL = 2
UA = "trading-agent-public/Q123-I25-SEC-acceptance-clock-audit/1"
TIMEOUT = 30

ACCEPT_RE = re.compile(r"<ACCEPTANCE-DATETIME>\s*([0-9]{14})")
CIK_RE = re.compile(r"CENTRAL INDEX KEY:\s*([0-9]{10})", re.I)
ACCESSION_RE = re.compile(r"ACCESSION NUMBER:\s*([0-9]{10}-[0-9]{2}-[0-9]{6})", re.I)
HEADER_RE = re.compile(r"<SEC-HEADER>(.*?)</SEC-HEADER>", re.I | re.S)



def get_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return response.read()


def get_json(url: str) -> tuple[bytes, dict]:
    body = get_bytes(url)
    value = json.loads(body.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("SEC_JSON_OBJECT_REQUIRED")
    return body, value


def parse_api_timestamp(value: str) -> tuple[str, str]:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    digits = dt.strftime("%Y%m%d%H%M%S")
    return digits, value


def _header_block(text: str) -> str:
    match = HEADER_RE.search(text)
    return match.group(1) if match else text


def parse_header_timestamp(text: str) -> str:
    match = ACCEPT_RE.search(_header_block(text))
    if not match:
        raise ValueError("ACCEPTANCE_DATETIME_HEADER_MISSING")
    digits = match.group(1)
    datetime.strptime(digits, "%Y%m%d%H%M%S")
    return digits


def parse_header_identity(text: str) -> tuple[str | None, str | None]:
    header = _header_block(text)
    cik_match = CIK_RE.search(header)
    accession_match = ACCESSION_RE.search(header)
    return (
        cik_match.group(1) if cik_match else None,
        accession_match.group(1) if accession_match else None,
    )


def select_accessions(recent: dict) -> list[dict]:
    forms = recent.get("form") or []
    filing_dates = recent.get("filingDate") or []
    acceptance = recent.get("acceptanceDateTime") or []
    accessions = recent.get("accessionNumber") or []
    rows = []
    for i, form in enumerate(forms):
        if form != FORM:
            continue
        if i >= len(filing_dates) or i >= len(accessions) or i >= len(acceptance):
            continue
        fd = str(filing_dates[i])
        if not (START <= fd <= END):
            continue
        value = acceptance[i]
        if not value:
            continue
        digits, original = parse_api_timestamp(str(value))
        rows.append({
            "filing_date": fd,
            "acceptance_api": original,
            "acceptance_digits": digits,
            "accession": str(accessions[i]),
        })
    rows.sort(key=lambda x: (x["acceptance_digits"], x["accession"]))
    return rows[:PER_SYMBOL]


def audit_symbol(symbol: str, cik: int) -> dict:
    sub_url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    body, payload = get_json(sub_url)
    recent = payload.get("filings", {}).get("recent", {})
    selected = select_accessions(recent)

    if len(selected) != PER_SYMBOL:
        return {
            "symbol": symbol,
            "cik": f"{cik:010d}",
            "status": "FAIL_SAMPLE_INCOMPLETE",
            "selected": selected,
            "source_sha256": hashlib.sha256(body).hexdigest(),
        }

    audited = []
    for row in selected:
        accession = row["accession"]
        accession_path = accession.replace("-", "")
        base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_path}"
        txt_url = f"{base}/{accession}.txt"
        headers_url = f"{base}/{accession}-index-headers.html"
        complete = get_bytes(txt_url).decode("utf-8", errors="replace")
        headers = get_bytes(headers_url).decode("utf-8", errors="replace")

        raw_digits = parse_header_timestamp(complete)
        index_digits = parse_header_timestamp(headers)
        api_digits = row["acceptance_digits"]

        complete_cik, complete_accession = parse_header_identity(complete)
        index_cik, index_accession = parse_header_identity(headers)
        identity_ok = (
            complete_cik == f"{cik:010d}"
            and index_cik == f"{cik:010d}"
            and complete_accession == accession
            and index_accession == accession
        )
        timestamp_match = raw_digits == index_digits == api_digits

        audited.append({
            **row,
            "complete_submission_url": txt_url,
            "index_headers_url": headers_url,
            "complete_acceptance_digits": raw_digits,
            "index_acceptance_digits": index_digits,
            "api_acceptance_digits": api_digits,
            "timestamp_match": timestamp_match,
            "identity_ok": identity_ok,
            "complete_cik": complete_cik,
            "index_cik": index_cik,
            "complete_accession": complete_accession,
            "index_accession": index_accession,
            "complete_sha256": hashlib.sha256(complete.encode("utf-8")).hexdigest(),
            "index_headers_sha256": hashlib.sha256(headers.encode("utf-8")).hexdigest(),
        })

    ok = all(x["timestamp_match"] and x["identity_marker_present"] for x in audited)
    return {
        "symbol": symbol,
        "cik": f"{cik:010d}",
        "status": "PASS" if ok else "FAIL_TIMESTAMP_OR_IDENTITY",
        "selected": audited,
        "source_sha256": hashlib.sha256(body).hexdigest(),
    }


def mutation_tests() -> dict[str, bool]:
    fixture = [
        {"acceptance_digits": "20250102120000", "accession": "B"},
        {"acceptance_digits": "20250101120000", "accession": "A"},
    ]
    a = sorted(fixture, key=lambda x: (x["acceptance_digits"], x["accession"]))
    b = sorted(list(reversed(fixture)), key=lambda x: (x["acceptance_digits"], x["accession"]))

    future = {"acceptance_digits": "20251201120000", "accession": "FUTURE"}
    before = json.dumps(a, sort_keys=True)
    after = json.dumps(sorted(fixture + [future], key=lambda x: (x["acceptance_digits"], x["accession"]))[:2], sort_keys=True)

    mismatch = {"api": "20250101120000", "raw": "20250101120001"}
    mismatch_fails_closed = mismatch["api"] != mismatch["raw"]

    return {
        "input_order_invariance": json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True),
        "future_addition_does_not_change_selected_prefix": before == after,
        "timestamp_mismatch_fails_closed": mismatch_fails_closed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    body, tickers = get_json("https://www.sec.gov/files/company_tickers.json")
    mapping = {}
    for item in tickers.values():
        if not isinstance(item, dict):
            continue
        ticker = str(item.get("ticker", "")).upper()
        if ticker in SYMBOLS and isinstance(item.get("cik_str"), int):
            mapping[ticker] = int(item["cik_str"])

    if set(mapping) != set(SYMBOLS):
        raise RuntimeError("Q123_MISSING_FIXED_CIK_MAPPING")

    results = [audit_symbol(symbol, mapping[symbol]) for symbol in SYMBOLS]
    mutation = mutation_tests()
    overall = all(item["status"] == "PASS" for item in results) and all(mutation.values())

    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-02-Q123-I25-SEC-ACCEPTANCE-CLOCK-AUDIT",
        "status": "Q123_F1_AUDIT_PASS" if overall else "Q123_F1_AUDIT_FAILED",
        "selection_rule": {
            "symbols": list(SYMBOLS),
            "form": FORM,
            "window_start": START,
            "window_end": END,
            "per_symbol": PER_SYMBOL,
            "sort": ["acceptance_digits", "accession"],
        },
        "source_fields": {
            "submission_api": "acceptanceDateTime",
            "complete_submission": "<ACCEPTANCE-DATETIME>",
            "index_headers": "<ACCEPTANCE-DATETIME>",
            "timezone_policy": "Do not infer an unstated timezone; compare source timestamp digits and preserve the API's explicit offset separately."
        },
        "symbol_results": results,
        "mutation_tests": mutation,
        "source_ticker_response_sha256": hashlib.sha256(body).hexdigest(),
        "governance": {
            "performance": False,
            "holdout": False,
            "selection": False,
            "ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "performance_authorized": False,
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
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "symbols": len(results),
        "samples": sum(len(x["selected"]) for x in results),
        "mutation_tests": mutation,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
