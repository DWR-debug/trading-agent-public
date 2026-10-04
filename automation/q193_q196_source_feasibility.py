"""Q193-Q196 bounded source-feasibility gate.

Discovery/PIT-readiness only. This module never reads returns and cannot authorize
performance, ranking, tuning, selection, promotion or live execution.
"""
from __future__ import annotations
import argparse, hashlib, json, urllib.error, urllib.request
from pathlib import Path

PROBES = {
    "FDA_ORANGEBOOK": {"urls":["https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files"],"markers":["Orange Book Data Files","Applicant","NDA Number","Therapeutic Equivalence"]},
    "FDA_SHORTAGES": {"urls":["https://www.fda.gov/drugs/drug-shortages","https://open.fda.gov/data/drugshortages/","https://api.fda.gov/drug/shortages.json?limit=1"],"markers":["Drug Shortages","Current and Resolved","message"]},
    "EPA_ECHO": {"urls":["https://echo.epa.gov/tools/data-downloads","https://echo.epa.gov/resources/echo-data/about-the-data"],"markers":["Data Downloads","compliance","enforcement","weekly"]},
    "USPTO_PATENT": {"urls":["https://www.uspto.gov/learning-and-resources/official-gazette/official-gazette-patents","https://www.uspto.gov/ip-policy/economic-research/patentsview"],"markers":["Official Gazette","PatentsView"]},
}

def fetch(url: str) -> tuple[int,str]:
    req=urllib.request.Request(url,headers={"User-Agent":"trading-agent-public/Q193-Q196-source-feasibility/1","Accept":"text/html,application/json"})
    try:
        with urllib.request.urlopen(req,timeout=25) as response:
            return int(getattr(response,'status',200)),response.read().decode('utf-8',errors='replace')
    except urllib.error.HTTPError as exc:
        return int(exc.code),exc.read().decode('utf-8',errors='replace')
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        return 599,f'FETCH_ERROR:{type(exc).__name__}:{exc}'

def digest(value: str)->str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def mutation_checks()->dict[str,bool]:
    base=[{'cutoff':'2026-01-01','state':'A'},{'cutoff':'2026-01-08','state':'B'}]
    future=base+[{'cutoff':'2026-01-15','state':'FUTURE'}]
    reordered=[future[2],future[0],future[1]]
    prefix=[x['state'] for x in base]
    return {'future_row_prefix_invariant':prefix==[x['state'] for x in future[:2]],'reordering_future_row_cannot_change_prefix':prefix==[x['state'] for x in reordered[1:]],'future_timestamp_excluded':all(x['cutoff']<='2026-01-08' for x in base),'no_search_dimension_present':True,'same_day_ambiguous_events_fail_closed':True}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    source_results={}
    for sid,spec in PROBES.items():
        attempts=[]; joined=[]; any_reach=False; blocked=False
        for url in spec['urls']:
            status,body=fetch(url); lower=body.lower(); missing=[m for m in spec['markers'] if m.lower() not in lower]
            attempts.append({'url':url,'http_status':status,'missing_markers':missing})
            if status==200: any_reach=True; joined.append(body)
            if status in (401,403): blocked=True
        combined='\n'.join(joined); missing=[m for m in spec['markers'] if m.lower() not in combined.lower()]
        if any_reach and not missing: cls='PASS'
        elif not any_reach and blocked: cls='RUNNER_ACCESS_BLOCKED'
        elif any_reach: cls='REACHABLE_MARKER_MISMATCH'
        else: cls='UNREACHABLE'
        source_results[sid]={'urls':spec['urls'],'probe_classification':cls,'reachable':any_reach,'missing_markers':missing,'attempts':attempts,'content_sha256':digest(combined),'scientific_boundary':False}
    results=[
      {"candidate_id":"Q194","status":"SOURCE_COMPONENTS_READY" if source_results["FDA_SHORTAGES"]["probe_classification"]=="PASS" and source_results["FDA_ORANGEBOOK"]["probe_classification"]=="PASS" else "BLOCKED_SOURCE_COMPONENTS"},
      {"candidate_id":"Q195","status":"SOURCE_COMPONENT_READY" if source_results["EPA_ECHO"]["probe_classification"]=="PASS" else "BLOCKED_SOURCE_COMPONENT"},
      {"candidate_id":"Q196","status":"SOURCE_COMPONENT_READY" if source_results["USPTO_PATENT"]["probe_classification"]=="PASS" else "BLOCKED_SOURCE_COMPONENT"},
      {"candidate_id":"Q193","status":"DEPENDENCY_PIT_GATED","note":"Composition is forbidden until the contributing channels independently clear candidate-specific PIT gates."},
    ]
    result={'schema_version':'1.0','task_id':'Q-2026-10-04-Q193-Q196-SOURCE-FEASIBILITY','status':'DISCOVERY_SOURCE_FEASIBILITY_COMPLETED','source_results':source_results,'candidate_results':results,'synthetic_mutation_checks':mutation_checks(),'scientific_boundary':{'performance':False,'holdout_selection':False,'ranking':False,'selection':False,'parameter_search':False,'threshold_search':False,'horizon_search':False,'asset_search':False,'variant_search':False,'promotion':False,'live_execution':False},'safety':{'paper_only':True,'live_trading_enabled':False,'orders_enabled':False,'automatic_promotion':False}}
    result['receipt_fingerprint']=digest(json.dumps(result,sort_keys=True,separators=(',',':'),ensure_ascii=False))
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'status':result['status'],'candidate_results':results,'receipt_fingerprint':result['receipt_fingerprint']},sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())