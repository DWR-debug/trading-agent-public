"""Q018 official-source feasibility preflight.

Coverage-only. This module never computes returns/P&L, never reads a holdout,
never ranks candidates, and never changes the fixed research universe.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
UNIVERSE = "q018_official_event_source_validation"
SYMBOLS = ("UNH", "UPS", "FDX", "DIS", "ADP", "BKNG", "ORLY", "AZO", "TJX", "RSG", "WM", "EOG")

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
SEC_ARCHIVE = "https://data.sec.gov/submissions/{name}"
SEC_HEADERS = {
    "User-Agent": "trading-agent-public research https://github.com/DWR-debug/trading-agent-public",
}
FED_HISTORICAL = "https://www.federalreserve.gov/monetarypolicy/fomchistorical{year}.htm"
FED_CALENDAR = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
TREASURY_API = (
    "https://api.fiscaldata.treasury.gov/services/api/"
    "fiscal_service/v1/accounting/od/auctions_query"
)

class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append((" ".join(self._parts).strip(), self._href))
            self._href = None
            self._parts = []

class FetchError(RuntimeError):
    pass

def _fetch_text(url: str, *, headers: dict[str, str] | None = None, timeout: int = 30) -> str:
    request = Request(url, headers=headers or {})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise FetchError(f"{url}: {exc}") from exc
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FetchError(f"{url}: non-UTF-8 response") from exc

def _fetch_json(url: str, *, headers: dict[str, str] | None = None, timeout: int = 30) -> Any:
    return json.loads(_fetch_text(url, headers=headers, timeout=timeout))

def _fp(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def _date_in_window(value: str) -> bool:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return STUDY_START <= parsed <= STUDY_END

def _sec_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    recent = payload.get("filings", {}).get("recent", {})
    if not recent:
        return []
    size = len(next(iter(recent.values())))
    keys = tuple(recent.keys())
    return [{key: recent[key][i] for key in keys} for i in range(size)]

def _sec_symbol_to_cik() -> dict[str, int]:
    payload = _fetch_json(SEC_TICKERS_URL, headers=SEC_HEADERS)
    mapping: dict[str, int] = {}
    for item in payload.values():
        ticker = str(item.get("ticker", "")).upper()
        if ticker in SYMBOLS:
            mapping[ticker] = int(item["cik_str"])
    return mapping

def _sec_form4_coverage(cik_map: dict[str, int]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    all_ok = True
    for symbol in SYMBOLS:
        if symbol not in cik_map:
            results[symbol] = {"symbol": symbol, "status": "DATA_INSUFFICIENT", "error": "CIK mapping missing"}
            all_ok = False
            continue
        cik = cik_map[symbol]
        try:
            payload = _fetch_json(SEC_SUBMISSIONS.format(cik=cik), headers=SEC_HEADERS)
            filing_meta = payload.get("filings", {})
            archive_specs = [
                item for item in filing_meta.get("files", [])
                if item.get("filingFrom", "9999-12-31") <= STUDY_END.isoformat()
                and item.get("filingTo", "0000-01-01") >= STUDY_START.isoformat()
            ]
            records: dict[str, dict[str, Any]] = {}
            for row in _sec_records(payload):
                acc = row.get("accessionNumber")
                filed = row.get("filingDate")
                if acc and filed and row.get("form") == "4" and _date_in_window(filed):
                    records[acc] = row

            archive_errors: list[str] = []
            for spec in archive_specs:
                try:
                    archived = _fetch_json(SEC_ARCHIVE.format(name=spec["name"]), headers=SEC_HEADERS)
                    for row in _sec_records(archived):
                        acc = row.get("accessionNumber")
                        filed = row.get("filingDate")
                        if acc and filed and row.get("form") == "4" and _date_in_window(filed):
                            records[acc] = row
                except FetchError as exc:
                    archive_errors.append(str(exc))

            by_year: dict[str, int] = {}
            for row in records.values():
                year = str(row["filingDate"])[:4]
                by_year[year] = by_year.get(year, 0) + 1
            expected_years = {str(y) for y in range(STUDY_START.year, STUDY_END.year + 1)}
            missing_years = sorted(expected_years - set(by_year))

            ordered = sorted(records.values(), key=lambda row: (row["filingDate"], row["accessionNumber"]))
            sample_rows: list[dict[str, Any]] = []
            sample_indices = sorted(set([0, len(ordered) // 2, len(ordered) - 1]))
            for idx in sample_indices:
                if not ordered:
                    break
                row = ordered[idx]
                primary = row.get("primaryDocument")
                if not primary:
                    sample_rows.append({"retrievable": False, "error": "primaryDocument missing"})
                    continue
                accession = str(row["accessionNumber"]).replace("-", "")
                url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary}"
                try:
                    body = _fetch_text(url, headers=SEC_HEADERS)
                    sample_rows.append({
                        "filing_date": row["filingDate"],
                        "accession": row["accessionNumber"],
                        "retrievable": True,
                        "transaction_code_field": bool(re.search(r"transaction\s*code|transactionCode", body, re.I)),
                        "purchase_or_sale_code_sample": bool(re.search(r"transactionCode\s*[^>]*>\s*[PS]\s*<", body, re.I)),
                    })
                except FetchError as exc:
                    sample_rows.append({
                        "filing_date": row["filingDate"],
                        "accession": row["accessionNumber"],
                        "retrievable": False,
                        "error": str(exc),
                    })

            status = (
                "COVERAGE_VALIDATED"
                if records
                and not archive_errors
                and not missing_years
                and sample_rows
                and all(item.get("retrievable") for item in sample_rows)
                else "DATA_INSUFFICIENT"
            )
            if status != "COVERAGE_VALIDATED":
                all_ok = False
            results[symbol] = {
                "symbol": symbol,
                "cik": cik,
                "status": status,
                "form4_count": len(records),
                "filing_year_counts": by_year,
                "missing_years": missing_years,
                "archive_manifest_count": len(archive_specs),
                "archive_errors": archive_errors,
                "samples": sample_rows,
                "pit_anchor": "SEC EDGAR ACCEPTANCE-DATETIME / filing acceptance timestamp",
            }
        except (FetchError, KeyError, ValueError) as exc:
            all_ok = False
            results[symbol] = {"symbol": symbol, "cik": cik, "status": "DATA_INSUFFICIENT", "error": str(exc)}
    return {
        "candidate": "A",
        "family": "sec_insider_flow_event",
        "source": "SEC EDGAR Form 4",
        "status": "COVERAGE_VALIDATED" if all_ok else "DATA_INSUFFICIENT",
        "symbols": results,
        "selection_used": False,
        "performance_evaluation": False,
    }

def _fed_coverage() -> dict[str, Any]:
    years: dict[str, Any] = {}
    all_ok = True
    for year in range(STUDY_START.year, STUDY_END.year + 1):
        try:
            html = _fetch_text(FED_HISTORICAL.format(year=year))
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text)
            statement_count = len(re.findall(r"\bStatement\b", text, re.I))
            rate_language = bool(re.search(r"target range.*federal funds rate|federal funds rate.*target range", text, re.I))
            status = "COVERAGE_VALIDATED" if statement_count >= 1 and rate_language else "DATA_INSUFFICIENT"
            if status != "COVERAGE_VALIDATED":
                all_ok = False
            years[str(year)] = {
                "source_url": FED_HISTORICAL.format(year=year),
                "statement_occurrences": statement_count,
                "target_rate_language_probe": rate_language,
                "status": status,
                "pit_anchor": "official FOMC statement/release date; next eligible trading bar",
            }
        except FetchError as exc:
            all_ok = False
            years[str(year)] = {"source_url": FED_HISTORICAL.format(year=year), "status": "DATA_INSUFFICIENT", "error": str(exc)}
    return {
        "candidate": "B",
        "family": "fomc_policy_decision_event",
        "source": "Federal Reserve official FOMC historical pages",
        "status": "COVERAGE_VALIDATED" if all_ok else "DATA_INSUFFICIENT",
        "years": years,
        "selection_used": False,
        "performance_evaluation": False,
    }

def _treasury_coverage() -> dict[str, Any]:
    params = {
        "fields": "record_date,security_type,security_term,auction_date,cusip,bid_to_cover_ratio",
        "filter": (
            f"security_type:eq:Note,security_term:eq:10-Year,"
            f"record_date:gte:{STUDY_START.isoformat()},record_date:lte:{STUDY_END.isoformat()}"
        ),
        "sort": "auction_date",
        "page[size]": 2000,
    }
    url = TREASURY_API + "?" + urlencode(params)
    try:
        payload = _fetch_json(url)
    except FetchError as exc:
        return {
            "candidate": "C",
            "family": "treasury_auction_demand_event",
            "source": "U.S. Treasury Fiscal Data Treasury Securities Auctions Data",
            "status": "DATA_INSUFFICIENT",
            "error": str(exc),
            "selection_used": False,
            "performance_evaluation": False,
        }
    rows = payload.get("data", [])
    usable = [
        row for row in rows
        if row.get("record_date") and row.get("auction_date") and row.get("cusip")
        and row.get("bid_to_cover_ratio") not in (None, "", "null")
    ]
    years = {str(row["record_date"])[:4] for row in usable}
    expected_years = {str(y) for y in range(STUDY_START.year, STUDY_END.year + 1)}
    missing_years = sorted(expected_years - years)
    status = "COVERAGE_VALIDATED" if usable and not missing_years else "DATA_INSUFFICIENT"
    return {
        "candidate": "C",
        "family": "treasury_auction_demand_event",
        "source": "U.S. Treasury Fiscal Data Treasury Securities Auctions Data",
        "status": status,
        "row_count": len(rows),
        "usable_row_count": len(usable),
        "missing_years": missing_years,
        "sample_first": usable[0] if usable else None,
        "sample_last": usable[-1] if usable else None,
        "pit_anchor": "official record_date / publication date; next eligible trading bar",
        "selection_used": False,
        "performance_evaluation": False,
    }

def run(*, output_path: str | Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "task_id": "Q-018-SOURCE-FEASIBILITY-PREFLIGHT",
        "recorded_at": date.today().isoformat(),
        "study_window": {"start": STUDY_START.isoformat(), "end": STUDY_END.isoformat()},
        "universe": {"name": UNIVERSE, "symbols": list(SYMBOLS)},
        "governance": {
            "coverage_only": True,
            "performance_evaluation": False,
            "holdout_used": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "asset_search": False,
            "feature_search": False,
            "horizon_search": False,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "sources": {
            "sec": SEC_TICKERS_URL,
            "fed_calendar": FED_CALENDAR,
            "fed_historical_pattern": FED_HISTORICAL,
            "treasury_api": TREASURY_API,
        },
    }
    cik_map = _sec_symbol_to_cik()
    result["sec"] = _sec_form4_coverage(cik_map)
    result["fed"] = _fed_coverage()
    result["treasury"] = _treasury_coverage()
    statuses = [result[k]["status"] for k in ("sec", "fed", "treasury")]
    result["overall_status"] = "COVERAGE_READY" if all(s == "COVERAGE_VALIDATED" for s in statuses) else "DATA_INSUFFICIENT"
    result["fingerprint"] = _fp(result)
    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"task_id": result["task_id"], "overall_status": result["overall_status"], "candidate_statuses": statuses, "fingerprint": result["fingerprint"]}, sort_keys=True))
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="research/runs/source_feasibility/q018_source_feasibility.json")
    args = parser.parse_args()
    try:
        run(output_path=args.output)
    except FetchError as exc:
        print(json.dumps({"status": "DATA_INSUFFICIENT", "error": str(exc)}))
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
