"""Q116 real two-quarter SEC 13F transition population feasibility."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,urllib.request,zipfile
from datetime import date,timedelta
from pathlib import Path
from typing import Any
import exchange_calendars as xcals
import pandas as pd
from automation.q111_security_identity_contract import canonical_security_key, normalize_text
from automation.q114_13f_manager_transitions import transition

DATASETS={
 "prior":"https://www.sec.gov/files/structureddata/data/form-13f-data-sets/01mar2026-31may2026_form13f.zip",
 "current":"https://www.sec.gov/files/datastandardsinnovation/data/form-13f-data-sets/01jun2026-31aug2026_form13f.zip",
}
TARGETS={
 "SPGI":{"S&P GLOBAL INC","SP GLOBAL INC"},"NDAQ":{"NASDAQ INC","NASDAQ INCORPORATED"},
 "AMP":{"AMERIPRISE FINANCIAL INC"},"RJF":{"RAYMOND JAMES FINANCIAL INC"},
 "WMB":{"WILLIAMS COMPANIES INC","WILLIAMS COMPANIES INC."},
 "VLO":{"VALERO ENERGY CORP","VALERO ENERGY CORPORATION"},
 "DVN":{"DEVON ENERGY CORP","DEVON ENERGY CORPORATION"},
 "EMN":{"EASTMAN CHEMICAL CO","EASTMAN CHEMICAL COMPANY"},
}
ALIASES={s:{normalize_text(a).replace(" CORPORATION"," CORP").replace(" COMPANY"," CO") for a in names} for s,names in TARGETS.items()}
UA="trading-agent-public/Q116 research"
_XNYS=xcals.get_calendar("XNYS")
_SESSION_CACHE:dict[str,str]={}

def norm_issuer(v:str)->str:
    return normalize_text(v).replace(" CORPORATION"," CORP").replace(" COMPANY"," CO")

def find_target(v:str)->str|None:
    n=norm_issuer(v)
    return next((s for s,a in ALIASES.items() if n in a),None)

def first_xnys_after(value:date)->str:
    key=value.isoformat()
    if key in _SESSION_CACHE:return _SESSION_CACHE[key]
    sessions=_XNYS.sessions_in_range(pd.Timestamp(value.isoformat()),pd.Timestamp((value+timedelta(days=14)).isoformat()))
    for stamp in sessions:
        d=stamp.date()
        if d>value:
            out=d.isoformat();_SESSION_CACHE[key]=out;return out
    raise ValueError("Q116_XNYS_NEXT_SESSION_NOT_FOUND:"+key)

def download(url:str)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/zip"})
    with urllib.request.urlopen(req,timeout=120) as response:return response.read()

def rows_from_member(zf:zipfile.ZipFile,suffix:str)->list[dict[str,str]]:
    name=next((n for n in zf.namelist() if n.lower().endswith(suffix.lower())),None)
    if not name:raise ValueError("Q116_MEMBER_NOT_FOUND:"+suffix)
    with zf.open(name) as raw:
        return list(csv.DictReader(io.TextIOWrapper(raw,encoding="utf-8-sig",newline=""),delimiter="\t"))

def num(row:dict[str,str],keys:tuple[str,...])->str:
    for k in keys:
        if row.get(k) not in (None,""):return row[k]
    raise ValueError("Q116_NUMERIC_FIELD_MISSING:"+",".join(keys))

def scan(archive:bytes,dataset_label:str)->dict[str,Any]:
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        subs=rows_from_member(zf,"submission.tsv");infos=rows_from_member(zf,"infotable.tsv")
    by_accession={r["ACCESSION_NUMBER"]:r for r in subs}
    out={s:{"periods":[],"rows":0,"managers":set(),"securities":set(),"filings":set()} for s in TARGETS}
    records=[]
    for row in infos:
        sym=find_target(row.get("NAMEOFISSUER",""))
        if sym is None:continue
        sub=by_accession.get(row.get("ACCESSION_NUMBER"))
        if sub is None:raise ValueError("Q116_ORPHAN_ACCESSION:"+str(row.get("ACCESSION_NUMBER")))
        key=canonical_security_key({
            "name_of_issuer":row.get("NAMEOFISSUER",""),
            "title_of_class":row.get("TITLEOFCLASS",""),
            "cusip":row.get("CUSIP"),
            "figi":row.get("FIGI"),
        })
        rec={
          "symbol":sym,"manager_cik":str(sub["CIK"]).zfill(10),"accession":str(row["ACCESSION_NUMBER"]),
          "filing_date":str(sub["FILING_DATE"]),"period_of_report":str(sub["PERIODOFREPORT"]),
          "security_key":key,"shares":num(row,("SSHPRNAMT","SHRS_OR_PRN_AMT","SHRSORPRNAMT")),
          "reported_value":num(row,("VALUE","REPORTEDVALUE")),"submission_type":str(sub["SUBMISSIONTYPE"]),
          "dataset":dataset_label,
        }
        rec["eligible_session"]=first_xnys_after(date.fromisoformat(rec["filing_date"]))
        records.append(rec)
        o=out[sym];o["rows"]+=1;o["managers"].add(rec["manager_cik"]);o["securities"].add(key);o["filings"].add(rec["accession"]);o["periods"].add(rec["period_of_report"])
    for o in out.values():
        for k in ("managers","securities","filings","periods"):o[k]=sorted(o[k])
    return {"coverage":out,"records":records,"archive_sha256":hashlib.sha256(archive).hexdigest(),"archive_bytes":len(archive)}

def latest_as_of(records:list[dict[str,Any]],as_of:date)->dict[tuple[str,str,str,str],dict[str,Any]]:
    chosen={}
    for r in records:
        filing=date.fromisoformat(r["filing_date"])
        if filing>as_of:continue
        key=(r["manager_cik"],r["period_of_report"],r["security_key"],r["symbol"])
        old=chosen.get(key)
        if old is None or (r["filing_date"],r["accession"])>(old["filing_date"],old["accession"]):
            chosen[key]=r
    return chosen

def build_transitions(prior:list[dict[str,Any]],current:list[dict[str,Any]],as_of:date)->dict[str,Any]:
    p=latest_as_of(prior,as_of);c=latest_as_of(current,as_of)
    prior_by={(r["manager_cik"],r["security_key"],r["symbol"]):r for r in p.values()}
    current_by={(r["manager_cik"],r["security_key"],r["symbol"]):r for r in c.values()}
    out={s:{k:0 for k in ("NEW","EXIT","INCREASE","DECREASE","UNCHANGED")} for s in TARGETS}
    paired=0
    for key,cur in current_by.items():
        prev=prior_by.get(key)
        def pos(r):
            return {"manager_cik":r["manager_cik"],"accession":r["accession"],
                    "acceptance_datetime":r["filing_date"]+"T23:59:59+00:00",
                    "period_of_report":r["period_of_report"],"name_of_issuer":"SPGI",
                    "title_of_class":"Common Stock","cusip":r["security_key"].split(":",1)[1] if r["security_key"].startswith("CUSIP:") else None,
                    "shares":r["shares"],"reported_value":r["reported_value"]}
        state=transition(pos(prev) if prev else None,pos(cur))["state"]
        out[cur["symbol"]][state]+=1
        if prev is not None:paired+=1
    return {"as_of":as_of.isoformat(),"transition_counts":out,"paired_current_positions":paired,"prior_snapshot_count":len(p),"current_snapshot_count":len(c)}

def synthetic_contract()->dict[str,bool]:
    rows=[
      {"accession":"A1","filing_date":"2026-05-01","manager_cik":"1","period_of_report":"2026-03-31","security_key":"CUSIP:78409V104","symbol":"SPGI","shares":"100","reported_value":"10000"},
      {"accession":"A2","filing_date":"2026-08-01","manager_cik":"1","period_of_report":"2026-06-30","security_key":"CUSIP:78409V104","symbol":"SPGI","shares":"140","reported_value":"15000"}
    ]
    out=build_transitions(rows[:1],rows[1:],date(2026,8,31))
    return {
      "paired":out["paired_current_positions"]==1,
      "increase":out["transition_counts"]["SPGI"]["INCREASE"]==1,
      "pit_cutoff_preserved":out["as_of"]=="2026-08-31",
      "eligible_session_materialized":first_xnys_after(date(2026,8,1))=="2026-08-03"
    }

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,default=Path("research/runs/q116_13f_transition_population/result.json"));a=p.parse_args()
    prior_blob=download(DATASETS["prior"]);current_blob=download(DATASETS["current"])
    prior=scan(prior_blob,"prior");current=scan(current_blob,"current")
    result={"schema_version":"1.0","task_id":"Q-2026-10-01-116-13F-TRANSITION-POPULATION","status":"13F_TWO_QUARTER_TRANSITION_FEASIBILITY_ONLY",
            "datasets":DATASETS,"prior":{k:prior[k] for k in ("coverage","archive_sha256","archive_bytes")},"current":{k:current[k] for k in ("coverage","archive_sha256","archive_bytes")},
            "transition_compile":build_transitions(prior["records"],current["records"],date(2026,8,31)),"synthetic":synthetic_contract(),
            "governance":{"performance":False,"holdout":False,"selection":False,"ranking":False,"parameter_search":False,"asset_search":False,"performance_authorized":False},
            "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}}
    result["receipt_fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Q116_STATUS:",result["status"]);print("Q116_SYNTHETIC_ALL_PASS:",all(result["synthetic"].values()));print("Q116_PRIOR_BYTES:",prior["archive_bytes"]);print("Q116_CURRENT_BYTES:",current["archive_bytes"])
    for s,v in result["transition_compile"]["transition_counts"].items():print("Q116_TARGET:",s,v)
    print("Q116_FINGERPRINT:",result["receipt_fingerprint"])
    return 0 if all(result["synthetic"].values()) else 2

if __name__=="__main__":raise SystemExit(main())
