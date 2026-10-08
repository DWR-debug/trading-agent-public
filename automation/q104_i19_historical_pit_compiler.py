"""Q104:I19 historical PIT materialization; pre-performance and fail-closed."""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,html.parser,io,json,re,time,urllib.error,urllib.request,xml.etree.ElementTree as ET,zipfile
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal
from pathlib import Path
from typing import Any

from automation.q104_i19_xbrl_pit_compiler import (
    EXACT_CONCEPTS,ELIGIBLE_FORMS,compile_issuer_state,compile_filing_state,
    parse_filing,parse_utc,fingerprint,
)
from automation.q114_13f_manager_transitions import compile_transitions
from automation.q111_security_identity_contract import canonical_security_key

ROOT=Path(__file__).resolve().parents[1]
CENSUS=ROOT/"research/evidence/q104_i19_13f_historical_identity_census_latest.json"
Q108=ROOT/"research/evidence/q108_pit_integration_2026_10_01.json"
COVERAGE=ROOT/"research/evidence/q113_13f_q107_coverage_result.json"
OUTPUT=ROOT/"research/evidence/q104_i19_historical_pit_compilation_latest.json"
BUNDLE=ROOT/"research/evidence/q104_i19_historical_compiler_input_bundle_latest.json"
START=dt.date(2013,7,1); CUTOFF=dt.date(2025,9,24)
UA="DWR-debug/trading-agent-public Q104-I19 historical PIT materializer/1.0"
GAP=.30; RETRIES=6; WORKERS=2

def fetch(url:str)->bytes:
    last=None
    for i in range(RETRIES):
        if i: time.sleep(min(60.,2.**(i-1)))
        else: time.sleep(GAP)
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json,text/html,application/xml,text/xml,*/*","Accept-Encoding":"identity","Connection":"close"})
            with urllib.request.urlopen(req,timeout=180) as r: return r.read()
        except urllib.error.HTTPError as e:
            last=e
            if e.code not in {408,425,429,500,502,503,504} or i==RETRIES-1: raise
            try: time.sleep(max(GAP,int((e.headers or {}).get("Retry-After","0"))))
            except (TypeError,ValueError): pass
        except (urllib.error.URLError,TimeoutError,OSError) as e: last=e
    raise last or RuntimeError("SEC_FETCH_FAILED")

def norm_cusip(v:str)->str: return re.sub(r"[^0-9A-Z]","",str(v or "").upper())
def field(row:dict[str,Any],name:str)->str:
    w=re.sub(r"[^A-Z0-9]","",name.upper())
    return next((str(v or "") for k,v in row.items() if re.sub(r"[^A-Z0-9]","",str(k).upper())==w),"")
def local_name(v:str)->str: return str(v).split(":",1)[-1].split("}",1)[-1].lower()

def require_census()->dict[str,Any]:
    if not CENSUS.exists(): raise RuntimeError("Q104_I19_CENSUS_RECEIPT_MISSING")
    r=json.loads(CENSUS.read_text(encoding="utf-8"))
    if r.get("candidate_id")!="Q104:I19": raise RuntimeError("Q104_I19_CENSUS_CANDIDATE_MISMATCH")
    if r.get("status")!="13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_COMPLETED_SOURCE_ONLY": raise RuntimeError("Q104_I19_CENSUS_NOT_POSITIVE")
    if set(r.get("completed_shards",[]))!={"2013-2017","2018-2021","2022-2025-09"}: raise RuntimeError("Q104_I19_CENSUS_SHARD_CLOSURE_FAILED")
    if r.get("identity_conflicts"): raise RuntimeError("Q104_I19_CENSUS_IDENTITY_CONFLICTS")
    j=r.get("acceptance_time_join",{})
    if j.get("complete") is not True or int(j.get("failures",0))!=0: raise RuntimeError("Q104_I19_CENSUS_ACCEPTANCE_JOIN_NOT_COMPLETE")
    if int(r.get("archive_count",0))<=0: raise RuntimeError("Q104_I19_CENSUS_ARCHIVE_COUNT_INVALID")
    return r

def load_maps()->tuple[dict[str,str],dict[str,str]]:
    q108=json.loads(Q108.read_text(encoding="utf-8"))
    ciks={str(k).upper():str(v).zfill(10) for k,v in q108.get("sec_ticker_mapping",{}).get("ciks",{}).items()}
    if len(ciks)!=8: raise RuntimeError("Q104_I19_Q108_CIK_MAP_NOT_EXACTLY_8")
    coverage=json.loads(COVERAGE.read_text(encoding="utf-8"))
    cm={}
    for sym,item in coverage.get("coverage",{}).items():
        for sk in item.get("security_keys",[]):
            sk=str(sk)
            if sk.upper().startswith("CUSIP:"):
                c=norm_cusip(sk.split(":",1)[1])
                if c and c in cm and cm[c]!=str(sym).upper(): raise RuntimeError("Q104_I19_CUSIP_SYMBOL_CONFLICT:"+c)
                if c: cm[c]=str(sym).upper()
    if not cm: raise RuntimeError("Q104_I19_FROZEN_CUSIP_MAP_EMPTY")
    return ciks,cm

def acceptance_map(census:dict[str,Any])->dict[str,dict[str,Any]]:
    out={}
    for a in census.get("archives",[]):
        for h in (a.get("target_hits",{}) or {}).values():
            for acc,rec in (h.get("acceptance_records",{}) or {}).items():
                if acc in out and out[acc]!=rec: raise RuntimeError("Q104_I19_ACCEPTANCE_RECORD_CONFLICT:"+acc)
                out[acc]=dict(rec)
    return out

def tsv(z:zipfile.ZipFile,suffix:str):
    names=[n for n in z.namelist() if n.lower().endswith(suffix.lower())]
    if not names: raise RuntimeError("SEC_MEMBER_NOT_FOUND:"+suffix)
    return csv.DictReader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8-sig",newline=""),delimiter="\t")

def materialize_13f(blob:bytes,target:dict[str,str],archive:dict[str,Any],accepted:dict[str,dict[str,Any]])->list[dict[str,Any]]:
    out=[]
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for row in tsv(z,"infotable.tsv"):
            cusip=norm_cusip(field(row,"CUSIP")); sym=target.get(cusip)
            if not sym: continue
            acc=field(row,"ACCESSION_NUMBER"); rec=accepted.get(acc)
            if not rec: raise RuntimeError("Q104_I19_TARGET_ACCESSION_ACCEPTANCE_MISSING:"+acc)
            shares=field(row,"SSHPRNAMT").replace(",",""); value=field(row,"VALUE").replace(",","")
            if not shares or not value: raise RuntimeError("Q104_I19_POSITION_NUMERIC_FIELD_MISSING:"+acc+":"+cusip)
            Decimal(shares); Decimal(value)
            out.append({
                "symbol":sym,"manager_cik":str(rec["filer_cik"]).zfill(10),"accession":acc,
                "acceptance_datetime":str(rec["acceptance_datetime"]),"period_of_report":str(rec["period"]),
                "name_of_issuer":field(row,"NAMEOFISSUER"),"title_of_class":field(row,"TITLEOFCLASS"),
                "cusip":cusip,
                "security_key":canonical_security_key({"name_of_issuer":field(row,"NAMEOFISSUER"),"title_of_class":field(row,"TITLEOFCLASS"),"cusip":cusip}),
                "shares":shares,"reported_value":value,
                "shares_unit":field(row,"SSHPRNAMTTYPE") or "UNSPECIFIED",
                "reported_value_unit":"USD_THOUSANDS_AS_REPORTED_BY_13F",
                "archive_url":archive["archive"]["url"],"archive_sha256":archive["archive_sha256"],
            })
    return out

def filing_rows(sub:dict[str,Any])->list[dict[str,Any]]:
    out=[]
    recent=sub.get("filings",{}).get("recent",{})
    if isinstance(recent,dict):
        n=len(recent.get("accessionNumber",[])); keys=list(recent.keys())
        for i in range(n):
            r={k:recent.get(k,[])[i] for k in keys if i<len(recent.get(k,[]))}
            if str(r.get("form","")).upper() in ELIGIBLE_FORMS and r.get("acceptanceDateTime"):
                try: d=dt.date.fromisoformat(str(r.get("filingDate"))[:10])
                except ValueError: continue
                if START<=d<=CUTOFF: out.append(r)
    for item in sub.get("filings",{}).get("files",[]) or []:
        name=item.get("name")
        if not name: continue
        h=json.loads(fetch("https://data.sec.gov/submissions/"+str(name)).decode("utf-8"))
        recent=h.get("filings",h); n=len(recent.get("accessionNumber",[])); keys=list(recent.keys())
        for i in range(n):
            r={k:recent.get(k,[])[i] for k in keys if i<len(recent.get(k,[]))}
            if str(r.get("form","")).upper() not in ELIGIBLE_FORMS or not r.get("acceptanceDateTime"): continue
            try: d=dt.date.fromisoformat(str(r.get("filingDate"))[:10])
            except ValueError: continue
            if START<=d<=CUTOFF: out.append(r)
    return sorted({str(r["accessionNumber"]):r for r in out}.values(),key=lambda r:(str(r["acceptanceDateTime"]),str(r["accessionNumber"])))

def archive_base(cik:str,acc:str)->str:
    return f"https://www.sec.gov/Archives/edgar/data/{int(str(cik).zfill(10))}/{str(acc).replace('-','')}"

def numeric_clean(v:str,sign:str="",scale:str="0")->str:
    raw=re.sub(r"\s+","",str(v or "")).replace(",","").replace("$","")
    if raw.startswith("(") and raw.endswith(")"): raw="-"+raw[1:-1]
    if sign=="-" and not raw.startswith("-"): raw="-"+raw
    return str(Decimal(raw)*Decimal(10)**int(scale or "0"))

class InlineFacts(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.current=None; self.depth=0; self.facts=[]
    def handle_starttag(self,tag,attrs):
        low=local_name(tag)
        if self.current is not None: self.depth+=1
        if low=="nonfraction" and self.current is None:
            self.current={"a":{str(k).lower():str(v or "") for k,v in attrs},"t":[]}; self.depth=0
    def handle_data(self,data):
        if self.current is not None: self.current["t"].append(data)
    def handle_endtag(self,tag):
        if self.current is None: return
        low=local_name(tag)
        if low=="nonfraction" and self.depth==0:
            a=self.current["a"]; self.facts.append({"name":a.get("name",""),"contextRef":a.get("contextref",""),"unitRef":a.get("unitref",""),"scale":a.get("scale","0"),"sign":a.get("sign",""),"text":"".join(self.current["t"])})
            self.current=None; self.depth=0
        else: self.depth=max(0,self.depth-1)

def contexts_from_html(text:str)->dict[str,dict[str,Any]]:
    out={}
    pat=r"<(?:[\\w.-]+:)?context\\b[^>]*?\\bid=[\"']([^\"']+)[\"'][^>]*>(.*?)</(?:[\\w.-]+:)?context\\s*>"
    for m in re.finditer(pat,text,flags=re.I|re.S):
        frag=m.group(2)
        im=re.search(r"<[^>]*instant\\b[^>]*>\\s*([^<]+)\\s*</[^>]*instant\\s*>",frag,flags=re.I)
        sm=re.search(r"<[^>]*startDate\\b[^>]*>\\s*([^<]+)\\s*</[^>]*startDate\\s*>",frag,flags=re.I)
        em=re.search(r"<[^>]*endDate\\b[^>]*>\\s*([^<]+)\\s*</[^>]*endDate\\s*>",frag,flags=re.I)
        dims=re.findall(r"<[^>]*?(?:explicitMember|typedMember)\\b",frag,flags=re.I)
        out[m.group(1)]={"instant":im.group(1).strip() if im else None,"start":sm.group(1).strip() if sm else None,"end":em.group(1).strip() if em else None,"dimensions":["dimension"]*len(dims)}
    return out

def inline_facts(body:bytes)->list[dict[str,Any]]:
    text=body.decode("utf-8","replace"); contexts=contexts_from_html(text); p=InlineFacts(); p.feed(text); out=[]
    for raw in p.facts:
        name=str(raw["name"])
        if name not in EXACT_CONCEPTS.values(): continue
        c=contexts.get(raw["contextRef"])
        if not c: continue
        unit=raw["unitRef"]; unit="USD" if unit.upper() in {"USD","ISO4217:USD"} else unit
        try: value=numeric_clean(raw["text"],raw["sign"],raw["scale"])
        except Exception: continue
        out.append({"concept":name,"unit":unit,"value":value,"start":c["start"],"end":c["end"],"instant":c["instant"],"fiscal_period":None,"dimensions":c["dimensions"],"consolidated":not bool(c["dimensions"])})
    return out

def xml_facts(body:bytes)->list[dict[str,Any]]:
    root=ET.fromstring(body); contexts={}; units={}
    for e in root.iter():
        ln=local_name(e.tag)
        if ln=="context":
            cid=str(e.attrib.get("id","")); instant=start=end=None; dims=[]
            for x in e.iter():
                l=local_name(x.tag)
                if l=="instant": instant=(x.text or "").strip()
                elif l=="startdate": start=(x.text or "").strip()
                elif l=="enddate": end=(x.text or "").strip()
                elif l in {"explicitmember","typedmember"}: dims.append(l)
            contexts[cid]={"instant":instant,"start":start,"end":end,"dimensions":dims}
        elif ln=="unit":
            units[str(e.attrib.get("id",""))]="".join(e.itertext()).strip()
    cmap={"netincomeloss":EXACT_CONCEPTS["net_income_loss"],"netcashprovidedbyusedinoperatingactivities":EXACT_CONCEPTS["operating_cash_flow"],"assets":EXACT_CONCEPTS["assets"]}
    out=[]
    for e in root.iter():
        ln=local_name(e.tag)
        if ln not in cmap: continue
        tag=str(e.tag)
        if tag.startswith("{") and "fasb.org/us-gaap/" not in tag: continue
        c=contexts.get(str(e.attrib.get("contextRef",""))); 
        if not c: continue
        u=units.get(str(e.attrib.get("unitRef","")),str(e.attrib.get("unitRef","")))
        unit="USD" if re.search(r"(?:^|:)USD(?:$|\\s)",u,re.I) and "shares" not in u.lower() else u
        try: value=str(Decimal("".join(e.itertext()).replace(",","")))
        except Exception: continue
        out.append({"concept":cmap[ln],"unit":unit,"value":value,"start":c["start"],"end":c["end"],"instant":c["instant"],"fiscal_period":None,"dimensions":c["dimensions"],"consolidated":not bool(c["dimensions"])})
    return out

def choose_instances(index:dict[str,Any])->list[str]:
    out=[]
    for item in index.get("directory",{}).get("item",[]) or []:
        n=str(item.get("name","")); low=n.lower()
        if not low.endswith(".xml") or low.endswith(".xsd"): continue
        if any(x in low for x in ("-cal.xml","-def.xml","-lab.xml","-pre.xml","-ref.xml","filingsummary.xml")): continue
        out.append(n)
    return out

def filing_facts(symbol:str,cik:str,row:dict[str,Any])->dict[str,Any]:
    acc=str(row["accessionNumber"]); base=archive_base(cik,acc)
    out={"symbol":symbol,"cik":str(cik).zfill(10),"accession":acc,"form":str(row.get("form","")).upper(),"acceptance_datetime":str(row["acceptanceDateTime"]),"filing_date":str(row.get("filingDate")),"report_date":row.get("reportDate"),"fiscal_period":row.get("fp"),"source_base":base}
    body=None; url=None; facts=[]; errors=[]
    if row.get("primaryDocument") and bool(row.get("isInlineXBRL")):
        url=f"{base}/{row['primaryDocument']}"
        try: body=fetch(url); facts=inline_facts(body)
        except Exception as e: errors.append("inline:"+type(e).__name__+":"+str(e))
    if not facts:
        index_url=f"{base}/index.json"; idx=None
        try: idx=json.loads(fetch(index_url).decode("utf-8"))
        except Exception:
            for suffix in (f"{acc}-index.html",f"{acc}-index.htm"):
                try:
                    h=fetch(f"{base}/{suffix}").decode("utf-8","replace")
                    names=re.findall(r'href=["\']([^"\']+\\.xml)["\']',h,flags=re.I)
                    idx={"directory":{"item":[{"name":n.split("/")[-1]} for n in names]}}; break
                except Exception as e: errors.append("index:"+type(e).__name__)
        if idx:
            for inst in choose_instances(idx):
                try:
                    url=f"{base}/{inst}"; body=fetch(url); facts=xml_facts(body)
                    if facts: break
                except Exception as e: errors.append("xml:"+inst+":"+type(e).__name__)
    for f in facts: f["fiscal_period"]=out["fiscal_period"]
    out.update({"facts":facts,"source_url":url,"source_sha256":hashlib.sha256(body).hexdigest() if body is not None else None,"errors":errors})
    try:
        state=compile_filing_state(parse_filing(out)); out["compile_state"]=state; out["eligible_complete_for_latest_selection"]=True
    except Exception as e:
        out["compile_state"]=None; out["eligible_complete_for_latest_selection"]=False; out["compile_error"]=type(e).__name__+":"+str(e)
    return out

def build()->tuple[dict[str,Any],dict[str,Any]]:
    census=require_census(); ciks,cusips=load_maps(); accepted=acceptance_map(census)
    positions=[]
    for a in census.get("archives",[]):
        blob=fetch(str(a["archive"]["url"])); digest=hashlib.sha256(blob).hexdigest()
        if digest!=str(a.get("archive_sha256")): raise RuntimeError("Q104_I19_ARCHIVE_SHA_MISMATCH:"+str(a["archive"]["url"]))
        positions.extend(materialize_13f(blob,cusips,a,accepted))
    if not positions: raise RuntimeError("Q104_I19_NO_TARGET_13F_POSITIONS")
    filings=[]
    counts={}
    for sym in sorted({p["symbol"] for p in positions}):
        sub=json.loads(fetch(f"https://data.sec.gov/submissions/CIK{ciks[sym]}.json").decode("utf-8")); rows=filing_rows(sub); counts[sym]=len(rows)
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            fs=list(ex.map(lambda r:filing_facts(sym,ciks[sym],r),rows))
        filings.extend(fs)
    transitions=compile_transitions(positions)
    sec_to_sym={}
    for p in positions: sec_to_sym[p["security_key"]]=p["symbol"]
    for x in transitions: x["symbol"]=sec_to_sym.get(x["security_key"])
    if any(x.get("symbol") not in counts for x in transitions): raise RuntimeError("Q104_I19_TRANSITION_SYMBOL_MAPPING_FAILED")
    complete=[f for f in filings if f.get("eligible_complete_for_latest_selection")]
    if not complete: raise RuntimeError("Q104_I19_NO_COMPLETE_XBRL_FILINGS")
    joined=[]; missing=[]
    for sym,acc_dt in sorted({(p["symbol"],p["acceptance_datetime"]) for p in positions}):
        fs=[f for f in complete if f["symbol"]==sym]
        r=compile_issuer_state(fs,transitions,symbol=sym,cutoff=parse_utc(acc_dt))
        r["decision_cutoff"]=acc_dt
        if r.get("status")!="COMPLETE": missing.append({"symbol":sym,"cutoff":acc_dt,"reason":r.get("reason")})
        else: joined.append(r)
    if missing: raise RuntimeError("Q104_I19_JOINED_STATE_MISSING:"+json.dumps(missing[:10],sort_keys=True))
    bundle={
      "schema_version":"1.0","record_type":"q104_i19_historical_compiler_input_bundle","candidate_id":"Q104:I19",
      "generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"census_receipt_fingerprint":census["receipt_fingerprint"],
      "frozen_cusip_map":dict(sorted(cusips.items())),"symbols":sorted(counts),
      "window":{"start":START.isoformat(),"cutoff":CUTOFF.isoformat()},
      "13f_position_count":len(positions),"13f_positions":sorted(positions,key=lambda x:(x["acceptance_datetime"],x["symbol"],x["manager_cik"],x["security_key"],x["accession"])),
      "transition_count":len(transitions),"transitions":sorted(transitions,key=lambda x:(x["symbol"],x["acceptance_datetime"],x["manager_cik"],x["security_key"],x["accession"])),
      "filing_counts":counts,"complete_filing_counts":{s:sum(1 for f in filings if f["symbol"]==s and f.get("eligible_complete_for_latest_selection")) for s in counts},
      "filings":filings,"joined_state_count":len(joined),"joined_states":joined,
      "scientific_boundary":{"performance_authorized":False,"holdout_selection_allowed":False,"ranking_allowed":False,"parameter_search_allowed":False,"threshold_search_allowed":False,"horizon_search_allowed":False,"promotion_allowed":False,"live_execution_allowed":False},
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
    }
    bundle["bundle_fingerprint"]=fingerprint(bundle)
    receipt={
      "schema_version":"1.0","record_type":"q104_i19_historical_pit_compilation","candidate_id":"Q104:I19",
      "status":"Q104_I19_HISTORICAL_PIT_COMPILATION_COMPLETED_NO_PERFORMANCE","generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "census_receipt_fingerprint":census["receipt_fingerprint"],"bundle_fingerprint":bundle["bundle_fingerprint"],
      "symbols":sorted(counts),"13f_position_count":len(positions),"transition_count":len(transitions),"joined_state_count":len(joined),
      "archive_count_rechecked":int(census["archive_count"]),"complete_filing_counts":bundle["complete_filing_counts"],
      "source_sha256s":sorted({f["source_sha256"] for f in filings if f.get("source_sha256")}),
      "next_gate":"independent PIT reproduction","historical_data_compiled":True,
      "governance":bundle["scientific_boundary"],"safety":bundle["safety"],
    }
    receipt["receipt_fingerprint"]=fingerprint(receipt); return bundle,receipt

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=OUTPUT); p.add_argument("--bundle",type=Path,default=BUNDLE); a=p.parse_args()
    bundle,receipt=build(); a.bundle.parent.mkdir(parents=True,exist_ok=True); a.output.parent.mkdir(parents=True,exist_ok=True)
    a.bundle.write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
    a.output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
    print(json.dumps({"status":receipt["status"],"receipt_fingerprint":receipt["receipt_fingerprint"],"bundle_fingerprint":receipt["bundle_fingerprint"],"positions":receipt["13f_position_count"],"transitions":receipt["transition_count"],"joined_states":receipt["joined_state_count"]},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
