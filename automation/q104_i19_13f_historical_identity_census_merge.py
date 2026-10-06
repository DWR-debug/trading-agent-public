"""Deterministic merge for Q104:I19 historical 13F census shards."""
from __future__ import annotations
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
EXPECTED={"2013-2017","2018-2021","2022-2025-09"}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--input-dir",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
    payloads=[json.loads(p.read_text(encoding="utf-8")) for p in a.input_dir.rglob("shard_receipt.json")]
    shards={p["shard"] for p in payloads}
    if shards!=EXPECTED:raise SystemExit("Q104_I19_MISSING_OR_DUPLICATE_SHARDS")
    urls=[];hashes={};frozen=None;archives=[];conf=set()
    for p in payloads:
        hashes[p["source_page_sha256"]]=1
        if frozen is None:frozen=p["frozen_cusips"]
        elif frozen!=p["frozen_cusips"]:raise SystemExit("Q104_I19_FROZEN_CUSIP_MISMATCH")
        for x in p["archives"]:
            u=x["archive"]["url"]
            if u in urls:raise SystemExit("Q104_I19_DUPLICATE_ARCHIVE")
            urls.append(u);archives.append(x);conf.update(x.get("security_identity_conflicts",[]))
    if len(hashes)!=1:raise SystemExit("Q104_I19_SOURCE_PAGE_HASH_MISMATCH")
    archives.sort(key=lambda x:(x["archive"]["period_start"],x["archive"]["url"]))
    summary={}
    for s in sorted(frozen):
        hits=sum(1 for x in archives if x["target_hits"].get(s,{}).get("row_count",0)>0)
        summary[s]={"archives_with_match":hits,"archives_without_match":len(archives)-hits}
    receipt={"schema_version":"1.0","task_id":"Q-2026-10-06-104-I19-13F-HISTORICAL-ID-CENSUS","candidate_id":"Q104:I19",
      "status":"13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_COMPLETED_SOURCE_ONLY","generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "official_source":"https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets","source_page_sha256":next(iter(hashes)),
      "completed_shards":sorted(shards),"archive_count":len(archives),"frozen_cusips":frozen,"archives":archives,"coverage_summary":summary,
      "identity_conflicts":sorted(conf),"scientific_boundary":{"performance_authorized":False,"holdout_selection_allowed":False,"ranking_allowed":False,"parameter_search_allowed":False,"threshold_search_allowed":False,"horizon_search_allowed":False,"promotion_allowed":False,"live_execution_allowed":False},
      "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
      "next_gate":"historical security-identity closure + SEC acceptance-time join + concept-specific PIT compiler + independent reproduction"}
    receipt["receipt_fingerprint"]=hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"
",encoding="utf-8")
if __name__=="__main__":raise SystemExit(main())
