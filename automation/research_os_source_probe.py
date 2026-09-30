"""Low-impact rotating public endpoint probe. No dataset download, auth, PIT inference or performance."""
from __future__ import annotations
import argparse,json,time,urllib.error,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from automation.research_os_evidence_bus import ROOT,load_registry,source_index,build_receipt,write_receipt
def request(url:str,method:str="HEAD")->dict[str,Any]:
    req=urllib.request.Request(url,method=method,headers={"User-Agent":"trading-agent-research-os/0.1","Accept":"text/html,application/json;q=0.9,*/*;q=0.1"})
    start=time.perf_counter()
    try:
        with urllib.request.urlopen(req,timeout=12) as r:
            if method=="GET": r.read(1024)
            return {"network_reachable":True,"http_status":int(r.status),"http_success":200<=int(r.status)<400,"final_url":r.geturl(),"content_type":r.headers.get("Content-Type"),"elapsed_ms":round((time.perf_counter()-start)*1000,2)}
    except urllib.error.HTTPError as e:
        return {"network_reachable":True,"http_status":int(e.code),"http_success":False,"final_url":url,"content_type":e.headers.get("Content-Type") if e.headers else None,"elapsed_ms":round((time.perf_counter()-start)*1000,2),"error":f"HTTPError:{e.code}"}
    except (urllib.error.URLError,TimeoutError,ValueError) as e:
        return {"network_reachable":False,"http_status":None,"http_success":False,"final_url":url,"content_type":None,"elapsed_ms":round((time.perf_counter()-start)*1000,2),"error":type(e).__name__}
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--bucket",type=int,default=0); p.add_argument("--bucket-count",type=int,default=4); p.add_argument("--max-sources",type=int,default=4); p.add_argument("--output",type=Path,default=Path("research/runs/self_hosted/research_os/source_probe.json")); a=p.parse_args()
    if a.bucket_count<1 or a.max_sources<1: raise ValueError("bucket-count and max-sources must be positive")
    reg=load_registry(); sources=list(source_index(reg).values()); bucket=a.bucket%a.bucket_count; selected=[s for i,s in enumerate(sources) if i%a.bucket_count==bucket][:a.max_sources]
    now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"); results=[]
    for source in selected:
        result=request(source["source_url"])
        if result["http_status"] in {403,405,406} or (result["http_status"] is None and not result["network_reachable"]):
            fallback=request(source["source_url"],"GET"); result={"initial":result,"fallback_get":fallback,**result}
            if fallback.get("network_reachable"): result.update({k:fallback[k] for k in ("network_reachable","http_status","http_success","final_url","content_type")})
        raw={"source_id":source["id"],"observed_at":now,"probe":result}
        receipt=build_receipt(source_id=source["id"],raw_payload=raw,normalized_payload=result,retrieved_at=now,parser_version="research_os_source_probe/0.1",pit_status="DISCOVERY_ONLY",access_status="RESPONDED" if result.get("network_reachable") else "UNREACHABLE",receipt_type="source_capability_probe",registry=reg)
        results.append({"source_id":source["id"],"class":source.get("class"),"pit_fit":source.get("pit_fit"),"probe":result,"receipt":receipt})
    report={"schema_version":1,"research_os_version":reg["research_os_version"],"probe_type":"public_endpoint_reachability_only","observed_at":now,"bucket":bucket,"bucket_count":a.bucket_count,"sources":results,"scientific_evidence":False,"performance_authorization":False,"holdout_used":False,"paid_resources":False}
    path=a.output if a.output.is_absolute() else ROOT/a.output; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for x in results: write_receipt(x["receipt"],path.parent/"receipts"/f'{x["source_id"]}.json')
    print(json.dumps({"bucket":bucket,"sources":[x["source_id"] for x in results]},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
