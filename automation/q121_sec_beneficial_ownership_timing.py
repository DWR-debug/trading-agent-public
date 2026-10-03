"""Q121 fixed SEC beneficial-ownership disclosure timing compiler.

Discovery/PIT only. The compiler uses the post-2024 SEC Schedule 13D/13G
filing-hour contract and maps observations only to the next eligible XNYS
session. It never uses returns or holdout data.
"""
from __future__ import annotations

import argparse, hashlib, json
import urllib.error, urllib.request
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import exchange_calendars as xcals

SYMBOLS=("SPGI","NDAQ","AMP","RJF","WMB","VLO","DVN","EMN")
FORMS=frozenset({"SC 13D","SC 13G","SC 13D/A","SC 13G/A"})
START=date(2024,2,5)
END=date(2025,9,24)
WINDOW=20
ET=ZoneInfo("America/New_York")
CAL=xcals.get_calendar("XNYS")
UA="trading-agent-public/Q121-beneficial-ownership-timing"

def get_json(url:str)->tuple[int,bytes,object]:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            b=r.read()
        try: p=json.loads(b)
        except json.JSONDecodeError: p=None
        return 200,b,p
    except urllib.error.HTTPError as e:
        return int(e.code),e.read(),None
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        return 599,str(e).encode(),None

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def next_xnys(after_date:date)->date:
    s=CAL.sessions_in_range((after_date+timedelta(days=1)).isoformat(),(after_date+timedelta(days=10)).isoformat())
    if len(s)==0:
        raise RuntimeError(f"NO_XNYS_AFTER:{after_date}")
    return s[0].date()

def parse_acceptance(value:str)->datetime:
    return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)

def classify_event(row:dict)->dict:
    if str(row.get("form","")) not in FORMS:
        return {"state":"IGNORED_FORM"}
    if not row.get("acceptanceDateTime") or not row.get("filingDate") or not row.get("accessionNumber"):
        return {"state":"INVALID_MISSING_METADATA"}
    acc=parse_acceptance(str(row["acceptanceDateTime"]))
    local=acc.astimezone(ET)
    local_date=local.date()
    filing=date.fromisoformat(str(row["filingDate"]))
    if filing != local_date:
        raise RuntimeError("FILING_DATE_MISMATCH")
    t=local.time()
    if t < time(17,30):
        state="STANDARD_DAY"
    elif t <= time(22,0):
        state="LATE_DAY_SAME_DATE"
    else:
        state="OUT_OF_CONTRACT"
    return {
        "state":state,
        "accession":str(row["accessionNumber"]),
        "form":str(row["form"]),
        "acceptance_datetime_utc":acc.isoformat(),
        "acceptance_datetime_et":local.isoformat(),
        "filing_date":filing.isoformat()
    }

def compile_events(rows:list[dict], cutoff:date=END)->dict:
    events=[]
    for row in rows:
        if str(row.get("form","")) not in FORMS:
            continue
        event=classify_event(row)
        if event["state"] in {"INVALID_MISSING_METADATA","OUT_OF_CONTRACT"}:
            continue
        if date.fromisoformat(event["filing_date"]) < START or date.fromisoformat(event["filing_date"]) > cutoff:
            continue
        event["eligible_session"]=next_xnys(date.fromisoformat(event["filing_date"])).isoformat()
        events.append(event)
    events.sort(key=lambda x:(x["acceptance_datetime_utc"],x["accession"]))
    if len({x["accession"] for x in events}) != len(events):
        raise RuntimeError("DUPLICATE_ACCESSION")
    calendar=[ts.date() for ts in CAL.sessions_in_range(START.isoformat(),cutoff.isoformat())]
    by_issuer_session={}
    for e in events:
        key=(e.get("issuer"),e["eligible_session"])
        by_issuer_session.setdefault(key,[]).append(e)
    density=[]
    for idx,s in enumerate(calendar):
        prior=calendar[max(0,idx-WINDOW+1):idx+1]
        count=sum(1 for e in events if e["eligible_session"] in {x.isoformat() for x in prior})
        late=sum(1 for e in events if e["eligible_session"] in {x.isoformat() for x in prior} and e["state"]=="LATE_DAY_SAME_DATE")
        density.append({"decision_session":s.isoformat(),"arrival_count_20":count,"late_day_count_20":late})
    return {"event_count":len(events),"events":events,"arrival_density_20":density}

def fetch_issuer(symbol:str,cik:int)->dict:
    url=f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    status,body,payload=get_json(url)
    if status!=200 or not isinstance(payload,dict):
        raise RuntimeError(f"SEC_SUBMISSIONS_HTTP_{status}:{symbol}")
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
    for ext in payload.get("filings",{}).get("files",[]):
        name=ext.get("name")
        if not name: continue
        st,bb,pp=get_json("https://data.sec.gov/submissions/"+name)
        if st!=200 or not isinstance(pp,dict):
            raise RuntimeError(f"SEC_SUBMISSIONS_ARCHIVE_HTTP_{st}:{symbol}:{name}")
        n=len(pp.get("form",[]))
        for i in range(n):
            rows.append({
                "form":pp.get("form",[""]*n)[i],
                "filingDate":pp.get("filingDate",[""]*n)[i],
                "acceptanceDateTime":pp.get("acceptanceDateTime",[""]*n)[i] if i<len(pp.get("acceptanceDateTime",[])) else None,
                "accessionNumber":pp.get("accessionNumber",[""]*n)[i]
            })
    by_acc={}
    for r in rows:
        acc=str(r.get("accessionNumber",""))
        if not acc: continue
        if acc not in by_acc:
            by_acc[acc]=r
    return {"symbol":symbol,"cik":f"{cik:010d}","source_url":url,"source_sha256":sha(body),"rows":list(by_acc.values())}

def mutation_tests(rows:list[dict])->dict:
    a=compile_events(rows,END)
    b=compile_events(list(reversed(rows)),END)
    future=dict(rows[0]) if rows else {"form":"SC 13G","acceptanceDateTime":"2025-09-01T18:00:00Z","filingDate":"2025-09-01","accessionNumber":"BASE"}
    future["acceptanceDateTime"]="2026-01-02T18:00:00Z"; future["filingDate"]="2026-01-02"; future["accessionNumber"]="FUTURE"
    c=compile_events(rows+[future],END)
    boundary_standard={"form":"SC 13G","acceptanceDateTime":"2024-06-03T21:29:59Z","filingDate":"2024-06-03","accessionNumber":"BSTD"}
    boundary_late={"form":"SC 13G","acceptanceDateTime":"2024-06-03T21:30:00Z","filingDate":"2024-06-03","accessionNumber":"BLATE"}
    return {
        "input_order_invariance":json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True),
        "future_cutoff_invariance":json.dumps(a,sort_keys=True)==json.dumps(c,sort_keys=True),
        "accession_lineage":len({x["accession"] for x in a["events"]})==a["event_count"],
        "boundary_1730":classify_event(boundary_standard)["state"]=="STANDARD_DAY",
        "boundary_1730_late":classify_event(boundary_late)["state"]=="LATE_DAY_SAME_DATE"
    }

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,required=True); args=ap.parse_args()
    st,body,payload=get_json("https://www.sec.gov/files/company_tickers.json")
    if st!=200 or not isinstance(payload,dict): raise RuntimeError("SEC_TICKERS_HTTP")
    mapping={}
    for row in payload.values():
        t=str(row.get("ticker","")).upper(); cik=row.get("cik_str")
        if t in SYMBOLS and isinstance(cik,int): mapping[t]=cik
    if set(mapping)!=set(SYMBOLS): raise RuntimeError("MISSING_CIK_MAPPING")
    compiled={}
    all_mut=True
    total_events=0
    for symbol in SYMBOLS:
        issuer=fetch_issuer(symbol,mapping[symbol])
        c=compile_events(issuer["rows"])
        for e in c["events"]: e["issuer"]=symbol
        # Re-run the session aggregation after adding issuer identity.
        c=compile_events([dict(x,issuer=symbol) for x in issuer["rows"]])
        compiled[symbol]=c
        total_events+=c["event_count"]
        all_mut=all_mut and all(mutation_tests(issuer["rows"]).values())
    result={
        "schema_version":"1.0",
        "task_id":"Q-2026-10-03-121-SEC-BENEFICIAL-OWNERSHIP-TIMING",
        "status":"Q121_DISCOVERY_PIT_COMPLETED" if all_mut else "Q121_DISCOVERY_PIT_FAILED",
        "symbols":list(SYMBOLS),
        "study_window":{"start":START.isoformat(),"end":END.isoformat()},
        "reform_effective_date":START.isoformat(),
        "fixed_forms":sorted(FORMS),
        "issuer_results":compiled,
        "summary":{"event_count":total_events},
        "governance":{
            "performance":False,"holdout":False,"selection":False,"ranking":False,
            "parameter_search":False,"threshold_search":False,"horizon_search":False,
            "asset_search":False,"variant_search":False,
            "performance_authorized":False,"automatic_promotion":False
        },
        "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}
    }
    result["receipt_fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"event_count":total_events,"receipt_fingerprint":result["receipt_fingerprint"]}))
    return 0

if __name__=="__main__": raise SystemExit(main())
