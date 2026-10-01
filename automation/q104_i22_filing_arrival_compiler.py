"""Q104:I22 deterministic SEC filing-arrival compiler, pre-performance only."""
from __future__ import annotations
import argparse, hashlib, json, urllib.request, urllib.error
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import exchange_calendars as xcals

SYMBOLS=("SPGI","NDAQ","AMP","RJF","WMB","VLO","DVN","EMN")
FORMS=frozenset({"8-K","8-K/A","10-Q","10-Q/A","10-K","10-K/A"})
START=date(2011,1,1); END=date(2025,9,24); WINDOW=20
UA="trading-agent-public/Q104-I22-filing-arrival"
TIMEOUT=45
CAL=xcals.get_calendar("XNYS")

def get_json(url:str)->tuple[int,bytes,object]:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
            b=r.read()
        try: p=json.loads(b)
        except json.JSONDecodeError: p=None
        return 200,b,p
    except urllib.error.HTTPError as e:
        return int(e.code),e.read(),None
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        return 599,str(e).encode(),None

def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()

def next_xnys(after_date:date)->date:
    sessions=CAL.sessions_in_range(after_date+timedelta(days=1),after_date+timedelta(days=10))
    if len(sessions)==0: raise RuntimeError(f"NO_XNYS_AFTER:{after_date}")
    return sessions[0].date()

def parse_acceptance(value:str)->datetime:
    return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)

def compile_rows(rows:list[dict], cutoff:date=END)->dict:
    events=[]
    for row in rows:
        if row.get("form") not in FORMS or not row.get("acceptanceDateTime") or not row.get("accessionNumber"):
            continue
        try: acc=parse_acceptance(str(row["acceptanceDateTime"]))
        except ValueError as e: raise RuntimeError("INVALID_ACCEPTANCE_DATETIME") from e
        if acc.date()<START or acc.date()>cutoff: continue
        eligible=next_xnys(acc.date())
        if eligible>cutoff: continue
        events.append({
            "form":row["form"],
            "accession":str(row["accessionNumber"]),
            "filing_date":str(row.get("filingDate","")),
            "acceptance_datetime":acc.isoformat(),
            "eligible_session":eligible.isoformat()
        })
    events.sort(key=lambda x:(x["acceptance_datetime"],x["accession"],x["form"]))
    event_sessions=sorted({date.fromisoformat(x["eligible_session"]) for x in events})
    by_session={s:[] for s in event_sessions}
    for e in events:
        by_session[date.fromisoformat(e["eligible_session"])].append(e)

    # The fixed window is defined in actual XNYS sessions, not in the sparse
    # set of sessions on which an event happened. Otherwise a quiet month
    # could be treated as if it had only a few elapsed sessions.
    calendar_sessions = [ts.date() for ts in CAL.sessions_in_range(
        datetime.combine(START, datetime.min.time(), tzinfo=timezone.utc),
        datetime.combine(cutoff, datetime.max.time(), tzinfo=timezone.utc),
    )]
    density=[]
    for idx, s in enumerate(calendar_sessions):
        prior=calendar_sessions[max(0,idx-WINDOW+1):idx+1]
        density.append({
            "decision_session":s.isoformat(),
            "arrival_count_20":sum(len(by_session.get(p,[])) for p in prior),
            "window_session_count":len(prior),
        })
    return {
        "filing_count":len(events),
        "eligible_session_count":len(event_sessions),
        "decision_session_count":len(calendar_sessions),
        "first_acceptance":events[0]["acceptance_datetime"] if events else None,
        "last_acceptance":events[-1]["acceptance_datetime"] if events else None,
        "events":events,
        "arrival_density_20":density
    }

def fetch_issuer(symbol:str,cik:int)->dict:
    url=f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    status,body,payload=get_json(url)
    if status!=200 or not isinstance(payload,dict): raise RuntimeError(f"SEC_SUBMISSIONS_HTTP_{status}:{symbol}")
    rows=[]
    recent=payload.get("filings",{}).get("recent",{})
    n=len(recent.get("form",[]))
    for i in range(n):
        rows.append({
            "form":recent.get("form",[""]*n)[i],
            "filingDate":recent.get("filingDate",[""]*n)[i],
            "acceptanceDateTime":recent.get("acceptanceDateTime",[""]*n)[i] if i<len(recent.get("acceptanceDateTime",[])) else None,
            "accessionNumber":recent.get("accessionNumber",[""]*n)[i]
        })
    historical=[]
    for ext in payload.get("filings",{}).get("files",[]):
        name=ext.get("name")
        if not name: continue
        start=ext.get("filingFrom",""); end=ext.get("filingTo","")
        if end and end<START.isoformat(): continue
        if start and start>END.isoformat(): continue
        u="https://data.sec.gov/submissions/"+name
        st,bb,pp=get_json(u)
        if st!=200 or not isinstance(pp,dict): raise RuntimeError(f"SEC_SUBMISSIONS_ARCHIVE_HTTP_{st}:{symbol}:{name}")
        n=len(pp.get("form",[]))
        for i in range(n):
            d=str(pp.get("filingDate",[""]*n)[i])
            if not (START.isoformat()<=d<=END.isoformat()): continue
            historical.append({
                "form":pp.get("form",[""]*n)[i],
                "filingDate":d,
                "acceptanceDateTime":pp.get("acceptanceDateTime",[""]*n)[i] if i<len(pp.get("acceptanceDateTime",[])) else None,
                "accessionNumber":pp.get("accessionNumber",[""]*n)[i]
            })
    merged=rows+historical
    # A filing may occur in the recent array and an extension only after a dataset refresh;
    # accession is the stable lineage key. Keep the earliest row with complete acceptance metadata.
    by_acc={}
    for r in merged:
        acc=str(r.get("accessionNumber",""))
        if not acc: continue
        old=by_acc.get(acc)
        if old is None or (r.get("acceptanceDateTime") or "") < (old.get("acceptanceDateTime") or ""):
            by_acc[acc]=r
    return {"symbol":symbol,"cik":f"{cik:010d}","source_url":url,"source_sha256":sha(body),"rows":list(by_acc.values())}

def mutation_tests(compiled:list[dict])->dict:
    # Input-row ordering invariance.
    order_ok=True
    future_ok=True
    accession_ok=True
    for item in compiled:
        rows=item["raw_rows"]
        a=compile_rows(rows)
        shuffled=list(reversed(rows))
        b=compile_rows(shuffled)
        order_ok &= json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)
        future=dict(rows[0]) if rows else {"form":"8-K","acceptanceDateTime":"2025-01-02T12:00:00Z","accessionNumber":"FUTURE-TEST","filingDate":"2025-01-02"}
        future["acceptanceDateTime"]="2025-12-01T12:00:00Z"; future["filingDate"]="2025-12-01"
        future_rows=rows+[future]
        c=compile_rows(future_rows)
        # pre-END state must be byte-identical because future event is beyond cutoff.
        future_ok &= json.dumps(a,sort_keys=True)==json.dumps(c,sort_keys=True)
        accs=[e["accession"] for e in a["events"]]
        accession_ok &= len(accs)==len(set(accs))
    return {
        "input_order_invariance":order_ok,
        "future_acceptance_invariance":future_ok,
        "amendment_accession_separation":accession_ok
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    st,body,payload=get_json("https://www.sec.gov/files/company_tickers.json")
    if st!=200 or not isinstance(payload,dict): raise RuntimeError("SEC_TICKERS_HTTP")
    mapping={}
    for row in payload.values():
        t=str(row.get("ticker","")).upper(); cik=row.get("cik_str")
        if t in SYMBOLS and isinstance(cik,int): mapping[t]=cik
    if set(mapping)!=set(SYMBOLS): raise RuntimeError("MISSING_CIK_MAPPING")
    issuers=[fetch_issuer(s,mapping[s]) for s in SYMBOLS]
    compiled=[]
    for item in issuers:
        c=compile_rows(item["rows"])
        compiled.append({"symbol":item["symbol"],"cik":item["cik"],"raw_rows":item["rows"],"compiled":c,"source_sha256":item["source_sha256"]})
    mutation=mutation_tests(compiled)
    result={
        "schema_version":"1.0",
        "task_id":"Q-2026-10-01-104-I22-FILING-ARRIVAL",
        "status":"I22_PIT_COMPILER_COMPLETED" if all(mutation.values()) else "I22_PIT_COMPILER_FAILED",
        "fixed_forms":sorted(FORMS),
        "study_window":{"start":START.isoformat(),"end":END.isoformat()},
        "eligible_session_rule":"first XNYS session whose session_date is strictly after the acceptanceDateTime calendar date",
        "arrival_density_window":WINDOW,
        "symbols":list(SYMBOLS),
        "issuer_results":{x["symbol"]:x["compiled"] for x in compiled},
        "summary":{"filings":sum(x["compiled"]["filing_count"] for x in compiled),"eligible_sessions":sum(x["compiled"]["eligible_session_count"] for x in compiled)},
        "mutation_tests":mutation,
        "governance":{"performance":False,"holdout":False,"selection":False,"ranking":False,"parameter_search":False,"asset_search":False,"threshold_search":False,"performance_authorized":False,"automatic_promotion":False},
        "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
        "source_response_fingerprint":sha(body)
    }
    result["receipt_fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"filings":result["summary"]["filings"],"mutation_tests":mutation}))
    return 0

if __name__=="__main__": raise SystemExit(main())
