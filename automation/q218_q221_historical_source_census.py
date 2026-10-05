"""Historical source-census gates for Q218-Q221.

The census is deliberately discovery/PIT infrastructure only. It does not read
market outcomes, rank candidates, optimize parameters, or authorize performance.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SEC_CIKS = {
    "AAPL": "320193",
    "MSFT": "789019",
    "AMZN": "1018724",
    "JPM": "19617",
    "XOM": "34088",
    "NVDA": "1045810",
    "WMT": "104169",
    "DIS": "1744489",
}
FIXED_START = "2025-01-01"
FIXED_END = "2026-10-05"
SEC_HEADERS = {"User-Agent": "TradingAgent-Public-Research/1.0 research@example.invalid"}
USA_RDTNE_URL = "https://www.usaspending.gov/award/CONT_AWD_N0003019F5005_9700_N0003017G0050_9700/"
SEC_NOTES_URL = "https://www.sec.gov/files/dera/data/financial-statement-notes-data-sets/2009q1_notes.zip"


def fetch(url: str, limit: int | None = 1000000) -> tuple[int, str, bytes]:
    request = urllib.request.Request(url, headers=SEC_HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read(limit) if limit is not None else response.read()
        return int(getattr(response, "status", 200)), response.headers.get("Content-Type", ""), body


def sec_submission_census() -> dict:
    issuer_results = {}
    for symbol, cik in SEC_CIKS.items():
        status, content_type, body = fetch(f"https://data.sec.gov/submissions/CIK{cik}.json", None)
        data = json.loads(body.decode("utf-8"))
        recent = data.get("filings", {}).get("recent", {})
        rows = []
        for i, form in enumerate(recent.get("form", [])):
            if form not in {"10-K", "8-K"}:
                continue
            filing_date = recent.get("filingDate", [None])[i]
            if not filing_date or not (FIXED_START <= filing_date <= FIXED_END):
                continue
            accession = recent["accessionNumber"][i]
            primary = recent["primaryDocument"][i]
            index_headers = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                f"{accession.replace('-', '')}/{accession}-index-headers.html"
            )
            try:
                _, _, page = fetch(index_headers, None)
                text = page.decode("utf-8", errors="replace")
                acceptance = re.findall(r"<ACCEPTANCE-DATETIME>\s*([0-9]{14})", text, flags=re.I)
                exhibit_991 = bool(re.search(r"EXHIBIT\s+99\.1", text, flags=re.I))
                earnings_release = bool(re.search(r"EARNINGS\s+RELEASE", text, flags=re.I))
                rows.append({
                    "form": form,
                    "filing_date": filing_date,
                    "accession": accession,
                    "primary_document": primary,
                    "report_date": (recent.get("reportDate", [None])[i] if i < len(recent.get("reportDate", [])) else None),
                    "index_headers_url": index_headers,
                    "acceptance_datetime_found": bool(acceptance),
                    "acceptance_datetime": acceptance[0] if acceptance else None,
                    "exhibit_99_1": exhibit_991,
                    "earnings_release_marker": earnings_release,
                })
            except Exception as exc:
                rows.append({
                    "form": form,
                    "filing_date": filing_date,
                    "accession": accession,
                    "primary_document": primary,
                    "report_date": (recent.get("reportDate", [None])[i] if i < len(recent.get("reportDate", [])) else None),
                    "index_headers_url": index_headers,
                    "error": type(exc).__name__ + ":" + str(exc),
                })
        annual = [r for r in rows if r["form"] == "10-K"]
        voluntary = [r for r in rows if r["form"] == "8-K" and r.get("exhibit_99_1") and r.get("earnings_release_marker")]
        annual_dates = {r.get("report_date") for r in annual if r.get("report_date")}
        matched_dates = sorted({r.get("report_date") for r in voluntary if r.get("report_date") in annual_dates})
        issuer_results[symbol] = {
            "cik": cik,
            "status": status,
            "content_type": content_type,
            "window_row_count": len(rows),
            "annual_10k_count": len(annual),
            "earnings_release_8k_count": len(voluntary),
            "same_report_date_pair_count": len(matched_dates),
            "matched_report_dates": matched_dates[:8],
            "latest_10k": annual[0] if annual else None,
            "latest_8k_earnings_release": voluntary[0] if voluntary else None,
            "pairability_observed": bool(matched_dates),
        }
    return {
        "fixed_window": {"start": FIXED_START, "end": FIXED_END},
        "issuer_count": len(issuer_results),
        "issuer_results": issuer_results,
        "pairable_issuer_count": sum(int(x["pairability_observed"]) for x in issuer_results.values()),
    }


def sec_notes_census() -> dict:
    status, content_type, body = fetch(SEC_NOTES_URL, None)
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        names = archive.namelist()
    lower = {name.lower() for name in names}
    required_markers = ["sub.txt", "tag.txt", "dim.txt", "num.txt", "txt.txt"]
    return {
        "status": status,
        "content_type": content_type,
        "archive_sha256": hashlib.sha256(body).hexdigest(),
        "archive_bytes": len(body),
        "zip_parse_ok": True,
        "required_member_markers_present": {marker: marker in lower for marker in required_markers},
        "member_count": len(names),
        "members_sample": names[:20],
    }


def usa_rdtne_census() -> dict:
    status, content_type, body = fetch(USA_RDTNE_URL, None)
    text = body.decode("utf-8", errors="replace")
    upper = re.sub(r"\s+", " ", text).upper()
    return {
        "status": status,
        "content_type": content_type,
        "content_sha256": hashlib.sha256(body).hexdigest(),
        "content_bytes": len(body),
        "rdtne_marker_found": "RESEARCH DEVELOPMENT TEST AND EVALUATION" in upper,
        "competition_marker_found": "COMPETITION" in upper,
        "transaction_marker_found": "TRANSACTION" in upper or "MODIFICATION" in upper,
        "lookahead_used": False,
    }


def q129_contract_check(repo_root: Path) -> dict:
    contract = repo_root / "research/governance/q129_options_source_contract_2026_10_03.json"
    receipt = repo_root / "research/evidence/q129_independent_pit_2026_10_03.json"
    return {
        "contract_present": contract.is_file(),
        "independent_pit_receipt_present": receipt.is_file(),
        "same_day_use_allowed": False,
    }


def run(output: Path) -> dict:
    result = {
        "schema_version": 1,
        "record_type": "q218_q221_historical_source_census",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixed_control_window": {"start": FIXED_START, "end": FIXED_END},
        "candidate_ids": ["Q218", "Q219", "Q220", "Q221"],
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "q218_sec_pair_census": sec_submission_census(),
        "q219_q129_contract": q129_contract_check(Path.cwd()),
        "q220_sec_notes_census": sec_notes_census(),
        "q221_usa_rdtne_census": usa_rdtne_census(),
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    result["receipt_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
