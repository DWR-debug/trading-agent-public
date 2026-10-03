"""Q131-R1 SEC disclosure-complexity source/PIT feasibility probe.

Source/PIT only. No prices, returns, holdouts, ranking, tuning, performance,
promotion or live execution.

The probe uses SEC historical daily master indexes to identify a fixed,
deterministic sample of Q107 issuer filings, then parses only source-observable
structural fields from the filing-detail page/header.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import date
from html import unescape
from pathlib import Path

SYMBOLS=("SPGI","NDAQ","AMP","RJF","WMB","VLO","DVN","EMN")
FORMS=("8-K","8-K/A","10-Q","10-Q/A","10-K","10-K/A")
START="2025-09-22"
END="2025-09-24"
MAX_PER_ISSUER_FORM=2
UA="trading-agent-public/Q131R1-sec-disclosure-complexity/1"
INDEX_TEMPLATE="https://www.sec.gov/Archives/edgar/daily-index/{year}/QTR{quarter}/master.{yyyymmdd}.idx"

def sha256(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def get(url:str)->tuple[int,bytes,dict[str,str]]:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/plain,text/html,*/*"})
    try:
        with urllib.request.urlopen(req,timeout=45) as response:
            return int(getattr(response,"status",200)),response.read(),{k.lower():v for k,v in response.headers.items()}
    except urllib.error.HTTPError as exc:
        return int(exc.code),exc.read(),{}
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise RuntimeError(f"SEC_TRANSPORT_ERROR:{url}:{exc}") from exc

def qtr(month:int)->int:
    return ((month-1)//3)+1

def daily_index_url(day:str)->str:
    d=date.fromisoformat(day)
    return INDEX_TEMPLATE.format(year=d.year,quarter=qtr(d.month),yyyymmdd=d.strftime("%Y%m%d"))

def parse_master(body:bytes)->list[dict[str,str]]:
    rows=[]
    for raw in body.decode("latin-1").splitlines():
        line=raw.strip()
        if not line or "|" not in line:
            continue
        p=line.split("|",4)
        if len(p)!=5:
            continue
        cik,company,form,filed,filename=p
        if cik.isdigit() and form.upper() in FORMS and re.fullmatch(r"\d{4}-\d{2}-\d{2}",filed) and filename.startswith("edgar/data/"):
            rows.append({"cik":cik.zfill(10),"company_name":company,"form":form.upper(),"filed_date":filed,"filename":filename})
    return rows

def issuer_ciks()->dict[str,str]:
    status,body,_=get("https://www.sec.gov/files/company_tickers.json")
    if status!=200: raise RuntimeError(f"SEC_TICKERS_HTTP_{status}")
    payload=json.loads(body); out={}
    for row in payload.values():
        t=str(row.get("ticker","")).upper()
        if t in SYMBOLS:
            out[t]=str(row.get("cik_str","")).zfill(10)
    if set(out)!=set(SYMBOLS):
        raise RuntimeError(f"MISSING_ISSUER_CIK:{sorted(set(SYMBOLS)-set(out))}")
    return out

def accession_from_filename(filename:str)->str:
    matches=re.findall(r"/(\d{18})(?:/|-[^/]*)",filename)
    if not matches:
        raise ValueError(f"ACCESSION_NOT_FOUND:{filename}")
    raw=matches[0]
    return f"{raw[:10]}-{raw[10:12]}-{raw[12:]}"

def filing_index_url(filename:str)->str:
    parts=filename.split("/")
    if len(parts)<4: raise ValueError(f"BAD_FILENAME:{filename}")
    raw_dir=parts[-2]
    if not re.fullmatch(r"\d{18}",raw_dir):
        raise ValueError(f"BAD_ACCESSION_DIR:{filename}")
    accession=f"{raw_dir[:10]}-{raw_dir[10:12]}-{raw_dir[12:]}"
    directory="/".join(parts[:-1])
    return f"https://www.sec.gov/Archives/{directory}/{accession}-index.html"

def plain_text(html:str)->str:
    return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",unescape(html))).strip()

def parse_filing_detail(html:str)->dict[str,object]:
    text=plain_text(html)
    m=re.search(r"Documents\s+(\d+)",text,re.I)
    if not m: raise RuntimeError("SEC_DETAIL_DOCUMENTS_MISSING")
    row_match=re.search(r"<tr\b[^>]*>.*?PRIMARY DOCUMENT.*?</tr>",html,re.I|re.S)
    if not row_match: raise RuntimeError("SEC_PRIMARY_DOCUMENT_ROW_MISSING")
    primary_text=plain_text(row_match.group(0))
    nums=[int(x) for x in re.findall(r"\b\d{2,}\b",primary_text)]
    if not nums: raise RuntimeError("SEC_PRIMARY_DOCUMENT_SIZE_MISSING")
    size=nums[-1]
    data_match=re.search(r"Data Files.*?(?:Mailing Address|Business Address)",html,re.I|re.S)
    data_count=0 if not data_match else len(re.findall(r"<tr\b[^>]*>",data_match.group(0),re.I))-1
    if data_count<0: data_count=0
    return {
        "documents_count":int(m.group(1)),
        "primary_document_size_bytes":size,
        "data_files_count":data_count,
        "primary_document_ixbrl":"ixbrl" in primary_text.lower(),
    }

def extract_header_fields(html:str)->dict[str,str|None]:
    compact=unescape(html)
    def field(section:str)->str|None:
        pattern=r"SUBJECT COMPANY:.*?CENTRAL INDEX KEY:\s*(\d+)" if section=="subject" else r"FILED BY:.*?CENTRAL INDEX KEY:\s*(\d+)"
        m=re.search(pattern,compact,re.I|re.S)
        return m.group(1).zfill(10) if m else None
    acc=re.search(r"ACCEPTANCE-DATETIME:\s*(\d{14})",compact,re.I)
    accepted=None
    if acc:
        r=acc.group(1); accepted=f"{r[:4]}-{r[4:6]}-{r[6:8]} {r[8:10]}:{r[10:12]}:{r[12:14]}"
    else:
        m=re.search(r"Accepted\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",plain_text(html),re.I)
        accepted=m.group(1) if m else None
    return {"subject_cik":field("subject"),"filer_cik":field("filer"),"accepted_datetime":accepted}

def mutation_parse_invariance(html:str)->bool:
    a=parse_filing_detail(html)
    mutated=re.sub(r"\s+"," ",html)
    b=parse_filing_detail(mutated)
    return a==b

def run(output:Path)->dict[str,object]:
    ciks=issuer_ciks()
    candidates=[]
    cache={}
    for day in ("2025-09-22","2025-09-23","2025-09-24"):
        status,body,headers=get(daily_index_url(day))
        if status!=200: raise RuntimeError(f"SEC_DAILY_INDEX_HTTP_{status}:{day}")
        cache[day]={"sha256":sha256(body),"headers":headers,"rows":parse_master(body)}
    for symbol in sorted(SYMBOLS):
        for form in FORMS:
            rows=[r for day in cache.values() for r in day["rows"] if r["cik"]==ciks[symbol] and r["form"]==form and r["filed_date"]>=START and r["filed_date"]<=END]
            rows=sorted(rows,key=lambda r:(r["filename"],r["filed_date"]))[:MAX_PER_ISSUER_FORM]
            candidates.extend({"symbol":symbol,"issuer_cik":ciks[symbol],**r} for r in rows)
    if not candidates:
        result: dict[str, object] = {
            "schema_version": "1.0",
            "task_id": "Q-2026-10-03-131R1-SEC-DISCLOSURE-COMPLEXITY",
            "status": "Q131R1_FIXED_WINDOW_NO_MATCHING_FILINGS",
            "fixed_universe": SYMBOLS,
            "fixed_window": {"start": START, "end": END},
            "forms": FORMS,
            "sample_rule": {"max_per_issuer_form": MAX_PER_ISSUER_FORM, "order": "filename ascending"},
            "daily_index_dates_checked": len(cache),
            "filings_checked": 0,
            "daily_index_source_receipts": {
                day: {
                    "sha256": payload["sha256"],
                    "rows_scanned": len(payload["rows"]),
                }
                for day, payload in cache.items()
            },
            "observations": [],
            "negative_evidence": {
                "reason": "NO_MATCHING_FILINGS_IN_PREREGISTERED_WINDOW",
                "fixed_window": {"start": START, "end": END},
                "fixed_forms": list(FORMS),
            },
            "mutation_tests": {
                "html_whitespace_invariance": "NOT_RUN_NO_MATCHING_FILINGS",
            },
            "pit": {
                "exact_first_publication_time_proven": False,
                "immutable_revision_lineage_proven": False,
                "same_day_formal_use_allowed": False,
            },
            "governance": {
                "performance": False,
                "holdout": False,
                "selection": False,
                "ranking": False,
                "parameter_search": False,
                "threshold_search": False,
                "horizon_search": False,
                "asset_search": False,
                "variant_search": False,
                "performance_authorized": False,
                "automatic_promotion": False,
            },
            "safety": {
                "paper_only": True,
                "live_trading_enabled": False,
                "orders_enabled": False,
                "automatic_promotion": False,
            },
        }
        result["receipt_fingerprint"] = hashlib.sha256(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
    observations=[]
    for item in candidates:
        time.sleep(0.35)
        idx_url=filing_index_url(item["filename"])
        status,body,headers=get(idx_url)
        if status!=200: raise RuntimeError(f"SEC_FILING_INDEX_HTTP_{status}:{item['symbol']}:{item['filename']}")
        detail=plain_text(body.decode("utf-8",errors="replace"))
        header=extract_header_fields(body.decode("utf-8",errors="replace"))
        structural=parse_filing_detail(body.decode("utf-8",errors="replace"))
        accession=accession_from_filename(item["filename"])
        ok=(header["filer_cik"]==item["issuer_cik"] and header["subject_cik"] in (None,item["issuer_cik"]) and header["accepted_datetime"] is not None)
        if not ok:
            raise RuntimeError(f"Q131R1_IDENTITY_FAILED:{item['symbol']}:{accession}:{header}")
        observations.append({
            "symbol":item["symbol"],"issuer_cik":item["issuer_cik"],"filer_cik":header["filer_cik"],
            "subject_cik":header["subject_cik"],"accession_number":accession,"filing_date":item["filed_date"],
            "form":item["form"],"filing_index_url":idx_url,"index_sha256":sha256(body),
            **header,**structural,"http_headers":{"content_type":headers.get("content-type")}})
    mutation=mutation_parse_invariance(body.decode("utf-8",errors="replace"))
    result={
      "schema_version":"1.0","task_id":"Q-2026-10-03-131R1-SEC-DISCLOSURE-COMPLEXITY",
      "status":"Q131R1_SOURCE_COMPLEXITY_VECTOR_COMPLETED","fixed_universe":SYMBOLS,
      "fixed_window":{"start":START,"end":END},"forms":FORMS,
      "sample_rule":{"max_per_issuer_form":MAX_PER_ISSUER_FORM,"order":"filename ascending"},
      "daily_index_dates_checked":len(cache),"filings_checked":len(observations),
      "observations":observations,
      "mutation_tests":{"html_whitespace_invariance":mutation},
      "pit":{"exact_first_publication_time_proven":False,"immutable_revision_lineage_proven":False,"same_day_formal_use_allowed":False},
      "governance":{"performance":False,"holdout":False,"selection":False,"ranking":False,"parameter_search":False,"threshold_search":False,"horizon_search":False,"asset_search":False,"variant_search":False,"performance_authorized":False,"automatic_promotion":False},
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}}
    result["receipt_fingerprint"]=hashlib.sha256(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); r=run(a.output)
    print(json.dumps({"status":r["status"],"filings_checked":r["filings_checked"],"receipt_fingerprint":r["receipt_fingerprint"]},sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
