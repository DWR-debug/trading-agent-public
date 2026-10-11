"""Q104:I19 historical SEC 13F identity/archive census; source/PIT only."""
from __future__ import annotations
import argparse,csv,hashlib,html.parser,io,json,re,threading,time,urllib.error,urllib.request,zipfile
import http.client
from concurrent.futures import ThreadPoolExecutor,as_completed
from automation.q111_security_identity_contract import normalize_text
from datetime import date,datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGE="https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets"
EVIDENCE=ROOT/"research/evidence/q113_13f_q107_coverage_result.json"
START=date(2013,7,1); END=date(2025,10,1); CUTOFF=date(2025,9,24)
SHARDS={
    "2013-2016":(date(2013,7,1),date(2017,1,1)),
    "2017-2018":(date(2017,1,1),date(2019,1,1)),
    "2019-2020":(date(2019,1,1),date(2021,1,1)),
    "2021-2022":(date(2021,1,1),date(2023,1,1)),
    "2023":(date(2023,1,1),date(2024,1,1)),
    "2024-2025-09":(date(2024,1,1),END),
}
UA="DWR-debug/trading-agent-public Q104-I19 historical 13F census/3.0"
# Six concurrent census shards each reserve at most ~1.5 SEC requests/sec.
# Aggregate nominal budget is <=9 requests/sec, below SEC's 10 requests/sec
# cap with headroom for other first-party research jobs.
ARCHIVE_REQUEST_GAP_SECONDS=0.67
HEADER_REQUEST_GAP_SECONDS=0.67
ARCHIVE_WORKERS=3
HEADER_WORKERS=4
MAX_FETCH_RETRIES=6
MAX_RETRY_DELAY_SECONDS=60

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

def fetch(url,retries=MAX_FETCH_RETRIES,rate_limiter=None):
    last=None
    for i in range(retries):
        if rate_limiter is not None:
            rate_limiter.wait()
        elif i == 0:
            time.sleep(ARCHIVE_REQUEST_GAP_SECONDS)
        try:
            req=urllib.request.Request(
                url,
                headers={
                    "User-Agent":UA,
                    "Accept":"application/zip,*/*",
                    "Accept-Encoding":"identity",
                    "Connection":"close",
                },
            )
            with urllib.request.urlopen(req,timeout=180) as r:return r.read()
        except urllib.error.HTTPError as e:
            last=e
            if e.code not in {408,425,429,500,502,503,504} or i+1>=retries:
                raise
            retry_after=None
            try:
                retry_after=int((getattr(e, "headers", None) or {}).get("Retry-After", "0"))
            except (AttributeError,TypeError,ValueError):
                retry_after=0
            delay=max(ARCHIVE_REQUEST_GAP_SECONDS, retry_after, min(MAX_RETRY_DELAY_SECONDS, 5*(2**i)))
            time.sleep(delay)
        except http.client.IncompleteRead as e:
            # urllib can raise IncompleteRead from response.read() when the
            # server closes a large SEC ZIP stream early. Discard the partial
            # bytes and retry the whole immutable URL through the same limiter.
            last=e
            if i+1>=retries: raise
            time.sleep(min(MAX_RETRY_DELAY_SECONDS, 5*(2**i)))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last=e
            if i+1>=retries: raise
            time.sleep(min(MAX_RETRY_DELAY_SECONDS, 5*(2**i)))
    raise last or RuntimeError("SEC_FETCH_FAILED")

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

class RateLimiter:
    def __init__(self,gap_seconds):
        self.gap_seconds=gap_seconds; self._lock=threading.Lock(); self._next=0.0
    def wait(self):
        with self._lock:
            now=time.monotonic(); delay=self._next-now
            if delay>0: time.sleep(delay)
            self._next=time.monotonic()+self.gap_seconds


def accession_header_url(cik,accession):
    cik10=str(cik).strip().zfill(10)
    normalized=str(accession).strip().replace("-","")
    acc=str(accession).strip()
    if not re.fullmatch(r"\d{10}-\d{2}-\d{6}",acc):
        raise ValueError("SEC_ACCESSION_UNPARSEABLE:"+acc)
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik10)}/{normalized}/{acc}-index-headers.html"


def parse_acceptance_header(text,expected_cik,expected_accession,expected_form,expected_filing_date):
    accepted=re.search(r"<ACCEPTANCE-DATETIME>\s*([0-9]{14})",text,re.I)
    accession_m=re.search(r"ACCESSION NUMBER:\s*([0-9]{10}-[0-9]{2}-[0-9]{6})",text,re.I)
    cik_m=re.search(r"CENTRAL INDEX KEY:\s*([0-9]{10})",text,re.I)
    form_m=re.search(r"CONFORMED SUBMISSION TYPE:\s*([^\s<]+)",text,re.I)
    filed_m=re.search(r"FILED AS OF DATE:\s*([0-9]{8})",text,re.I)
    if not accepted: raise ValueError("MISSING_ACCEPTANCE_DATETIME")
    if not accession_m or accession_m.group(1)!=expected_accession: raise ValueError("ACCESSION_MISMATCH")
    if not cik_m or cik_m.group(1)!=str(expected_cik).zfill(10): raise ValueError("FILER_CIK_MISMATCH")
    if not form_m or form_m.group(1).upper()!=expected_form.upper(): raise ValueError("FORM_MISMATCH")
    if filed_m:
        filed=f"{filed_m.group(1)[:4]}-{filed_m.group(1)[4:6]}-{filed_m.group(1)[6:8]}"
        if filed!=expected_filing_date: raise ValueError("FILING_DATE_MISMATCH")
    raw=accepted.group(1)
    return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}T{raw[8:10]}:{raw[10:12]}:{raw[12:14]}"



def enrich_acceptance_times(accession_meta, rate_limiter=None):
    """Resolve SEC acceptance timestamps once per unique target accession.

    This is intentionally separated from archive scanning so slow SEC header
    requests cannot block the historical archive download pipeline.
    """
    limiter=rate_limiter or RateLimiter(HEADER_REQUEST_GAP_SECONDS)
    records={}; failures={}

    def one(item):
        accession,meta=item
        cik=meta.get("filer_cik","")
        if not cik:
            raise RuntimeError("MISSING_FILER_CIK:"+accession)
        url=accession_header_url(cik,accession)
        limiter.wait()
        req=urllib.request.Request(
            url,
            headers={
                "User-Agent":UA,
                "Accept":"text/html,text/plain,*/*",
                "Accept-Encoding":"identity",
                "Connection":"close",
            },
        )
        try:
            with urllib.request.urlopen(req,timeout=45) as resp:
                body=resp.read()
                status=int(getattr(resp,"status",200))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"SEC_HEADER_HTTP_{exc.code}") from exc
        if status!=200:
            raise RuntimeError(f"SEC_HEADER_HTTP_{status}")
        value=parse_acceptance_header(
            body.decode("utf-8","replace"),
            cik,
            accession,
            meta.get("submission_type",""),
            meta["filing_date"],
        )
        return accession,{
            "accession":accession,
            "filer_cik":str(cik).zfill(10),
            "filing_date":meta["filing_date"],
            "period":meta.get("period"),
            "submission_type":meta.get("submission_type"),
            "acceptance_datetime":value,
            "acceptance_timezone":"America/New_York",
            "acceptance_clock_basis":"SEC_EDGAR_SGML_ACCEPTANCE_DATETIME",
            "source_url":url,
            "header_sha256":hashlib.sha256(body).hexdigest(),
            "header_bytes":len(body),
        }

    with ThreadPoolExecutor(max_workers=HEADER_WORKERS) as ex:
        futures={ex.submit(one,item):item[0] for item in accession_meta.items()}
        for future in as_completed(futures):
            accession=futures[future]
            try:
                k,v=future.result()
                records[k]=v
            except Exception as exc:
                failures[accession]=str(exc)
    return records,failures


def scan_archive(blob,archive,targets,**_ignored):
    """Scan one quarterly archive for frozen security identities only.

    Acceptance-time enrichment is deliberately deferred until all archives in
    the shard have been scanned, preventing header latency from serializing the
    archive download/scan pipeline.
    """
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        eligible={}
        for row in tsv(zf,"submission.tsv"):
            acc=field(row,"ACCESSION_NUMBER")
            raw=field(row,"FILING_DATE")
            if not acc or not raw:
                continue
            try:
                d=parse_date(raw)
            except ValueError:
                continue
            if d<=CUTOFF:
                eligible[acc]={
                    "filing_date":d.isoformat(),
                    "period":field(row,"PERIODOFREPORT"),
                    "filer_cik":field(row,"CIK"),
                    "submission_type":field(row,"SUBMISSIONTYPE"),
                }

        wanted={c:s for s,cs in targets.items() for c in cs}
        hits={
            s:{
                "row_count":0,
                "cusips":set(),
                "issuer_names":set(),
                "class_names":set(),
                "accessions":set(),
                "filing_dates":set(),
                "periods":set(),
                "_issuer_name_observations_by_cusip":{},
            }
            for s in targets
        }
        conflicts=set()

        for row in tsv(zf,"infotable.tsv"):
            acc=field(row,"ACCESSION_NUMBER")
            if acc not in eligible:
                continue
            c=norm_cusip(field(row,"CUSIP"))
            sym=wanted.get(c)
            if sym is None:
                continue
            if sum(c in cs for cs in targets.values())>1:
                conflicts.add(c)
            h=hits[sym]
            h["row_count"]+=1
            h["cusips"].add(c)
            raw_issuer_name=field(row,"NAMEOFISSUER").strip()
            h["issuer_names"].add(raw_issuer_name)
            normalized_issuer_name=normalize_text(raw_issuer_name)
            variants=h["_issuer_name_observations_by_cusip"].setdefault(c,{})
            observation=variants.setdefault(normalized_issuer_name,{"row_count":0,"raw_examples":set(),"accessions":set(),"filing_dates":set()})
            observation["row_count"]+=1
            observation["raw_examples"].add(raw_issuer_name)
            observation["accessions"].add(acc)
            observation["filing_dates"].add(eligible[acc]["filing_date"])
            h["class_names"].add(field(row,"TITLEOFCLASS"))
            h["accessions"].add(acc)
            h["filing_dates"].add(eligible[acc]["filing_date"])
            h["periods"].add(eligible[acc]["period"])

    for h in hits.values():
        for k in ("cusips","issuer_names","class_names","accessions","filing_dates","periods"):
            h[k]=sorted(x for x in h[k] if x)

    issuer_name_cusip_audit={}
    unresolved_issuer_name_cusips=[]
    for symbol,h in hits.items():
        by_cusip={}
        raw_by_cusip=h.pop("_issuer_name_observations_by_cusip",{})
        for cusip,by_name in sorted(raw_by_cusip.items()):
            observations=[]
            for normalized_name,details in sorted(by_name.items()):
                accession_order=sorted(details["accessions"],key=lambda acc:(eligible.get(acc,{}).get("filing_date",""),acc))
                filing_dates=sorted(details["filing_dates"])
                observations.append({
                    "normalized_name":normalized_name or None,
                    "row_count":int(details["row_count"]),
                    "distinct_accession_count":len(details["accessions"]),
                    "accession_samples":accession_order[:5],
                    "filing_date_min":filing_dates[0] if filing_dates else None,
                    "filing_date_max":filing_dates[-1] if filing_dates else None,
                    "raw_variant_count":len(details["raw_examples"]),
                    "raw_examples":sorted(x for x in details["raw_examples"] if x)[:5],
                })
            normalized_names=sorted({x for x in by_name if x})
            missing_name_rows=int(by_name.get("",{}).get("row_count",0))
            if missing_name_rows:
                name_status="UNRESOLVED_MISSING_ISSUER_NAME"
            elif len(normalized_names)>1:
                name_status="UNRESOLVED_ISSUER_NAME_VARIANTS"
            else:
                name_status="SINGLE_NORMALIZED_NAME_OBSERVED_NOT_IDENTITY_PROOF"
            by_cusip[cusip]={
                "status":name_status,
                "identity_resolution_proven":False,
                "normalized_name_count":len(normalized_names),
                "missing_name_rows":missing_name_rows,
                "observed_row_count":sum(int(x["row_count"]) for x in observations),
                "observations":observations,
            }
            if name_status.startswith("UNRESOLVED_"):
                unresolved_issuer_name_cusips.append({
                    "symbol":symbol,"cusip":cusip,"status":name_status,
                    "normalized_name_count":len(normalized_names),
                    "missing_name_rows":missing_name_rows,
                    "observed_row_count":sum(int(x["row_count"]) for x in observations),
                })
        issuer_name_cusip_audit[symbol]=by_cusip

    target_accession_meta={
        accession:eligible[accession]
        for h in hits.values()
        for accession in h["accessions"]
        if accession in eligible
    }
    missing_meta={
        accession
        for h in hits.values()
        for accession in h["accessions"]
        if accession not in target_accession_meta
    }
    if missing_meta:
        raise RuntimeError(
            "Q104_I19_TARGET_ACCESSION_METADATA_MISSING:"
            + ",".join(sorted(missing_meta))
        )

    return {
        "archive":archive,
        "archive_sha256":hashlib.sha256(blob).hexdigest(),
        "archive_bytes":len(blob),
        "target_hits":hits,
        "issuer_name_cusip_audit":issuer_name_cusip_audit,
        "unresolved_issuer_name_cusips":sorted(unresolved_issuer_name_cusips,key=lambda x:(x["symbol"],x["cusip"])),
        "identity_resolution_proven":False,
        "target_accession_meta":target_accession_meta,
        "security_identity_conflicts":sorted(conflicts),
        "acceptance_failures":{},
        "acceptance_record_count":0,
        "target_unique_accession_count":len(target_accession_meta),
    }


def load_page(page_file=None):
    return Path(page_file).read_bytes() if page_file else fetch(PAGE)


def synthetic_contract():
    sub="ACCESSION_NUMBER\tFILING_DATE\tPERIODOFREPORT\nA1\t01-JUL-2017\t30-JUN-2017\nA2\t01-NOV-2025\t30-SEP-2025\n"
    info="ACCESSION_NUMBER\tNAMEOFISSUER\tTITLEOFCLASS\tCUSIP\nA1\tOld Name Corp\tCommon Stock\t78409V104\nA2\tFuture Name Corp\tCommon Stock\t78409V104\n"
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as zf: zf.writestr("SUBMISSION.tsv",sub); zf.writestr("INFOTABLE.tsv",info)
    r=scan_archive(b.getvalue(),{"url":"synthetic://q104","label":"synthetic","period_start":"2017-07-01"},{"SPGI":{"78409V104"}})
    h=r["target_hits"]["SPGI"]
    return {"hash":len(r["archive_sha256"])==64,"matched":h["row_count"]==1,"future_excluded":"Future Name Corp" not in h["issuer_names"],"no_identity_conflict":not r["security_identity_conflicts"]}

def aggregate_issuer_name_cusip_audit(archive_records,symbols):
    """Aggregate normalized NAMEOFISSUER observations under frozen CUSIP keys.

    Variants are diagnostics only: they never rewrite the frozen CUSIP universe
    or remove rows. Even one observed normalized name is not identity proof.
    """
    combined={symbol:{} for symbol in symbols}
    for record in archive_records:
        archive=record.get("archive") or {}
        label=str(archive.get("label") or archive.get("url") or "UNKNOWN_ARCHIVE")
        for symbol,by_cusip in (record.get("issuer_name_cusip_audit") or {}).items():
            if symbol not in combined:
                combined[symbol]={}
            for cusip,audit in by_cusip.items():
                item=combined[symbol].setdefault(cusip,{"archive_labels":set(),"observations":{}})
                item["archive_labels"].add(label)
                for observation in audit.get("observations",[]):
                    name=observation.get("normalized_name") or ""
                    target=item["observations"].setdefault(name,{
                        "row_count":0,"distinct_accession_count":0,"raw_examples":set(),
                        "accession_samples":set(),"filing_date_min":None,"filing_date_max":None,
                        "archive_labels":set(),
                    })
                    target["row_count"]+=int(observation.get("row_count",0) or 0)
                    target["distinct_accession_count"]+=int(observation.get("distinct_accession_count",0) or 0)
                    target["raw_examples"].update(observation.get("raw_examples",[]))
                    target["accession_samples"].update(observation.get("accession_samples",[]))
                    target["archive_labels"].add(label)
                    first=observation.get("filing_date_min")
                    last=observation.get("filing_date_max")
                    if first and (target["filing_date_min"] is None or first<target["filing_date_min"]): target["filing_date_min"]=first
                    if last and (target["filing_date_max"] is None or last>target["filing_date_max"]): target["filing_date_max"]=last
    result={symbol:{} for symbol in symbols}
    for symbol,by_cusip in sorted(combined.items()):
        for cusip,item in sorted(by_cusip.items()):
            observations=[]
            for normalized_name,details in sorted(item["observations"].items()):
                observations.append({
                    "normalized_name":normalized_name or None,
                    "row_count":details["row_count"],
                    "distinct_accession_count":details["distinct_accession_count"],
                    "filing_date_min":details["filing_date_min"],
                    "filing_date_max":details["filing_date_max"],
                    "archive_labels":sorted(details["archive_labels"]),
                    "raw_examples":sorted(x for x in details["raw_examples"] if x)[:5],
                    "accession_samples":sorted(details["accession_samples"])[:8],
                })
            normalized_names=[x for x in item["observations"] if x]
            missing_name_rows=int(item["observations"].get("",{}).get("row_count",0))
            if missing_name_rows:
                status="UNRESOLVED_MISSING_ISSUER_NAME"
            elif len(normalized_names)>1:
                status="UNRESOLVED_ISSUER_NAME_VARIANTS"
            else:
                status="SINGLE_NORMALIZED_NAME_OBSERVED_NOT_IDENTITY_PROOF"
            result[symbol][cusip]={
                "status":status,
                "identity_resolution_proven":False,
                "normalized_name_count":len(normalized_names),
                "missing_name_rows":missing_name_rows,
                "observed_row_count":sum(int(x["row_count"]) for x in observations),
                "archive_labels":sorted(item["archive_labels"]),
                "observations":observations,
            }
    return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--shard",choices=sorted(SHARDS),required=True); ap.add_argument("--output",type=Path,required=True); ap.add_argument("--page-file",type=Path); a=ap.parse_args()
    page=load_page(a.page_file); all_archives=discover_archives(page); lo,hi=SHARDS[a.shard]; selected=[x for x in all_archives if lo<=date.fromisoformat(x["period_start"])<hi]; targets=frozen_cusips()
    receipt={"schema_version":"1.0","task_id":"Q-2026-10-06-104-I19-13F-HISTORICAL-ID-CENSUS-"+a.shard,"candidate_id":"Q104:I19",
      "status":"13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_SOURCE_ONLY","generated_at_utc":datetime.now(timezone.utc).isoformat(),"official_source":PAGE,
      "source_page_sha256":hashlib.sha256(page).hexdigest(),"data_boundary":{"start_inclusive":START.isoformat(),"end_exclusive":END.isoformat(),"filing_cutoff":CUTOFF.isoformat()},
      "shard":a.shard,"shard_boundary":{"start_inclusive":lo.isoformat(),"end_exclusive":hi.isoformat()},"discovered_archive_count_total":len(all_archives),
      "selected_archive_count":len(selected),"frozen_cusips":{s:sorted(cs) for s,cs in targets.items()},"archives":[],"synthetic":synthetic_contract(),
      "scientific_boundary":{"performance_authorized":False,"holdout_selection_allowed":False,"ranking_allowed":False,"parameter_search_allowed":False,"threshold_search_allowed":False,"horizon_search_allowed":False,"promotion_allowed":False,"live_execution_allowed":False},
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
      "next_gate":"historical security-identity closure + SEC acceptance-time join + concept-specific PIT compiler + independent reproduction"}
    # One limiter covers archive downloads AND header lookups within this shard.
    # The two phases can never reset the gap and create a request burst at handoff.
    request_limiter=RateLimiter(max(ARCHIVE_REQUEST_GAP_SECONDS,HEADER_REQUEST_GAP_SECONDS))
    shard_order=list(SHARDS).index(a.shard)
    time.sleep(shard_order * 0.10)
    scanned={}
    completed_archives=0

    def scan_one(q):
        blob=fetch(q["url"],rate_limiter=request_limiter)
        return q["url"],scan_archive(blob,q,targets)
    with ThreadPoolExecutor(max_workers=ARCHIVE_WORKERS) as ex:
        futures=[ex.submit(scan_one,q) for q in selected]
        for future in as_completed(futures):
            url,record=future.result()
            scanned[url]=record
            completed_archives += 1
            print(json.dumps({
                "phase":"archive_scan",
                "shard":a.shard,
                "completed":completed_archives,
                "total":len(selected),
                "archive_url":url,
            },sort_keys=True),flush=True)

    # Acceptance-time enrichment is a second bounded phase across all unique
    # target accessions. It can no longer stall the archive scanner.
    all_accession_meta={}
    accession_owner={}
    for q in selected:
        record=scanned[q["url"]]
        for accession,meta in record["target_accession_meta"].items():
            if accession in all_accession_meta:
                raise RuntimeError("Q104_I19_DUPLICATE_TARGET_ACCESSION_ACROSS_ARCHIVES:"+accession)
            all_accession_meta[accession]=meta
            accession_owner[accession]=q["url"]

    acceptance_records,acceptance_failures=enrich_acceptance_times(
        all_accession_meta,
        rate_limiter=request_limiter,
    )
    print(json.dumps({
        "phase":"acceptance_time_join",
        "shard":a.shard,
        "target_unique_accessions":len(all_accession_meta),
        "acceptance_records":len(acceptance_records),
        "acceptance_failures":len(acceptance_failures),
    },sort_keys=True),flush=True)

    for q in selected:
        record=scanned[q["url"]]
        record.pop("target_accession_meta",None)
        archive_accessions=sorted({
            accession
            for h in record["target_hits"].values()
            for accession in h["accessions"]
        })
        archive_failures={
            accession:acceptance_failures[accession]
            for accession in archive_accessions
            if accession in acceptance_failures
        }
        archive_records={
            accession:acceptance_records[accession]
            for accession in archive_accessions
            if accession in acceptance_records
        }
        for h in record["target_hits"].values():
            h["acceptance_records"]={
                accession:archive_records[accession]
                for accession in h["accessions"]
                if accession in archive_records
            }
            h["acceptance_complete"]=(
                len(h["acceptance_records"])==len(h["accessions"])
                and not any(accession in archive_failures for accession in h["accessions"])
            )
        record["acceptance_failures"]=archive_failures
        record["acceptance_record_count"]=len(archive_records)
        record["target_unique_accession_count"]=len(archive_accessions)

    # Keep receipt order deterministic; any worker exception aborts the shard fail-closed.
    for q in selected:
        receipt["archives"].append(scanned[q["url"]])
    counts={s:0 for s in targets}; misses={s:[] for s in targets}; names={s:set() for s in targets}; conflicts=set()
    for q in receipt["archives"]:
        for s,h in q["target_hits"].items():
            if h["row_count"]: counts[s]+=1; names[s].update(h["issuer_names"])
            else: misses[s].append(q["archive"]["label"] or q["archive"]["url"])
        conflicts.update(q["security_identity_conflicts"])
    receipt["coverage_summary"]={s:{"archives_with_match":counts[s],"archives_without_match":len(selected)-counts[s],"historical_issuer_names_discovered":sorted(names[s]),"missed_archives":misses[s]} for s in targets}
    receipt["issuer_name_cusip_audit"]=aggregate_issuer_name_cusip_audit(receipt["archives"],targets)
    receipt["unresolved_issuer_name_cusips"]=[
        {"symbol":symbol,"cusip":cusip,"status":audit["status"],"normalized_name_count":audit["normalized_name_count"],"missing_name_rows":audit["missing_name_rows"],"observed_row_count":audit["observed_row_count"],"archive_labels":audit["archive_labels"],"normalized_names":[x["normalized_name"] for x in audit["observations"] if x["normalized_name"] is not None]}
        for symbol,by_cusip in receipt["issuer_name_cusip_audit"].items()
        for cusip,audit in by_cusip.items() if audit["status"].startswith("UNRESOLVED_")
    ]
    for symbol in targets:
        unresolved=[x["cusip"] for x in receipt["unresolved_issuer_name_cusips"] if x["symbol"]==symbol]
        receipt["coverage_summary"][symbol]["issuer_name_cusips_with_unresolved_variants"]=sorted(unresolved)
        receipt["coverage_summary"][symbol]["issuer_name_identity_status"]=(
            "UNRESOLVED_CUSIP_ISSUER_NAME_VARIANTS_PRESENT" if unresolved else "NO_VARIANT_OBSERVED_NOT_IDENTITY_PROOF"
        )
        receipt["coverage_summary"][symbol]["identity_resolution_proven"]=False
    receipt["identity_review"]={
        "status":"UNRESOLVED_CUSIP_ISSUER_NAME_VARIANTS_PRESENT" if receipt["unresolved_issuer_name_cusips"] else "NO_VARIANT_OBSERVED_NOT_PROOF",
        "unresolved_pair_count":len(receipt["unresolved_issuer_name_cusips"]),
        "identity_resolution_proven":False,
        "interpretation":"Issuer labels are descriptive fields. Variants under one frozen CUSIP are retained for review and do not rewrite the frozen universe or drop rows; a single observed normalized name is not proof of correct identity.",
    }
    receipt["identity_conflicts"]=sorted(conflicts)
    receipt["acceptance_failures"]={}
    for q in receipt["archives"]:
        for acc,err in q.get("acceptance_failures",{}).items(): receipt["acceptance_failures"][acc]=err
    acceptance_checked=sum(q.get("acceptance_record_count",0) for q in receipt["archives"])
    acceptance_targets=sum(q.get("target_unique_accession_count",0) for q in receipt["archives"])
    receipt["acceptance_time_join"]={"records_checked":acceptance_checked,"target_unique_accessions":acceptance_targets,"failures":len(receipt["acceptance_failures"]),"complete":acceptance_targets==acceptance_checked and not receipt["acceptance_failures"],"timezone_inference":False}
    receipt["archive_completeness_for_shard"]=len(selected)>0 and len(receipt["archives"])==len(selected)
    receipt["receipt_fingerprint"]=hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"shard":a.shard,"archive_count":len(selected),"coverage_summary":receipt["coverage_summary"],"identity_review":receipt["identity_review"],"unresolved_issuer_name_cusips":receipt["unresolved_issuer_name_cusips"],"fingerprint":receipt["receipt_fingerprint"]},ensure_ascii=False,sort_keys=True))
    return 0 if all(receipt["synthetic"].values()) and not receipt["identity_conflicts"] and receipt["archive_completeness_for_shard"] and receipt["acceptance_time_join"]["complete"] else 2

if __name__=="__main__": raise SystemExit(main())
