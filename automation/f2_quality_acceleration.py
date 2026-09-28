"""F2 Quality-Acceleration PIT feasibility.

Builds gross-profitability level, one-period change, and second difference from
exact annual SEC filings. This is source/PIT feasibility only and never ranks
assets for performance.
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from automation.f1_profitability_feasibility import (
    ANNUAL_FORMS, CIK_MAP, COMPANYFACTS_URL, ROOT, SUBMISSIONS_URL,
    _fetch_json, _select_concept,
)
STUDY_START=date(2011,1,1); STUDY_END=date(2025,9,24)
SYMBOLS=("UPS","FDX","DIS","ADP","ORLY","AZO","TJX","RSG")
def _fp(value: object)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def _value(fact: dict[str,Any])->float:
    out=float(fact["row"]["val"])
    if not __import__("math").isfinite(out): raise ValueError("SEC XBRL fact value is not finite")
    return out
def _annual_rows(symbol:str)->list[dict[str,Any]]:
    cik=CIK_MAP[symbol]
    submissions=_fetch_json(SUBMISSIONS_URL.format(cik=cik))
    companyfacts=_fetch_json(COMPANYFACTS_URL.format(cik=cik))
    recent=submissions.get("filings",{}).get("recent",{})
    if not recent:return []
    size=len(next(iter(recent.values()))); rows=[]; seen=set()
    for i in range(size):
        row={k:recent[k][i] for k in recent}
        if row.get("form") not in ANNUAL_FORMS: continue
        accession=row.get("accessionNumber"); filing_date=row.get("filingDate"); acceptance=row.get("acceptanceDateTime"); report_date=row.get("reportDate")
        if not all(isinstance(x,str) and x for x in (accession,filing_date,acceptance,report_date)): continue
        filing_day=date.fromisoformat(filing_date)
        if not STUDY_START<=filing_day<=STUDY_END or accession in seen: continue
        seen.add(accession)
        filing={"accession":accession,"report_date":report_date}
        revenue=_select_concept(companyfacts,"revenue",filing,instant=False)
        cogs=_select_concept(companyfacts,"cogs",filing,instant=False)
        assets=_select_concept(companyfacts,"assets",filing,instant=True)
        if not all("row" in x for x in (revenue,cogs,assets)): continue
        rv,cv,av=_value(revenue),_value(cogs),_value(assets)
        if av==0: raise ValueError(f"{symbol}: assets are zero for {accession}")
        rows.append({"accession":accession,"form":row["form"],"filing_date":filing_date,"acceptance_datetime":acceptance,"report_date":report_date,"fiscal_year":row.get("fiscalYear"),"revenue_tag":revenue["tag"],"cogs_tag":cogs["tag"],"assets_tag":assets["tag"],"revenue":rv,"cogs":cv,"assets":av,"gross_profitability":(rv-cv)/av})
    rows.sort(key=lambda x:(x["acceptance_datetime"],x["accession"]))
    for i in range(1,len(rows)):
        if rows[i]["acceptance_datetime"]<=rows[i-1]["acceptance_datetime"]: raise ValueError(f"{symbol}: acceptance chronology is not strictly increasing")
        rows[i]["quality_growth"]=rows[i]["gross_profitability"]-rows[i-1]["gross_profitability"]
    for i in range(2,len(rows)):
        rows[i]["quality_acceleration"]=rows[i]["quality_growth"]-rows[i-1]["quality_growth"]
    return rows
def assess_symbol(symbol:str)->dict[str,Any]:
    rows=_annual_rows(symbol); acc=[r for r in rows if "quality_acceleration" in r]
    return {"symbol":symbol,"cik":CIK_MAP[symbol],"annual_fact_rows":len(rows),"complete_acceleration_rows":len(acc),"status":"COVERAGE_VALIDATED" if acc else "DATA_INSUFFICIENT","pit_anchor":"exact accession + report date + EDGAR acceptance chronology","future_filing_mutation_rule":"later filing cannot modify an earlier accession-bound observation","rows":rows}
def run(output:str|Path)->dict[str,Any]:
    details=[]; all_ok=True
    for symbol in SYMBOLS:
        try:item=assess_symbol(symbol)
        except Exception as exc:item={"symbol":symbol,"cik":CIK_MAP[symbol],"status":"DATA_INSUFFICIENT","error":str(exc)}
        details.append(item); all_ok &= item["status"]=="COVERAGE_VALIDATED"
    result={"schema_version":"1.0","task_id":"F2-QUALITY-ACCELERATION-SEC-PIT-FEASIBILITY-2026-09-28","recorded_at_utc":datetime.now(timezone.utc).isoformat(),"candidate":"F2_QUALITY_ACCELERATION","symbols":list(SYMBOLS),"study_window":{"start":STUDY_START.isoformat(),"end":STUDY_END.isoformat()},"definition":{"quality_level":"(revenue-cogs)/assets","quality_growth":"level_t-level_t-1","quality_acceleration":"growth_t-growth_t-1","timing":"latest exact annual filing accepted at or before decision timestamp"},"governance":{"performance_evaluation":False,"holdout_used":False,"selection_used":False,"parameter_search":False,"asset_search":False,"threshold_search":False,"performance_trial_authorized":False},"safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},"status":"COVERAGE_READY" if all_ok else "DATA_INSUFFICIENT","symbols_detail":details}
    result["fingerprint"]=_fp(result)
    path=Path(output); path=path if path.is_absolute() else ROOT/path
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"fingerprint":result["fingerprint"]},sort_keys=True)); return result
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--output",default="research/runs/f2_quality_acceleration/f2_source_pit_feasibility.json"); a=p.parse_args(); raise SystemExit(0 if run(a.output)["status"] in {"COVERAGE_READY","DATA_INSUFFICIENT"} else 1)
