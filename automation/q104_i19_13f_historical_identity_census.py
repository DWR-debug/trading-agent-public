"""Q104:I19 historical SEC 13F identity/archive census; source/PIT only."""
from __future__ import annotations
import argparse,csv,hashlib,html.parser,io,json,re,time,urllib.request,zipfile
from datetime import date,datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGE="https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets"
EVIDENCE=ROOT/"research/evidence/q113_13f_q107_coverage_result.json"
START=date(2013,7,1); END=date(2025,10,1); CUTOFF=date(2025,9,24)
SHARDS={"2013-2017":(date(2013,7,1),date(2018,1,1)),
        "2018-2021":(date(2018,1,1),date(2022,1,1)),
        "2022-2025-09":(date(2022,1,1),END)}
UA="DWR-debug/trading-agent-public Q104-I19 historical 13F census/1.0"

class LinkParser(html.parser.HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.h=None; self.buf=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a": self.h=next((v for k,v in attrs if k.lower()=="href" and v),None); self.buf=[]
    def handle_data(self,data):
        if self.h is not None:self.buf.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=="a" and self.h is not None:
            self.links.append((self.h," ".join(self.buf).strip())); self.h=None; self.buf=[]

def norm_cusip(v): return re.sub(r"[^0-9A-Z]","",str(v or "").upper())

def parse_date(v):
    for fmt in ("%Y-%m-%d","%d-%b-%Y","%d-%B-%Y","%m/%d/%Y"):
        try:return datetime.strptime(str(v).strip(),fmt).date()
        except ValueError: pass
    raise ValueError("SEC_DATE_UNPARSEABLE:"+str(v))

def parse_period_start(url):
    n=url.rsplit("/",1)[-1].lower()
    m=re.search(r"(20\d{2})q([1-4])_form13f\.zip$",n)
    if m:return date(int(m.group(1)),{1:1,2:4,3:7,4:10}[int(m.group(2))],1)
    months={"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
    m=re.match(r"(\d{2})(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(20\d{2})-",n)
    return date(int(m.group(3)),months[m.group(2)],int(m.group(1))) if m else None

def discover_archives(page):
    p=LinkParser(); p.feed(page.decode("utf-8","replace")); out={}
    for href,label in p.links:
        if not href.lower().endswith(".zip") or "form13f" not in href.lower(): continue
        if href.startswith("/"): href="https://www.sec.gov"+href
        if not href.startswith("https://www.sec.gov/"): continue
        start=parse_period_start(href)
        if start is not None and START<=start<END: out[href]={"url":href,"label":label,"period_start":start.isoformat()}
    return sorted(out.values(),key=lambda x:(x["period_start"],x["url"]))

def fetch(url,retries=4):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/zip,*/*","Accept-Encoding":"identity"})
            with urllib.request.urlopen(req,timeout=180) as r:return r.read()
        except Exception as e:
            last=e
            if i+1<retries:time.sleep(2**i)
    raise last

def field(row,name):
    wanted=re.sub(r"[^A-Z0-9]","",name.upper())
    for k,v in row.items():
        if re.sub(r"[^A-Z0-9]","",str(k).upper())==wanted:return str(v or "")
    return ""

def tsv(zf,suffix):
    name=next((n for n in zf.namelist() if n.lower().endswith(suffix.lower())),None)
    if name is None: raise ValueError("SEC_MEMBER_NOT_FOUND:"+suffix)
    return csv.DictReader(io.TextIOWrapper(zf.open(name),encoding="utf-8-sig",newline=""),delimiter="\t")

def frozen_cusips():
    payload=json.loads(EVIDENCE.read_text(encoding="utf-8"))
    return {s:{norm_cusip(str(k).split(":",1)[1]) for k in x.get("security_keys",[]) if str(k).upper().startswith("CUSIP:")}
            for s,x in payload.get("coverage",{}).items()}

def scan_archive(blob,archive,targets):
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        eligible={}
        for row in tsv(zf,"submission.tsv"):
            acc=field(row,"ACCESSION_NUMBER"); raw=field(row,"FILING_DATE")
            if not acc or not raw:continue
            try:d=parse_date(raw)
            except ValueError:continue
            if d<=CUTOFF: eligible[acc]={"filing_date":d.isoformat(),"period":field(row,"PERIODOFREPORT")}
        wanted={c:s for s,cs in targets.items() for c in cs}
        hits={s:{"row_count":0,"cusips":set(),"issuer_names":set(),"class_names":set(),"accessions":set(),"filing_dates":set(),"periods":set()} for s in targets}
        conflicts=set()
        for row in tsv(zf,"infotable.tsv"):
            acc=field(row,"ACCESSION_NUMBER")
            if acc not in eligible:continue
            c=norm_cusip(field(row,"CUSIP")); sym=wanted.get(c)
            if sym is None:continue
            if sum(c in cs for cs in targets.values())>1: conflicts.add(c)
            h=hits[sym]; h["row_count"]+=1; h["cusips"].add(c); h["issuer_names"].add(field(row,"NAMEOFISSUER"))
            h["class_names"].add(field(row,"TITLEOFCLASS")); h["accessions"].add(acc); h["filing_dates"].add(eligible[acc]["filing_date"]); h["periods"].add(eligible[acc]["period"])
    for h in hits.values():
        for k in ("cusips","issuer_names","class_names","accessions","filing_dates","periods"): h[k]=sorted(x for x in h[k] if x)
    return {"archive":archive,"archive_sha256":hashlib.sha256(blob).hexdigest(),"archive_bytes":len(blob),"target_hits":hits,"security_identity_conflicts":sorted(conflicts)}

def synthetic_contract():
    sub="ACCESSION_NUMBER\tFILING_DATE\tPERIODOFREPORT\nA1\t01-JUL-2017\t30-JUN-2017\nA2\t01-NOV-2025\t30-SEP-2025\n"
    info="ACCESSION_NUMBER\tNAMEOFISSUER\tTITLEOFCLASS\tCUSIP\nA1\tOld Name Corp\tCommon Stock\t78409V104\nA2\tFuture Name Corp\tCommon Stock\t78409V104\n"
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as zf: zf.writestr("SUBMISSION.tsv",sub); zf.writestr("INFOTABLE.tsv",info)
    r=scan_archive(b.getvalue(),{"url":"synthetic://q104","label":"synthetic","period_start":"2017-07-01"},{"SPGI":{"78409V104"}})
    h=r["target_hits"]["SPGI"]
    return {"hash":len(r["archive_sha256"])==64,"matched":h["row_count"]==1,"future_excluded":"Future Name Corp" not in h["issuer_names"],"no_identity_conflict":not r["security_identity_conflicts"]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--shard",choices=sorted(SHARDS),required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    page=fetch(PAGE); all_archives=discover_archives(page); lo,hi=SHARDS[a.shard]; selected=[x for x in all_archives if lo<=date.fromisoformat(x["period_start"])<hi]; targets=frozen_cusips()
    receipt={"schema_version":"1.0","task_id":"Q-2026-10-06-104-I19-13F-HISTORICAL-ID-CENSUS-"+a.shard,"candidate_id":"Q104:I19",
      "status":"13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_SOURCE_ONLY","generated_at_utc":datetime.now(timezone.utc).isoformat(),"official_source":PAGE,
      "source_page_sha256":hashlib.sha256(page).hexdigest(),"data_boundary":{"start_inclusive":START.isoformat(),"end_exclusive":END.isoformat(),"filing_cutoff":CUTOFF.isoformat()},
      "shard":a.shard,"shard_boundary":{"start_inclusive":lo.isoformat(),"end_exclusive":hi.isoformat()},"discovered_archive_count_total":len(all_archives),
      "selected_archive_count":len(selected),"frozen_cusips":{s:sorted(cs) for s,cs in targets.items()},"archives":[],"synthetic":synthetic_contract(),
      "scientific_boundary":{"performance_authorized":False,"holdout_selection_allowed":False,"ranking_allowed":False,"parameter_search_allowed":False,"threshold_search_allowed":False,"horizon_search_allowed":False,"promotion_allowed":False,"live_execution_allowed":False},
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
      "next_gate":"historical security-identity closure + SEC acceptance-time join + concept-specific PIT compiler + independent reproduction"}
    for q in selected: receipt["archives"].append(scan_archive(fetch(q["url"]),q,targets))
    counts={s:0 for s in targets}; misses={s:[] for s in targets}; names={s:set() for s in targets}; conflicts=set()
    for q in receipt["archives"]:
        for s,h in q["target_hits"].items():
            if h["row_count"]: counts[s]+=1; names[s].update(h["issuer_names"])
            else: misses[s].append(q["archive"]["label"] or q["archive"]["url"])
        conflicts.update(q["security_identity_conflicts"])
    receipt["coverage_summary"]={s:{"archives_with_match":counts[s],"archives_without_match":len(selected)-counts[s],"historical_issuer_names_discovered":sorted(names[s]),"missed_archives":misses[s]} for s in targets}
    receipt["identity_conflicts"]=sorted(conflicts); receipt["archive_completeness_for_shard"]=len(selected)>0 and len(receipt["archives"])==len(selected)
    receipt["receipt_fingerprint"]=hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"shard":a.shard,"archive_count":len(selected),"coverage_summary":receipt["coverage_summary"],"fingerprint":receipt["receipt_fingerprint"]},ensure_ascii=False,sort_keys=True))
    return 0 if all(receipt["synthetic"].values()) and not receipt["identity_conflicts"] and receipt["archive_completeness_for_shard"] else 2

if __name__=="__main__": raise SystemExit(main())
