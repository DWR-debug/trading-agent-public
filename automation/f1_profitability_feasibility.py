"""F1 gross-profitability source/PIT feasibility preflight.

This is a coverage-only harness. It does not compute returns, rank assets for
performance, access holdouts, tune parameters, or authorize trading.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
SYMBOLS = ("UPS", "FDX", "DIS", "ADP", "ORLY", "AZO", "TJX", "RSG")
CIK_MAP = {
    "UPS": 1090727, "FDX": 1048911, "DIS": 1744489, "ADP": 8670,
    "ORLY": 898173, "AZO": 866787, "TJX": 109198, "RSG": 1060391,
}
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
HEADERS = {"User-Agent": "trading-agent-public research https://github.com/DWR-debug/trading-agent-public"}
TAG_MAP = {
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"),
    "cogs": ("CostOfRevenue", "CostOfGoodsAndServicesSold"),
    "assets": ("Assets",),
}
ANNUAL_FORMS = {"10-K", "10-K/A"}

class FetchError(RuntimeError):
    pass

def _fetch_json(url: str) -> Any:
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as exc:
        raise FetchError(f"{url}: {exc}") from exc

def _fp(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _acceptance(value: str) -> datetime:
    return datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)

def _annual_filing_rows(submissions: dict[str, Any]) -> list[dict[str, Any]]:
    recent = submissions.get("filings", {}).get("recent", {})
    if not recent:
        return []
    size = len(next(iter(recent.values())))
    rows = []
    for i in range(size):
        row = {k: recent[k][i] for k in recent}
        if row.get("form") not in ANNUAL_FORMS:
            continue
        try:
            filed = date.fromisoformat(row["filingDate"])
            if filed < STUDY_START or filed > STUDY_END:
                continue
            acceptance = _acceptance(row["acceptanceDateTime"])
        except (KeyError, TypeError, ValueError):
            continue
        rows.append({
            "accession": row.get("accessionNumber"),
            "form": row.get("form"),
            "filing_date": row.get("filingDate"),
            "acceptance_datetime": acceptance.isoformat(),
            "report_date": row.get("reportDate"),
            "fiscal_year": row.get("fiscalYear"),
        })
    return sorted(rows, key=lambda x: (x["acceptance_datetime"], x["accession"]))

def _fact_rows(companyfacts: dict[str, Any], tag: str) -> list[dict[str, Any]]:
    concept = companyfacts.get("facts", {}).get("us-gaap", {}).get(tag)
    if not concept:
        return []
    out = []
    for unit, rows in concept.get("units", {}).items():
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            item = dict(row)
            item["unit"] = unit
            out.append(item)
    return out

def _valid_fact(rows: list[dict[str, Any]], filing: dict[str, Any], *, instant: bool) -> list[dict[str, Any]]:
    out = []
    accession = filing["accession"]
    report_date = filing.get("report_date")
    for row in rows:
        if row.get("accn") != accession or row.get("form") not in ANNUAL_FORMS:
            continue
        if report_date and row.get("end") != report_date:
            continue
        if instant:
            if row.get("start") is not None:
                continue
        else:
            start = row.get("start")
            end = row.get("end")
            if not start or not end or row.get("fp") not in ("FY", None):
                continue
            try:
                days = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
            except ValueError:
                continue
            if not 300 <= days <= 380:
                continue
        if row.get("val") is None or row.get("unit") in (None, "shares"):
            continue
        out.append(row)
    return out

def _select_concept(companyfacts: dict[str, Any], concept: str, filing: dict[str, Any], *, instant: bool) -> dict[str, Any]:
    for tag in TAG_MAP[concept]:
        valid = _valid_fact(_fact_rows(companyfacts, tag), filing, instant=instant)
        if len(valid) == 1:
            return {"tag": tag, "row": valid[0]}
        if len(valid) > 1:
            return {"error": f"AMBIGUOUS_{concept.upper()}_{tag}", "candidates": valid}
    return {"error": f"MISSING_{concept.upper()}"}

def assess_symbol(symbol: str) -> dict[str, Any]:
    cik = CIK_MAP[symbol]
    submissions = _fetch_json(SUBMISSIONS_URL.format(cik=cik))
    companyfacts = _fetch_json(COMPANYFACTS_URL.format(cik=cik))
    filings = _annual_filing_rows(submissions)
    checked = []
    complete = 0
    for filing in filings:
        revenue = _select_concept(companyfacts, "revenue", filing, instant=False)
        cogs = _select_concept(companyfacts, "cogs", filing, instant=False)
        assets = _select_concept(companyfacts, "assets", filing, instant=True)
        ok = all("row" in x for x in (revenue, cogs, assets))
        if ok:
            complete += 1
        checked.append({
            "filing": filing,
            "complete": ok,
            "revenue": {"tag": revenue.get("tag"), "status": "FOUND" if "row" in revenue else revenue.get("error")},
            "cogs": {"tag": cogs.get("tag"), "status": "FOUND" if "row" in cogs else cogs.get("error")},
            "assets": {"tag": assets.get("tag"), "status": "FOUND" if "row" in assets else assets.get("error")},
        })
    missing = [item for item in checked if not item["complete"]]
    return {
        "symbol": symbol,
        "cik": cik,
        "annual_10k_filings": len(filings),
        "complete_annual_facts": complete,
        "incomplete_filing_count": len(missing),
        "status": "COVERAGE_VALIDATED" if filings and not missing else "DATA_INSUFFICIENT",
        "pit_anchor": "EDGAR acceptance datetime matched by accession number; XBRL facts constrained to the exact filing accession and report date",
        "filings": checked,
    }

def run(output: str | Path) -> dict[str, Any]:
    symbols = []
    all_ok = True
    for symbol in SYMBOLS:
        try:
            item = assess_symbol(symbol)
        except (FetchError, KeyError, ValueError) as exc:
            item = {"symbol": symbol, "cik": CIK_MAP[symbol], "status": "DATA_INSUFFICIENT", "error": str(exc)}
        symbols.append(item)
        all_ok &= item.get("status") == "COVERAGE_VALIDATED"
    result = {
        "schema_version": "1.0",
        "task_id": "F1-GROSS-PROFITABILITY-SOURCE-PIT-FEASIBILITY-2026-09-28",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "study_window": {"start": STUDY_START.isoformat(), "end": STUDY_END.isoformat()},
        "candidate": "F1_GROSS_PROFITABILITY_ASSETS",
        "symbols": list(SYMBOLS),
        "tag_map": TAG_MAP,
        "governance": {"performance_evaluation": False, "holdout_used": False, "selection_used": False, "parameter_search": False, "asset_search": False, "performance_trial_authorized": False},
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
        "status": "COVERAGE_READY" if all_ok else "DATA_INSUFFICIENT",
        "symbols_detail": symbols,
    }
    result["fingerprint"] = _fp(result)
    path = Path(output)
    if not path.is_absolute(): path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "fingerprint": result["fingerprint"]}, sort_keys=True))
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="research/runs/f1_profitability/f1_source_pit_feasibility.json")
    args = parser.parse_args()
    raise SystemExit(0 if run(args.output)["status"] in {"COVERAGE_READY", "DATA_INSUFFICIENT"} else 1)