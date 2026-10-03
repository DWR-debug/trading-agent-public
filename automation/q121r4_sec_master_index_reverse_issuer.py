"""Q121-R4 official SEC quarterly master-index reverse-issuer feasibility."""
from __future__ import annotations
import argparse,gzip,hashlib,io,json,re,time,urllib.error,urllib.request,zipfile
from datetime import date
from pathlib import Path
from automation import q121r1_sec_reverse_issuer_coverage as r1

START="2024-02-05"
END="2025-09-24"
FORM_SET={"SC 13D","SC 13G","SC 13D/A","SC 13G/A"}
REQUEST_GAP_SECONDS=0.35
UA="trading-agent-public/Q121R4-sec-master-index/1"
TRANSPORTS=("master.zip","master.gz","master.idx")


def index_url(year:int,quarter:int)->str:
    return f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/master.idx"
CIKS={"SPGI":"0000064040","NDAQ":"0001120193","AMP":"0000820027","RJF":"0000720005","WMB":"0000107263","VLO":"0001035002","DVN":"0001090012","EMN":"0000915389"}
QUARTERS=((2024,1),(2024,2),(2024,3),(2024,4),(2025,1),(2025,2),(2025,3))
CONTROLS=(("0001104659-24-021877","0000064040",None),("0001193125-24-189043","0001120193",None),("0001193125-24-258276","0001239819","0000820027"))

def sha256_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def decode_sec_submission_body(body:bytes)->bytes:
    """Decode a SEC archive payload when HTTP delivered gzip content."""
    if body.startswith(b"\x1f\x8b"):
        try:
            return gzip.decompress(body)
        except OSError as exc:
            raise RuntimeError("SEC_SUBMISSION_GZIP_DECODE_FAILED") from exc
    return body


def extract_control_cik(text:str,section:str)->str|None:
    """Extract the first CIK from the requested SEC-HEADER section."""
    compact=r1.plain_text(text)
    if section=="Subject":
        section_pattern=r"SUBJECT COMPANY\s*:?(.*?)(?=FILED BY\s*:|$)"
    elif section=="Filed by":
        section_pattern=r"FILED BY\s*:?(.*)$"
    else:
        raise ValueError(f"UNKNOWN_HEADER_SECTION:{section}")
    section_match=re.search(section_pattern,compact,re.IGNORECASE|re.DOTALL)
    if not section_match:
        return None
    cik_match=re.search(r"CENTRAL\s+INDEX\s+KEY\s*:?\s*(\d{1,10})",section_match.group(1),re.IGNORECASE)
    return cik_match.group(1).zfill(10) if cik_match else None


def fetch(url:str)->tuple[int,bytes]:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/plain,application/zip,application/gzip,*/*","Accept-Encoding":"gzip, deflate","Host":"www.sec.gov"})
    last_status=None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=60) as response:
                return int(getattr(response,"status",200)),response.read()
        except urllib.error.HTTPError as exc:
            last_status=int(exc.code)
            if last_status not in {429,500,502,503,504} or attempt == 2:
                return last_status,exc.read()
        except (urllib.error.URLError,TimeoutError,OSError) as exc:
            if attempt == 2:
                raise RuntimeError(f"SEC_TRANSPORT_ERROR:{url}:{exc}") from exc
        time.sleep(2 ** attempt)
    raise RuntimeError(f"SEC_TRANSPORT_RETRY_EXHAUSTED:{url}:status={last_status}")

def fetch_master(year:int,quarter:int)->tuple[bytes,dict[str,object]]:
    attempts=[]
    for transport in TRANSPORTS:
        url=f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/{transport}"
        time.sleep(REQUEST_GAP_SECONDS)
        status,body=fetch(url)
        attempts.append({"transport":transport,"url":url,"status":status})
        if status!=200:
            continue
        if transport=="master.zip":
            try:
                with zipfile.ZipFile(io.BytesIO(body)) as z:
                    names=[n for n in z.namelist() if n.lower().endswith("/master.idx") or n.lower()=="master.idx"]
                    if len(names)!=1:
                        raise RuntimeError(f"SEC_MASTER_ZIP_UNEXPECTED_MEMBERS:{names}")
                    logical=z.read(names[0])
            except (zipfile.BadZipFile,OSError,KeyError) as exc:
                raise RuntimeError(f"SEC_MASTER_ZIP_INVALID:{year}:QTR{quarter}:{exc}") from exc
        elif transport=="master.gz":
            try: logical=gzip.decompress(body)
            except OSError as exc: raise RuntimeError(f"SEC_MASTER_GZIP_INVALID:{year}:QTR{quarter}:{exc}") from exc
        else:
            logical=body
        return logical,{"transport":transport,"transport_url":url,"transport_sha256":sha256_bytes(body),"logical_sha256":sha256_bytes(logical),"raw_bytes":len(body),"logical_bytes":len(logical),"attempts":attempts}
    raise RuntimeError("SEC_MASTER_INDEX_ALL_TRANSPORTS_BLOCKED:"+json.dumps(attempts,sort_keys=True,separators=(",",":")))

def parse_master(body:bytes)->list[dict[str,str]]:
    rows=[]
    for raw in body.decode("latin-1").splitlines():
        line=raw.strip()
        if not line or "|" not in line: continue
        parts=line.split("|",4)
        if len(parts)!=5: continue
        cik,company,form,filing_date,filename=parts
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",filing_date): continue
        if not re.fullmatch(r"\d{1,10}",cik.strip()): continue
        if not filename.startswith("edgar/data/"): continue
        rows.append({"cik":cik.strip().zfill(10),"company_name":company.strip(),"form":form.strip().upper(),"filed_date":filing_date,"filename":filename.strip()})
    return rows

def accession_from_filename(filename:str)->str:
    m=re.search(r"(\d{10}-\d{2}-\d{6})(?:[-.]|$)",filename)
    if m: return m.group(1)
    m=re.search(r"/(\d{18})/",filename)
    if m:
        raw=m.group(1); return f"{raw[:10]}-{raw[10:12]}-{raw[12:]}"
    raise ValueError(f"ACCESSION_NOT_FOUND_IN_FILENAME:{filename}")

def filing_index_url(filename:str)->str:
    parts=filename.split("/")
    if len(parts)<4: raise ValueError(f"INVALID_FILENAME:{filename}")
    cik=str(int(parts[2])); acc=accession_from_filename(filename).replace("-","")
    accession=accession_from_filename(filename)
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{accession}-index.htm"

def header_url(filename:str)->str:
    return filing_index_url(filename).replace("-index.htm","-index-headers.html")

def within_window(v:str)->bool:
    d=date.fromisoformat(v); return date.fromisoformat(START)<=d<=date.fromisoformat(END)

def run(output:Path)->dict[str,object]:
    receipts=[]; rows=[]
    for year,quarter in QUARTERS:
        body,transport=fetch_master(year,quarter)
        parsed=[x for x in parse_master(body) if x["form"] in FORM_SET and within_window(x["filed_date"])]
        receipts.append({"year":year,"quarter":quarter,"source_family":f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/",**transport,"matching_rows":len(parsed)})
        rows.extend(parsed)
    by_accession={}
    duplicate_accession_rows=0
    for row in rows:
        acc=accession_from_filename(row["filename"])
        by_accession.setdefault(acc, []).append(row)
        if len(by_accession[acc]) > 1:
            duplicate_accession_rows += 1
    controls=[]
    for accession,expected_subject,expected_filer in CONTROLS:
        matches=by_accession.get(accession,[])
        if not matches:
            raise RuntimeError(f"Q121R4_CONTROL_NOT_RECOVERED:{accession}")

        matched_check=None
        for row in matches:
            url=header_url(row["filename"]); time.sleep(REQUEST_GAP_SECONDS); status,body=fetch(url)
            candidates=[]
            if status==200:
                candidates.append((url,body,status))
            source_text_url="https://www.sec.gov/Archives/"+row["filename"]
            time.sleep(REQUEST_GAP_SECONDS)
            source_status,source_body=fetch(source_text_url)
            if source_status==200:
                candidates.append((source_text_url,source_body,source_status))

            for identity_url,identity_body,identity_status in candidates:
                header_text=decode_sec_submission_body(identity_body).decode("utf-8",errors="replace")
                subject=extract_control_cik(header_text,"Subject") or r1.extract_header_section_cik(header_text,"Subject") or r1.extract_labeled_cik(header_text,"Subject")
                filer=extract_control_cik(header_text,"Filed by") or r1.extract_header_section_cik(header_text,"Filed by") or r1.extract_labeled_cik(header_text,"Filed by")
                accepted=r1.extract_accepted(header_text)
                if subject==expected_subject and (expected_filer is None or filer==expected_filer) and accepted is not None:
                    matched_check={"accession_number":accession,"index_cik":row["cik"],"form":row["form"],"filing_date":row["filed_date"],"filename":row["filename"],"header_url":url,"identity_source_url":identity_url,"header_http_status":status,"identity_http_status":identity_status,"header_sha256":sha256_bytes(identity_body),"subject_cik":subject,"filed_by_cik":filer,"accepted_datetime":accepted,"expected_subject_cik":expected_subject,"expected_filer_cik":expected_filer}
                    break
            if matched_check is not None:
                break

        if matched_check is None:
            raise RuntimeError(f"Q121R4_CONTROL_IDENTITY_NOT_RECOVERED:{accession}:expected_subject={expected_subject}:expected_filer={expected_filer}")
        controls.append(matched_check)
    result={"schema_version":"1.0","task_id":"Q-2026-10-03-121R4-SEC-MASTER-INDEX-REVERSE-ISSUER-FEASIBILITY","status":"Q121R4_MASTER_INDEX_ROUTE_FEASIBILITY_COMPLETED","window":{"start":START,"end":END},"forms":sorted(FORM_SET),"frozen_issuer_cik_map":CIKS,"quarters_checked":len(receipts),"quarter_receipts":receipts,"filtered_form_rows":len(rows),"unique_accessions":len(by_accession),"accession_row_count":sum(len(v) for v in by_accession.values()),"duplicate_accession_rows":duplicate_accession_rows,"frozen_controls_checked":len(controls),"controls":controls,"interpretation":{"quarterly_master_index_coverage_for_fixed_window":True,"frozen_controls_recovered":True,"subject_header_recovery_verified":True,"full_subject_issuer_population_compiled":False,"same_day_pit_safe":False,"revision_lineage_established":False},"governance":{"performance":False,"holdout":False,"selection":False,"ranking":False,"parameter_search":False,"threshold_search":False,"horizon_search":False,"asset_search":False,"variant_search":False,"performance_authorized":False,"automatic_promotion":False},"safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}}
    result["receipt_fingerprint"]=hashlib.sha256(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); result=run(a.output)
    print(json.dumps({"status":result["status"],"quarters_checked":result["quarters_checked"],"filtered_form_rows":result["filtered_form_rows"],"controls":result["frozen_controls_checked"],"receipt_fingerprint":result["receipt_fingerprint"]},sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
