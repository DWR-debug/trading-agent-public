"""Freeze the exact Q218 SEC event population and next-XNYS market inputs.

This is a pre-performance data-freeze step. It reads the already frozen Q218
performance contract, verifies the exact SEC accessions and acceptance clocks,
stores raw SEC responses, maps each event to the first XNYS session whose open
is strictly after the pair-closure clock, and freezes the corresponding
daily OHLCV observations. It never evaluates performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/governance/q218_performance_contract_2026_10_08.json"
TRIAL_ID = "T-2026-10-08-Q218-PERFORMANCE-01"
SEC_UA = "DWR-debug/trading-agent-public Q218 performance input freeze/1.0 research@example.invalid"
YAHOO_UA = "DWR-debug/trading-agent-public Q218 performance market input freeze/1.0 research@example.invalid"
MAX_ATTEMPTS = 5


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fp(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str, headers: dict[str, str]) -> bytes:
    last: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as response:
                return response.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in {408, 425, 429, 500, 502, 503, 504}:
                raise
            if attempt < MAX_ATTEMPTS:
                time.sleep(min(16, 2 ** (attempt - 1)))
    raise RuntimeError(f"Q218 source fetch failed: {url}: {last}")


def load_contract() -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("trial_id") != TRIAL_ID or contract.get("status") != "FROZEN_PRE_PERFORMANCE_CONTRACT":
        raise RuntimeError("Q218 performance contract is not frozen")
    governance = contract.get("governance", {})
    for key in ("selection_used","holdout_selection_used","parameter_search","threshold_search",
                "horizon_search","asset_search","variant_search","family_ranking",
                "promotion_decision","performance_authorized"):
        if governance.get(key) is not False:
            raise RuntimeError(f"Q218 contract governance invalid: {key}")
    safety = contract.get("safety", {})
    if safety != {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False}:
        raise RuntimeError("Q218 contract safety invalid")
    return contract


def sec_submission_index(cik: str, output_root: Path) -> tuple[dict, dict[str, str]]:
    raw = fetch(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json", {"User-Agent": SEC_UA, "Accept-Encoding": "identity"})
    rel = Path("sec/submissions") / f"CIK{int(cik):010d}.json"
    target = output_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return json.loads(raw.decode("utf-8")), {str(rel): sha256_bytes(raw)}


def accession_header(cik: str, accession: str) -> tuple[bytes, str]:
    rel_url = (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
        f"{accession.replace('-', '')}/{accession}-index-headers.html"
    )
    raw = fetch(rel_url, {"User-Agent": SEC_UA, "Accept-Encoding": "identity"})
    return raw, rel_url


def primary_document(cik: str, accession: str, document: str) -> tuple[bytes, str]:
    rel_url = (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
        f"{accession.replace('-', '')}/{document}"
    )
    raw = fetch(rel_url, {"User-Agent": SEC_UA, "Accept-Encoding": "identity"})
    return raw, rel_url


def acceptance_datetime(header: bytes, expected: str) -> str:
    import re
    text = header.decode("utf-8", errors="replace")
    m = re.search(r"<ACCEPTANCE-DATETIME>\s*([0-9]{14})", text, re.I)
    if not m:
        raise RuntimeError("Q218 acceptance datetime missing")
    raw = m.group(1)
    expected_raw = expected.replace("-", "").replace(":", "").replace("T", "").replace("Z", "")
    if raw != expected_raw:
        raise RuntimeError(f"Q218 acceptance mismatch: expected {expected}, got {raw}")
    local = datetime.strptime(raw, "%Y%m%d%H%M%S").replace(tzinfo=ZoneInfo("America/New_York"))
    return local.isoformat()


def next_xnys_session(closure: datetime, start: str, end: str) -> str:
    cal = xcals.get_calendar("XNYS")
    # exchange_calendars exposes a timezone-naive session index while
    # market_open is UTC-aware. Slice by session-date strings, then compare
    # the actual UTC market-open timestamp to the SEC acceptance closure.
    left = pd.Timestamp(start)
    right = pd.Timestamp(end) + pd.Timedelta(days=10)
    schedule = cal.schedule.loc[str(left.date()):str(right.date())]
    closure_ts = pd.Timestamp(closure)
    if closure_ts.tzinfo is None:
        closure_ts = closure_ts.tz_localize("UTC")
    else:
        closure_ts = closure_ts.tz_convert("UTC")
    open_column = "market_open" if "market_open" in schedule.columns else "open"
    eligible = schedule[schedule[open_column] > closure_ts]
    if eligible.empty:
        raise RuntimeError(f"No XNYS session after closure {closure.isoformat()}")
    return eligible.index[0].date().isoformat()


def yahoo_chart(symbol: str, session: str, output_root: Path) -> tuple[dict, dict]:
    from datetime import date, timedelta
    d = date.fromisoformat(session)
    period1 = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()) - 3 * 86400
    period2 = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()) + 4 * 86400
    query = urllib.parse.urlencode({
        "period1": period1, "period2": period2, "interval": "1d",
        "events": "div,splits", "includePrePost": "false",
    })
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol, safe='')}?{query}"
    raw = fetch(url, {"User-Agent": YAHOO_UA, "Accept": "application/json", "Accept-Encoding": "identity"})
    rel = Path("market_raw") / f"{symbol}_{session}.json"
    path = output_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    payload = json.loads(raw.decode("utf-8"))
    result = payload["chart"]["result"][0]
    tz_name = result.get("meta", {}).get("exchangeTimezoneName", "America/New_York")
    tz = ZoneInfo(tz_name)
    rows = []
    timestamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    for ts, op, hi, lo, cl, vol in zip(
        timestamps, quote["open"], quote["high"], quote["low"], quote["close"], quote["volume"]
    ):
        local_date = datetime.fromtimestamp(int(ts), tz=tz).date().isoformat()
        rows.append({"session": local_date, "open": op, "high": hi, "low": lo, "close": cl, "volume": vol})
    matches = [x for x in rows if x["session"] == session]
    if len(matches) != 1:
        raise RuntimeError(f"Q218 expected exactly one Yahoo market row for {symbol} {session}")
    row = matches[0]
    for key in ("open", "close"):
        value = row.get(key)
        if value is None or not math.isfinite(float(value)) or float(value) <= 0:
            raise RuntimeError(f"Q218 invalid market {key}: {symbol} {session}")
    return {"symbol": symbol, "session": session, "open": float(row["open"]), "high": float(row["high"]) if row["high"] is not None else None,
            "low": float(row["low"]) if row["low"] is not None else None, "close": float(row["close"]),
            "volume": float(row["volume"]) if row["volume"] is not None else None,
            "raw_response_path": rel.as_posix(), "raw_response_sha256": sha256_bytes(raw)}, {"url": url, "raw_response_sha256": sha256_bytes(raw)}


def freeze(output_root: Path, receipt_path: Path) -> dict:
    contract = load_contract()
    contract_sha = sha256_bytes(CONTRACT.read_bytes())
    issuers = contract["universe"]["issuers"]
    events = contract["event_pair_population"]
    fixed_start = contract["upstream"]["independent_pit_window"]["start"]
    fixed_end = contract["upstream"]["independent_pit_window"]["end"]
    future_cutoff = contract["upstream"]["future_cutoff_utc"]

    documents: list[dict] = []
    submissions: list[dict] = []
    frozen_events: list[dict] = []
    market_bars: list[dict] = []
    source_hashes: dict[str, str] = {}

    indices: dict[str, dict] = {}
    for symbol, cik in issuers.items():
        payload, hashes = sec_submission_index(str(cik), output_root)
        indices[symbol] = payload
        source_hashes.update(hashes)

    for row in events:
        symbol, ten_k_acc, eight_k_acc, ten_k_expected, eight_k_expected = row
        cik = str(issuers[symbol])
        recent = indices[symbol].get("filings", {}).get("recent", {})
        accessions = [str(x) for x in recent.get("accessionNumber", [])]
        forms = [str(x) for x in recent.get("form", [])]
        docs = [str(x) for x in recent.get("primaryDocument", [])]
        items = [str(x or "") for x in recent.get("items", [])]
        lookup = {acc: i for i, acc in enumerate(accessions)}
        actual_acceptance: dict[str, str] = {}
        for accession, expected_form, expected_item in ((ten_k_acc, "10-K", None), (eight_k_acc, "8-K", "2.02")):
            if accession not in lookup:
                raise RuntimeError(f"Q218 accession missing from SEC submissions: {symbol} {accession}")
            i = lookup[accession]
            if forms[i] != expected_form:
                raise RuntimeError(f"Q218 form mismatch: {symbol} {accession} {forms[i]}")
            if expected_item is not None and not any(part.strip() == expected_item for part in items[i].replace(";", ",").split(",")):
                raise RuntimeError(f"Q218 Item 2.02 missing: {symbol} {accession}")
            header, header_url = accession_header(cik, accession)
            actual = acceptance_datetime(header, ten_k_expected if accession == ten_k_acc else eight_k_expected)
            actual_acceptance[accession] = actual
            header_rel = Path("sec/headers") / f"{accession}.html"
            (output_root / header_rel).parent.mkdir(parents=True, exist_ok=True)
            (output_root / header_rel).write_bytes(header)
            source_hashes[header_rel.as_posix()] = sha256_bytes(header)
            doc_name = docs[i]
            primary, primary_url = primary_document(cik, accession, doc_name)
            doc_rel = Path("sec/documents") / f"{accession}.html"
            (output_root / doc_rel).parent.mkdir(parents=True, exist_ok=True)
            (output_root / doc_rel).write_bytes(primary)
            source_hashes[doc_rel.as_posix()] = sha256_bytes(primary)
            documents.append({
                "issuer": symbol, "cik": cik, "accession": accession, "form": expected_form,
                "primary_document": doc_name, "path": doc_rel.as_posix(),
                "sha256": sha256_bytes(primary), "header_path": header_rel.as_posix(),
                "header_sha256": sha256_bytes(header), "source_url": primary_url,
                "header_url": header_url, "acceptance_datetime": actual,
            })

        closure_values = [
            datetime.fromisoformat(actual_acceptance[ten_k_acc]),
            datetime.fromisoformat(actual_acceptance[eight_k_acc]),
        ]
        closure = max(closure_values)
        if closure > datetime.fromisoformat(future_cutoff.replace("Z","+00:00")):
            raise RuntimeError("Q218 closure exceeds frozen cutoff")
        action_session = next_xnys_session(closure, fixed_start, fixed_end)
        bar, _ = yahoo_chart(symbol, action_session, output_root)
        market_bars.append(bar)
        frozen_events.append({
            "issuer": symbol, "ten_k_accession": ten_k_acc,
            "item_2_02_8k_accession": eight_k_acc,
            "ten_k_acceptance_datetime": ten_k_expected,
            "item_2_02_8k_acceptance_datetime": eight_k_expected,
            "pair_closure_clock": closure.isoformat().replace("+00:00","Z"),
            "action_session": action_session,
        })

    bundle = {
        "schema_version":"1.0","record_type":"q218_frozen_performance_input_bundle",
        "candidate_id":"Q218","trial_id":TRIAL_ID,"contract_sha256":contract_sha,
        "source_upstream":contract["upstream"],"future_cutoff_session":future_cutoff[:10],
        "events":frozen_events,"documents":documents,"market_bars":market_bars,
        "submissions":sorted(source_hashes.items()),
        "executor_network_access":False,
        "selection_used":False,"parameter_search":False,"threshold_search":False,
        "horizon_search":False,"asset_search":False,"variant_search":False,
        "holdout_selection_used":False,
        "safety":contract["safety"],
    }
    bundle["bundle_fingerprint"]=fp(bundle)
    bundle_path=output_root/"input_bundle_manifest.json"
    bundle_path.parent.mkdir(parents=True,exist_ok=True)
    bundle_path.write_text(json.dumps(bundle,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    receipt={
        "schema_version":"1.0","record_type":"q218_performance_input_bundle",
        "candidate_id":"Q218","trial_id":TRIAL_ID,"status":"INPUT_BUNDLE_FROZEN",
        "bundle_fingerprint":bundle["bundle_fingerprint"],"contract_sha256":contract_sha,
        "event_count":len(frozen_events),"document_count":len(documents),"market_bar_count":len(market_bars),
        "bundle_manifest":"input_bundle_manifest.json",
        "source_response_count":len(source_hashes),
        "selection_used":False,"holdout_evaluation":False,"performance_evaluation":False,
        "performance_authorized":False,"safety":contract["safety"],
    }
    receipt_path.parent.mkdir(parents=True,exist_ok=True)
    receipt_path.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return receipt


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-root",type=Path,required=True)
    parser.add_argument("--receipt",type=Path,required=True)
    args=parser.parse_args()
    result=freeze(args.output_root,args.receipt)
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
