"""Independent Q104:I19 PIT reproduction; no primary compiler imports."""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json
from decimal import Decimal
from pathlib import Path
from typing import Any
import exchange_calendars as xcals

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"research/evidence/q104_i19_historical_pit_compilation_latest.json"
BUNDLE=ROOT/"research/evidence/q104_i19_historical_compiler_input_bundle_latest.json"
OUTPUT=ROOT/"research/evidence/q104_i19_independent_pit_reproduction_latest.json"
XNYS=xcals.get_calendar("XNYS")
CONCEPTS={"net_income_loss":"us-gaap:NetIncomeLoss","operating_cash_flow":"us-gaap:NetCashProvidedByUsedInOperatingActivities","assets":"us-gaap:Assets"}

def canon(v:Any)->str: return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def fp(v:Any)->str: return hashlib.sha256(canon(v).encode()).hexdigest()
def utc(v:str)->dt.datetime: return dt.datetime.fromisoformat(v.replace("Z","+00:00")).astimezone(dt.timezone.utc)
def session(v:dt.datetime)->str:
    s=XNYS.sessions_in_range((v.date()+dt.timedelta(days=1)).isoformat(),(v.date()+dt.timedelta(days=14)).isoformat())
    if not len(s): raise RuntimeError("Q104_I19_REPRO_NO_XNYS_SESSION")
    return s[0].date().isoformat()
def inputs():
    if not RECEIPT.exists() or not BUNDLE.exists(): raise RuntimeError("Q104_I19_REPRO_INPUT_MISSING")
    r=json.loads(RECEIPT.read_text(encoding="utf-8")); b=json.loads(BUNDLE.read_text(encoding="utf-8"))
    if r.get("status")!="Q104_I19_HISTORICAL_PIT_COMPILATION_COMPLETED_NO_PERFORMANCE": raise RuntimeError("Q104_I19_REPRO_UPSTREAM_NOT_POSITIVE")
    if r.get("candidate_id")!="Q104:I19" or b.get("candidate_id")!="Q104:I19": raise RuntimeError("Q104_I19_REPRO_CANDIDATE_MISMATCH")
    if r.get("bundle_fingerprint")!=b.get("bundle_fingerprint"): raise RuntimeError("Q104_I19_REPRO_BUNDLE_FINGERPRINT_MISMATCH")
    return r,b
def num(v:Any)->Decimal: return Decimal(str(v))
def fact_ok(f:dict[str,Any],concept:str)->bool:
    return str(f.get("concept") or "")==concept and str(f.get("unit") or "").upper()=="USD" and not f.get("dimensions") and f.get("value") not in (None,"")
def filing_state(f:dict[str,Any])->dict[str,Any]:
    fs=[x for x in f.get("facts",[]) if isinstance(x,dict)]
    ni=[x for x in fs if fact_ok(x,CONCEPTS["net_income_loss"]) and x.get("start") and x.get("end")]
    cfo=[x for x in fs if fact_ok(x,CONCEPTS["operating_cash_flow"]) and x.get("start") and x.get("end")]
    assets=[x for x in fs if fact_ok(x,CONCEPTS["assets"]) and x.get("instant")]
    pairs=[(a,b) for a in ni for b in cfo if a.get("start")==b.get("start") and a.get("end")==b.get("end") and a.get("fiscal_period")==b.get("fiscal_period")]
    if not pairs: raise RuntimeError("Q104_I19_REPRO_DURATION_ALIGNMENT_FAILED")
    pairs.sort(key=lambda z:(str(z[0].get("end")),str(z[0].get("fiscal_period","")))); n,c=pairs[-1]; end=str(n["end"])
    cur=[x for x in assets if str(x.get("instant"))==end]; prior=[x for x in assets if str(x.get("instant"))<end]
    if not cur or not prior: raise RuntimeError("Q104_I19_REPRO_ASSETS_HISTORY_MISSING")
    sig={canon({k:v for k,v in x.items() if k!="source_fragment"}) for x in cur}
    if len(sig)!=1: raise RuntimeError("Q104_I19_REPRO_ASSETS_CURRENT_CONFLICT")
    prior.sort(key=lambda x:str(x["instant"])); ca=num(cur[0]["value"]); pa=num(prior[-1]["value"]); denom=(ca+pa)/Decimal(2)
    if denom==0: raise RuntimeError("Q104_I19_REPRO_ASSETS_DENOMINATOR_ZERO")
    accr=num(n["value"])-num(c["value"]); intensity=accr/denom; state="POSITIVE_ACCRUAL" if intensity>0 else ("NEGATIVE_ACCRUAL" if intensity<0 else "ZERO_ACCRUAL")
    a=utc(str(f["acceptance_datetime"]))
    return {"filing_accession":str(f["accession"]),"filing_form":str(f["form"]).upper(),"acceptance_datetime":a.isoformat(),"eligible_xnys_session":session(a),"period_start":str(n["start"]),"period_end":end,"fiscal_period":str(n.get("fiscal_period","")),"prior_assets_instant":str(prior[-1]["instant"]),"accrual_amount":str(accr),"accrual_intensity":str(intensity),"accrual_state":state,"missingness":"COMPLETE"}
def institutional(ts:list[dict[str,Any]],symbol:str,cutoff:dt.datetime)->dict[str,Any]:
    rows=[dict(x) for x in ts if str(x.get("symbol") or "").upper()==symbol.upper() and x.get("acceptance_datetime") and utc(str(x["acceptance_datetime"]))<=cutoff]
    if not rows: return {"state":"MISSING","period_of_report":None,"increase_new_count":0,"decrease_exit_count":0,"eligible_transition_count":0}
    periods=sorted({str(x["period_of_report"]) for x in rows if x.get("period_of_report")});
    if not periods: return {"state":"MISSING","period_of_report":None,"increase_new_count":0,"decrease_exit_count":0,"eligible_transition_count":0}
    period=periods[-1]; selected=[x for x in rows if str(x.get("period_of_report"))==period]
    pos=sum(x.get("state") in {"INCREASE","NEW"} for x in selected); neg=sum(x.get("state") in {"DECREASE","EXIT"} for x in selected); net=pos-neg; latest=max(utc(str(x["acceptance_datetime"])) for x in selected)
    state="POSITIVE_INSTITUTIONAL_DEMAND" if net>0 else ("NEGATIVE_INSTITUTIONAL_DEMAND" if net<0 else "ZERO_INSTITUTIONAL_DEMAND")
    return {"state":state,"period_of_report":period,"increase_new_count":pos,"decrease_exit_count":neg,"eligible_transition_count":len(selected),"latest_transition_acceptance_datetime":latest.isoformat(),"latest_transition_eligible_xnys_session":session(latest)}
def build():
    r,b=inputs(); filings=b.get("filings",[]); ts=b.get("transitions",[]); targets=sorted({(str(x["symbol"]).upper(),str(x["acceptance_datetime"])) for x in b.get("13f_positions",[])})
    out=[]
    for sym,cut in targets:
        cutoff=utc(cut); accepted=[f for f in filings if str(f.get("symbol") or "").upper()==sym and str(f.get("form") or "").upper() in {"10-K","10-Q"} and utc(str(f["acceptance_datetime"]))<=cutoff]
        accepted.sort(key=lambda f:(utc(str(f["acceptance_datetime"])),str(f["accession"])))
        if not accepted: raise RuntimeError("Q104_I19_REPRO_NO_ACCEPTED_FILING")
        fs=filing_state(accepted[-1]); ins=institutional(ts,sym,cutoff)
        if ins["state"]=="MISSING": raise RuntimeError("Q104_I19_REPRO_MISSING_INSTITUTIONAL_STATE")
        out.append({"symbol":sym,"status":"COMPLETE","filing_state":fs,"institutional_state":ins,"decision_cutoff":cut})
    expected=b.get("joined_states",[]); emap={(str(x.get("symbol")).upper(),str(x.get("decision_cutoff"))):x for x in expected}
    if len(out)!=len(expected): raise RuntimeError("Q104_I19_REPRO_JOIN_COUNT_MISMATCH")
    mismatches=[]
    for x in out:
        ref=emap.get((x["symbol"],x["decision_cutoff"])); reduced={"symbol":ref.get("symbol"),"status":ref.get("status"),"filing_state":ref.get("filing_state"),"institutional_state":ref.get("institutional_state"),"decision_cutoff":ref.get("decision_cutoff")} if ref else None
        if reduced is None or canon(x)!=canon(reduced): mismatches.append((x["symbol"],x["decision_cutoff"]))
    if mismatches: raise RuntimeError("Q104_I19_REPRO_STATE_MISMATCH:"+json.dumps(mismatches[:10]))
    shuffled=[]
    for sym,cut in list(reversed(targets)):
        cutoff=utc(cut); accepted=[f for f in reversed(filings) if str(f.get("symbol") or "").upper()==sym and str(f.get("form") or "").upper() in {"10-K","10-Q"} and utc(str(f["acceptance_datetime"]))<=cutoff]; accepted.sort(key=lambda f:(utc(str(f["acceptance_datetime"])),str(f["accession"])))
        shuffled.append({"symbol":sym,"status":"COMPLETE","filing_state":filing_state(accepted[-1]),"institutional_state":institutional(list(reversed(ts)),sym,cutoff),"decision_cutoff":cut})
    if fp(out)!=fp(shuffled): raise RuntimeError("Q104_I19_REPRO_ORDER_INVARIANCE_FAILED")
    return {"schema_version":"1.0","record_type":"q104_i19_independent_pit_reproduction","candidate_id":"Q104:I19","status":"Q104_I19_INDEPENDENT_PIT_REPRODUCED","generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"upstream_receipts":{"compiler_receipt_fingerprint":r.get("receipt_fingerprint"),"bundle_fingerprint":b.get("bundle_fingerprint"),"census_receipt_fingerprint":r.get("census_receipt_fingerprint")},"joined_state_count":len(out),"reproduced_state_digest":fp(out),"invariance_checks":{"input_order":True,"future_observation_exclusion":False},"next_gate":"frozen preregistration + authorization reconcile","performance_authorized":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False,"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,default=OUTPUT); a=ap.parse_args(); result=build(); a.output.parent.mkdir(parents=True,exist_ok=True); result["receipt_fingerprint"]=fp(result); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(result,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
