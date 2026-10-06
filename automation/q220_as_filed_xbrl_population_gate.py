"""Q220 clean source/PIT repair: historical as-filed SEC XBRL population."""
from __future__ import annotations
import argparse, hashlib, json, re, threading, time, urllib.error, urllib.request
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

TARGET_ISSUERS={"SPGI":"0000064040","NDAQ":"0001120193","AMP":"0000820027","RJF":"0000720005","WMB":"0000107263","VLO":"0001035002","DVN":"0001090012","EMN":"0000915389"}
FORMS={"10-K","10-K/A"}; WINDOW_START=date(2019,1,1); WINDOW_END=date(2025,9,24); ROUTE_QUARTERS=((2025,1),(2025,2),(2025,3))
UA="DWR-debug/trading-agent-public Q220 as-filed XBRL repair/1.0 research@example.invalid"; GAP=0.22

def sha256(data:bytes)->str: return hashlib.sha256(data).hexdigest()

class Limiter:
    def __init__(self,gap:float=GAP): self.gap=gap; self.lock=threading.Lock(); self.next_allowed=0.0
    def wait(self):
        with self.lock:
            now=time.monotonic()
            if now<self.next_allowed: time.sleep(self.next_allowed-now)
            self.next_allowed=time.monotonic()+self.gap
LIMITER=Limiter()

def fetch(url:str,retries:int=3)->tuple[int,bytes]:
    last=""
    for attempt in range(retries):
        LIMITER.wait()
        req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,text/plain,application/json,application/xml,*/*","Accept-Encoding":"identity"})
        try:
            with urllib.request.urlopen(req,timeout=60) as r: return int(getattr(r,"status",200)),r.read()
        except urllib.error.HTTPError as exc:
            status=int(exc.code); last=f"HTTP_{status}"; body=exc.read()
            if status not in {429,500,502,503,504} or attempt==retries-1: return status,body
        except (urllib.error.URLError,TimeoutError,OSError) as exc: last=repr(exc)
        if attempt+1<retries: time.sleep(min(8.0,2.0**attempt))
    raise RuntimeError(f"SEC_TRANSPORT_FAILED:{url}:{last}")

def master_url(year:int,q:int)->str: return f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{q}/master.idx"
def archive_base(cik:str,acc:str)->str: return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}"

def parse_master(body:bytes)->list[dict[str,str]]:
    out=[]
    for line in body.decode("latin-1",errors="replace").splitlines():
        if "|" not in line: continue
        p=line.strip().split("|",4)
        if len(p)!=5: continue
        cik,company,form,filed,filename=[x.strip() for x in p]
        if cik.zfill(10) not in TARGET_ISSUERS.values() or form.upper() not in FORMS: continue
        try: d=date.fromisoformat(filed)
        except ValueError: continue
        if not(WINDOW_START<=d<=WINDOW_END) or not filename.startswith("edgar/data/"): continue
        m=re.search(r"(\d{10}-\d{2}-\d{6})",filename)
        if not m: continue
        out.append({"cik":cik.zfill(10),"company_name":company,"form":form.upper(),"filed_date":filed,"filename":filename,"accession":m.group(1)})
    return sorted({(x["cik"],x["accession"]):x for x in out}.values(),key=lambda x:(x["cik"],x["filed_date"],x["accession"],x["form"]))

def load_quarters(quarters):
    rows=[]; receipts=[]
    for year,q in quarters:
        url=master_url(year,q); status,body=fetch(url)
        if status!=200: raise RuntimeError(f"MASTER_INDEX_HTTP_{status}:{url}")
        parsed=parse_master(body); rows.extend(parsed)
        receipts.append({"year":year,"quarter":q,"url":url,"http_status":status,"sha256":sha256(body),"bytes":len(body),"matching_rows":len(parsed)})
    return rows,receipts

def parse_acceptance(header:bytes)->str|None:
    m=re.search(rb"ACCEPTANCE-DATETIME\s*[:=>]?\s*(\d{14})",header,re.I)
    if not m: return None
    raw=m.group(1).decode(); return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}T{raw[8:10]}:{raw[10:12]}:{raw[12:14]}Z"

def parse_items(body:bytes)->list[str]:
    obj=json.loads(body.decode("utf-8",errors="replace"))
    return [str(x["name"]) for x in ((obj.get("directory") or {}).get("item") or []) if isinstance(x,dict) and isinstance(x.get("name"),str)]

def local_name(qname:str)->str: return qname.split(":",1)[-1]
def nsmap(text:str)->dict[str,str]: return {p:u for p,u in re.findall(r'xmlns:([A-Za-z_][\w.-]*)=["\']([^"\']+)["\']',text,re.I)}

def ix_textblocks(html:bytes)->list[dict[str,object]]:
    text=html.decode("utf-8",errors="replace"); prefixes=nsmap(text); out=[]
    for m in re.finditer(r"<ix:nonNumeric\b([^>]*)>",text,re.I|re.S):
        attrs=dict(re.findall(r'([A-Za-z_:][\w:.-]*)\s*=\s*["\']([^"\']*)["\']',m.group(1),re.I|re.S))
        name=attrs.get("name")
        if not name or not local_name(name).lower().endswith("textblock"): continue
        prefix=name.split(":",1)[0] if ":" in name else ""
        out.append({"qname":name,"local_name":local_name(name),"namespace":prefixes.get(prefix),"context_ref":attrs.get("contextref"),"fact_id":attrs.get("id")})
    return out

def xsd_metadata(body:bytes)->dict[str,object]:
    text=body.decode("utf-8",errors="replace"); m=re.search(r'targetNamespace\s*=\s*["\']([^"\']+)["\']',text,re.I)
    elems=sorted(set(re.findall(r'<(?:xsd|xs):element\b[^>]*\bname=["\']([^"\']+)["\']',text,re.I)))
    tb=sorted(x for x in elems if x.lower().endswith("textblock"))
    return {"target_namespace":m.group(1) if m else None,"element_count":len(elems),"textblock_element_count":len(tb),"textblock_elements":tb[:500],"sha256":sha256(body)}

def presentation_metadata(body:bytes)->dict[str,object]:
    text=body.decode("utf-8",errors="replace")
    roles=sorted(set(re.findall(r'(?:xlink:role|role)\s*=\s*["\']([^"\']+)["\']',text,re.I)))
    arcs=re.findall(r'<(?:link:)?presentationArc\b[^>]*(?:>|/>)',text,re.I); endpoints=[]
    for arc in arcs:
        for key in ("xlink:from","xlink:to","from","to"):
            m=re.search(re.escape(key)+r'\s*=\s*["\']([^"\']+)["\']',arc,re.I)
            if m: endpoints.append(m.group(1))
    return {"sha256":sha256(body),"role_count":len(roles),"presentation_arc_count":len(arcs),"endpoint_count":len(endpoints),"roles":roles[:200],"endpoints":sorted(set(endpoints))[:1000]}

def submission_primary_map(cik:str)->dict[str,str]:
    status,body=fetch(f"https://data.sec.gov/submissions/CIK{cik}.json")
    if status!=200: raise RuntimeError(f"SUBMISSIONS_HTTP_{status}:{cik}")
    recent=((json.loads(body.decode("utf-8",errors="replace")).get("filings") or {}).get("recent") or {}); out={}
    for acc,form,doc,fd in zip(recent.get("accessionNumber",[]),recent.get("form",[]),recent.get("primaryDocument",[]),recent.get("filingDate",[])):
        if form in FORMS and fd<=WINDOW_END.isoformat(): out[str(acc)]=str(doc)
    return out

def choose_primary(items:list[str],preferred:str|None)->str|None:
    if preferred and preferred in items: return preferred
    c=[n for n in items if n.lower().endswith((".htm",".html")) and "index" not in n.lower()]
    return sorted(c)[0] if c else None

def inspect(row:dict[str,str],pmap:dict[str,str])->dict[str,object]:
    base=archive_base(row["cik"],row["accession"]); acc=row["accession"]
    sh,h=fetch(f"{base}/{acc}-index-headers.html")
    if sh!=200: raise RuntimeError(f"HEADER_HTTP_{sh}:{acc}")
    accepted=parse_acceptance(h)
    if not accepted: raise RuntimeError(f"MISSING_ACCEPTANCE_DATETIME:{acc}")
    sd,d=fetch(f"{base}/index.json")
    if sd!=200: raise RuntimeError(f"DIRECTORY_HTTP_{sd}:{acc}")
    items=parse_items(d); primary=choose_primary(items,pmap.get(acc))
    if not primary: raise RuntimeError(f"PRIMARY_DOCUMENT_NOT_FOUND:{acc}")
    sp,p=fetch(f"{base}/{primary}")
    if sp!=200: raise RuntimeError(f"PRIMARY_HTTP_{sp}:{acc}")
    xsd_names=sorted(n for n in items if n.lower().endswith(".xsd")); pre_names=sorted(n for n in items if n.lower().endswith(("_pre.xml","-pre.xml")))
    xml_names=sorted(n for n in items if n.lower().endswith(".xml") and not any(n.lower().endswith(s) for s in ("_pre.xml","-pre.xml","_cal.xml","-cal.xml","_def.xml","-def.xml","_lab.xml","-lab.xml","_ref.xml","-ref.xml")))
    if not xsd_names: raise RuntimeError(f"XSD_NOT_FOUND:{acc}")
    if not pre_names: raise RuntimeError(f"PRESENTATION_NOT_FOUND:{acc}")
    sx,xsd=fetch(f"{base}/{xsd_names[0]}"); sp2,pre=fetch(f"{base}/{pre_names[0]}")
    if sx!=200: raise RuntimeError(f"XSD_HTTP_{sx}:{acc}")
    if sp2!=200: raise RuntimeError(f"PRE_HTTP_{sp2}:{acc}")
    instance_name=xml_names[0] if xml_names and fetch(f"{base}/{xml_names[0]}")[0]==200 else None
    tb=ix_textblocks(p); xm=xsd_metadata(xsd); pm=presentation_metadata(pre); endpoints=" ".join(pm["endpoints"]); locals_=sorted(set(x["local_name"] for x in tb))
    hits=sorted(x for x in locals_ if f"#{x}" in endpoints or x in endpoints)
    return {"canonical_key":{"cik":row["cik"],"form":row["form"],"filed_date":row["filed_date"],"accession":acc},"acceptance_datetime":accepted,
            "header_sha256":sha256(h),"directory_index_sha256":sha256(d),"primary_document":primary,"primary_document_sha256":sha256(p),
            "primary_document_bytes":len(p),"xsd":xsd_names[0],"xsd_metadata":xm,"presentation_linkbase":pre_names[0],"presentation_metadata":pm,
            "instance_document":instance_name,"instance_available":bool(instance_name),"textblock_fact_count":len(tb),
            "textblock_concepts":sorted(set(x["qname"] for x in tb)),"presentation_mapped_textblock_concepts":hits,
            "presentation_mapping_complete_for_observed_textblocks":bool(tb) and len(hits)>=len(locals_),"raw_archive_as_filed":True,
            "performance_authorization":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False}

def concept_spec()->dict[str,object]:
    return {"schema_version":"1.0","candidate_id":"Q220","status":"FROZEN_SOURCE_STRUCTURE_ONLY",
            "principle":"narrative-vs-structured representation gap, not generic length/sentiment/novelty",
            "narrative_fact_rule":{"element_kind":"ix:nonNumeric","local_name_suffix":"TextBlock","must_have_context_ref":True,"must_have_presentation_lineage":True},
            "structured_side":{"source":"same as-filed filing XBRL instance/inline facts",
              "exact_numeric_qnames":["us-gaap:Assets","us-gaap:OperatingIncomeLoss","us-gaap:NetIncomeLoss","us-gaap:NetCashProvidedByUsedInOperatingActivities","us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"],
              "substitution_allowed":False},
            "amendment_rule":"10-K is primary event population; 10-K/A retained only for explicit amendment lineage.","pit_clock":"SEC acceptance datetime from archived submission header","future_data_prohibited":True}

def run(mode:str,output:Path)->dict[str,object]:
    quarters=ROUTE_QUARTERS if mode=="route" else tuple((y,q) for y in range(2019,2026) for q in (1,2,3,4) if not(y==2025 and q==4))
    rows,quarter_receipts=load_quarters(quarters)
    if mode=="route":
        selected=[]
        for c in TARGET_ISSUERS.values():
            choices=sorted([x for x in rows if x["cik"]==c and x["form"]=="10-K"],key=lambda x:(x["filed_date"],x["accession"]))
            if not choices: raise RuntimeError(f"ROUTE_10K_NOT_FOUND:{c}")
            selected.append(choices[0])
        rows=selected
    pmaps={c:submission_primary_map(c) for c in TARGET_ISSUERS.values()}; records=[]; failures=[]
    for row in rows:
        try: records.append(inspect(row,pmaps[row["cik"]]))
        except Exception as exc: failures.append({"canonical_key":row,"error":str(exc)})
    records.sort(key=lambda r:(r["canonical_key"]["cik"],r["canonical_key"]["filed_date"],r["canonical_key"]["accession"]))
    by_cik=defaultdict(list)
    for r in records: by_cik[r["canonical_key"]["cik"]].append(r)
    summary={}
    for symbol,cik in TARGET_ISSUERS.items():
        rr=by_cik[cik]; originals=[r for r in rr if r["canonical_key"]["form"]=="10-K"]
        summary[symbol]={"original_10k_count":len(originals),"amendment_count":sum(r["canonical_key"]["form"]=="10-K/A" for r in rr),
                         "textblock_ready_originals":sum(bool(r["textblock_fact_count"] and r["presentation_mapping_complete_for_observed_textblocks"]) for r in originals),
                         "records_with_failures":sum(f["canonical_key"]["cik"]==cik for f in failures)}
    ready=(not failures and all(v["original_10k_count"]>=(1 if mode=="route" else 5) for v in summary.values()) and
           all(v["textblock_ready_originals"]>=(1 if mode=="route" else 5) for v in summary.values()))
    result={"schema_version":"1.0","task_id":f"Q-2026-10-06-Q220-AS-FILED-XBRL-{mode.upper()}","candidate_id":"Q220","mode":mode,
            "status":f"Q220_AS_FILED_XBRL_{mode.upper()}_COMPLETED" if ready else f"Q220_AS_FILED_XBRL_{mode.upper()}_BLOCKED",
            "generated_at_utc":datetime.now(timezone.utc).isoformat(),"fixed_universe":TARGET_ISSUERS,
            "window":{"start":WINDOW_START.isoformat(),"end":WINDOW_END.isoformat()},
            "source_route":{"master_index":"SEC quarterly full-index","raw_archive":"SEC Archives filing directory","acceptance_header":True,
                            "directory_index":"index.json","primary_document":True,"extension_taxonomy":True,"presentation_linkbase":True,"flattened_fsn_not_authoritative":True},
            "quarter_receipts":quarter_receipts,"row_count":len(rows),"record_count":len(records),"failure_count":len(failures),"failures":failures,"issuer_summary":summary,
            "concept_spec":concept_spec(),"records":records,
            "interpretation":{"source_pit_structure_ready":ready,"performance_evidence":False,"performance_authorized":False,"promotion_allowed":False},
            "governance":{"performance":False,"holdout":False,"selection":False,"ranking":False,"parameter_search":False,"threshold_search":False,"horizon_search":False,"promotion":False,"live_execution":False},
            "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}}
    result["receipt_fingerprint"]=sha256(json.dumps(result,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode())
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8"); return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--mode",choices=("route","population"),required=True); ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); r=run(a.mode,a.output); print(json.dumps({k:r[k] for k in ("status","mode","row_count","record_count","failure_count","receipt_fingerprint")},sort_keys=True))
if __name__=="__main__": main()
