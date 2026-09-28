"""Freeze all Q076 performance input dependencies before authorization."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta
from pathlib import Path

def fp(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

def fetch(symbol,start,end):
    period1=int((start-timedelta(days=3)).timestamp())
    period2=int((end+timedelta(days=3)).timestamp())
    url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="")+"?"+urllib.parse.urlencode({"period1":period1,"period2":period2,"interval":"1d","events":"div,splits","includePrePost":"false"})
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"trading-agent-research/1.0"})
            with urllib.request.urlopen(req,timeout=20) as response:
                payload=json.loads(response.read().decode())
            result=payload["chart"]["result"][0]
            values=[]
            for ts,val in zip(result["timestamp"],result["indicators"]["adjclose"][0]["adjclose"]):
                if val is not None:
                    from datetime import datetime,timezone
                    values.append((datetime.fromtimestamp(int(ts),tz=timezone.utc).isoformat(),float(val)))
            return values
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,KeyError,IndexError,TypeError,ValueError) as exc:
            if attempt==3: raise
            time.sleep(2**attempt)
    raise RuntimeError("adjusted-close fetch failed")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--coverage-root",required=True)
    ap.add_argument("--output-root",required=True)
    ap.add_argument("--result",required=True)
    args=ap.parse_args()
    root=Path(args.coverage_root)
    manifest=json.loads((root/"snapshot_manifest.json").read_text())
    symbols=[d["symbol"] for d in manifest["data_snapshot"]["datasets"]]
    outroot=Path(args.output_root)
    dataset_rows=[]
    start=__import__("datetime").datetime.fromisoformat(manifest["selected_common_calendar_start"])
    end=__import__("datetime").datetime.fromisoformat(manifest["selected_common_calendar_end"])
    for symbol in symbols:
        values=fetch(symbol,start,end)
        target_ts=[row[0] for row in values]
        path=outroot/symbol/"adjusted_close.csv"
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("w",encoding="utf-8",newline="") as fh:
            w=csv.writer(fh); w.writerow(["timestamp","adjusted_close"])
            w.writerows(values)
        dataset_rows.append({"symbol":symbol,"path":str(path.as_posix()),"row_count":len(values),"fingerprint":fp(values)})
    bundle={"schema_version":"1.0","trial_id":"T-2026-09-28-076-INPUT-FREEZE","ohlcv_snapshot_manifest":str(root.as_posix())+"/snapshot_manifest.json","adjusted_close_datasets":dataset_rows,"performance_network_access":False}
    bundle["bundle_fingerprint"]=fp(bundle)
    result={"schema_version":"1.0","trial_id":bundle["trial_id"],"status":"INPUT_BUNDLE_FROZEN","bundle_fingerprint":bundle["bundle_fingerprint"],"datasets":dataset_rows,"performance_network_access":False,"selection_used":False,"performance_evaluation":False,"holdout_used_for_selection":False,"safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}}
    outroot.mkdir(parents=True,exist_ok=True)
    (outroot/"input_bundle_manifest.json").write_text(json.dumps(bundle,indent=2)+"\n")
    Path(args.result).parent.mkdir(parents=True,exist_ok=True)
    Path(args.result).write_text(json.dumps(result,indent=2)+"\n")
    print("Q076_INPUT_FREEZE_STATUS:",result["status"])
    print("Q076_INPUT_BUNDLE_FINGERPRINT:",result["bundle_fingerprint"])

if __name__=="__main__":
    main()
