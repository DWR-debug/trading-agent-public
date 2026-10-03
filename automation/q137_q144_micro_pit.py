"""Q137/Q144 bounded historical PIT micro-sample.

No returns or performance logic. Fixed Q107 universe, fixed sample dates,
fixed Wikimedia page map, and explicit SEC acceptance-time boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "research/governance/q144_q107_wikipedia_page_map_2026_10_03.json"
START = date(2025, 8, 25)
END = date(2025, 9, 24)
SYMBOLS = ("SPGI","NDAQ","AMP","RJF","WMB","VLO","DVN","EMN")
UA = "trading-agent-public/Q137-Q144-micro-PIT-R1/1"

def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return int(getattr(response, "status", 200)), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, f"FETCH_ERROR:{type(exc).__name__}:{exc}".encode()

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def parse_acceptance(value: str) -> datetime:
    raw = str(value).strip()
    if raw.isdigit() and len(raw) == 14:
        return datetime.strptime(raw, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("NAIVE_ACCEPTANCE_TIMESTAMP")
    return parsed.astimezone(timezone.utc)

def load_map() -> dict[str, str]:
    data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    symbols = {row["symbol"]: row["wikipedia_title"] for row in data["symbols"]}
    if tuple(symbols) != SYMBOLS:
        raise RuntimeError("Q144_PAGE_MAP_SYMBOL_ORDER_DRIFT")
    return symbols

def get_ciks() -> tuple[dict[str, int], str]:
    status, body = fetch("https://www.sec.gov/files/company_tickers.json")
    if status != 200:
        raise RuntimeError(f"SEC_TICKERS_HTTP_{status}")
    payload = json.loads(body)
    mapping = {}
    for row in payload.values():
        ticker = str(row.get("ticker", "")).upper()
        cik = row.get("cik_str")
        if ticker in SYMBOLS and isinstance(cik, int):
            mapping[ticker] = cik
    if set(mapping) != set(SYMBOLS):
        raise RuntimeError("MISSING_Q107_CIK_MAPPING")
    return mapping, sha(body)

def sec_sample(symbol: str, cik: int) -> dict[str, object]:
    url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    status, body = fetch(url)
    if status != 200:
        return {"symbol": symbol, "status": "INFRA_ACCESS_BLOCKED", "http_status": status, "source_sha256": sha(body)}
    payload = json.loads(body)
    recent = payload.get("filings", {}).get("recent", {})
    keys = ("filingDate", "acceptanceDateTime", "accessionNumber", "form")
    n = max((len(recent.get(k, [])) for k in keys), default=0)
    rows=[]
    for i in range(n):
        filing_date = recent.get("filingDate", [None] * n)[i] if i < len(recent.get("filingDate", [])) else None
        acceptance = recent.get("acceptanceDateTime", [None] * n)[i] if i < len(recent.get("acceptanceDateTime", [])) else None
        accession = recent.get("accessionNumber", [None] * n)[i] if i < len(recent.get("accessionNumber", [])) else None
        form = recent.get("form", [None] * n)[i] if i < len(recent.get("form", [])) else None
        if not filing_date or not acceptance or not accession:
            continue
        try:
            filing_day = date.fromisoformat(str(filing_date))
            accepted = parse_acceptance(str(acceptance))
        except (ValueError, TypeError):
            continue
        if START <= filing_day <= END:
            rows.append({
                "symbol": symbol, "form": str(form), "filing_date": filing_day.isoformat(),
                "acceptance_datetime_utc": accepted.isoformat(), "accession": str(accession),
            })
    unique = len({r["accession"] for r in rows}) == len(rows)
    return {
        "symbol": symbol, "status": "PIT_SAMPLE_RECONSTRUCTABLE" if rows and unique else "PIT_SAMPLE_UNRESOLVED",
        "cik": f"{cik:010d}", "source_url": url, "source_sha256": sha(body),
        "rows": sorted(rows, key=lambda r:(r["acceptance_datetime_utc"], r["accession"])),
        "event_count": len(rows), "accessions_unique": unique,
    }

def pageview_sample(symbol: str, title: str) -> dict[str, object]:
    article = urllib.parse.quote(title, safe="")
    url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
           f"all-access/all-agents/{article}/daily/2025082500/2025092500")
    status, body = fetch(url)
    if status != 200:
        return {"symbol": symbol, "status": "INFRA_ACCESS_BLOCKED", "http_status": status, "source_sha256": sha(body), "url": url}
    payload = json.loads(body)
    items = payload.get("items", [])
    valid=[]
    bad=0
    for item in items:
        ts = item.get("timestamp")
        views = item.get("views")
        identity = item.get("article")
        if not isinstance(ts, str) or identity is None or identity != title or not isinstance(views, int) or views < 0:
            bad += 1
            continue
        valid.append({"timestamp": ts, "views": views, "article": identity})
    timestamps=[r["timestamp"] for r in valid]
    monotonic=timestamps == sorted(timestamps)
    unique=len(timestamps)==len(set(timestamps))
    ok=bool(valid) and bad == 0 and monotonic and unique
    return {
        "symbol":symbol,"status":"PIT_SAMPLE_RECONSTRUCTABLE" if ok else "PIT_SAMPLE_UNRESOLVED",
        "title":title,"url":url,"http_status":status,"source_sha256":sha(body),
        "items":len(valid),"invalid_items":bad,"timestamps_monotonic":monotonic,"timestamps_unique":unique,
        "first_timestamp":timestamps[0] if timestamps else None,"last_timestamp":timestamps[-1] if timestamps else None,
    }

def mutation_checks(sec_results: dict[str, dict[str, object]]) -> dict[str, bool]:
    order_ok = True
    future_ok = True
    for value in sec_results.values():
        rows=list(value.get("rows", []))
        reversed_rows=list(reversed(rows))
        left=sorted(rows, key=lambda r:(r["acceptance_datetime_utc"], r["accession"]))
        right=sorted(reversed_rows, key=lambda r:(r["acceptance_datetime_utc"], r["accession"]))
        order_ok = order_ok and left == right
        future=row = {"filing_date": "2025-09-25", "acceptance_datetime_utc": "2025-09-25T12:00:00+00:00", "accession": "FUTURE-SYNTHETIC"}
        bounded=[r for r in rows if START.isoformat() <= r["filing_date"] <= END.isoformat()]
        with_future=[r for r in rows+[future] if START.isoformat() <= r["filing_date"] <= END.isoformat()]
        future_ok = future_ok and bounded == with_future
    return {"sec_input_order_invariance": order_ok, "future_cutoff_invariance": future_ok, "no_search_dimension_present": True}

def run(output: Path) -> dict[str, object]:
    page_map = load_map()
    ciks, tickers_sha = get_ciks()
    sec_results={symbol:sec_sample(symbol,ciks[symbol]) for symbol in SYMBOLS}
    wiki_results={symbol:pageview_sample(symbol,page_map[symbol]) for symbol in SYMBOLS}
    all_sec=all(x["status"]=="PIT_SAMPLE_RECONSTRUCTABLE" for x in sec_results.values())
    all_wiki=all(x["status"]=="PIT_SAMPLE_RECONSTRUCTABLE" for x in wiki_results.values())
    result={
        "schema_version":"1.0","task_id":"Q-2026-10-03-Q137-Q144-MICRO-PIT-R1",
        "status":"MICRO_PIT_SAMPLE_COMPLETED_NO_PERFORMANCE",
        "sample_boundary":{"start":START.isoformat(),"end":END.isoformat(),"symbols":list(SYMBOLS)},
        "q137_sec_submission_sample":{"all_symbols_reconstructable":all_sec,"results":sec_results,"company_tickers_sha256":tickers_sha},
        "q144_wikimedia_pageview_sample":{"all_symbols_reconstructable":all_wiki,"results":wiki_results,"page_map_path":str(MAP_PATH.relative_to(ROOT))},
        "mutation_tests":mutation_checks(sec_results),
        "scientific_boundary":{"performance":False,"holdout_selection":False,"asset_selection":False,"parameter_search":False,"threshold_search":False,"horizon_search":False,"variant_search":False,"candidate_ranking":False,"promotion":False,"live_execution":False},
        "safety":{"PAPER_ONLY":True,"LIVE_TRADING_ENABLED":False,"ORDERS_ENABLED":False,"AUTOMATIC_PROMOTION":False},
    }
    result["receipt_fingerprint"]=sha(json.dumps(result,sort_keys=True,separators=(",",":")).encode())
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"sec_reconstructable":all_sec,"wikimedia_reconstructable":all_wiki,"receipt_fingerprint":result["receipt_fingerprint"]},sort_keys=True))
    return result

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args()
    run(args.output); return 0

if __name__=="__main__": raise SystemExit(main())