"""Historical coverage preflight for Trial 030.
No returns, performance, or optimization are evaluated.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

from data.yahoo_loader import load_yahoo_history
from research.asset_universes import list_universes

CANDIDATES=(
    "VV","VHT","VFH","VIS","VAW","VDE","VPU","VGT",
    "SPDW","SPMD","SPEM","SPTL","SPIP",
)
TARGET_FETCH=3520
TARGET_COMMON=3500
EXCLUDED=("IWB","IEFA","BIV","BSV","VGIT","JNK","HDV","DBE","IYF","IYE","IYG","DJP","EPHE")
OUT=Path("research/preflight_trial_030_coverage_2026_09_24/report.json")

def main():
    registered=set()
    for u in list_universes():
        registered.update(u.symbols)
    overlap=set(CANDIDATES)&registered
    assert not overlap, f"Overlap with registered universes: {sorted(overlap)}"
    assert not (set(CANDIDATES)&set(EXCLUDED)), "Candidate overlaps invalid Trial 029 set."

    reports={}
    timestamps={}
    for symbol in CANDIDATES:
        quality={}
        candles=load_yahoo_history(
            symbol,"1d",TARGET_FETCH,
            allow_partial=True,
            skip_invalid_ohlc=True,
            quality_report=quality,
        )
        ts=[c.timestamp for c in candles]
        reports[symbol]={
            "count":len(candles),
            "data_start":candles[0].timestamp.isoformat() if candles else None,
            "data_end":candles[-1].timestamp.isoformat() if candles else None,
            "duplicate_timestamps":len(ts)-len(set(ts)),
            "quality_report":quality,
        }
        timestamps[symbol]=set(ts)
    common=set.intersection(*timestamps.values())
    result={
        "status":"PASS" if len(common)>=TARGET_COMMON and all(r["count"]>=TARGET_COMMON and r["duplicate_timestamps"]==0 for r in reports.values()) else "FAIL",
        "candidate_count":len(CANDIDATES),
        "target_fetch":TARGET_FETCH,
        "target_common":TARGET_COMMON,
        "common_calendar_count":len(common),
        "symbols":reports,
        "selection_basis":"historical coverage only; no performance data evaluated",
        "timestamp_run":datetime.now(timezone.utc).isoformat(),
        "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False},
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    print("TRIAL_030_PREFLIGHT_STATUS:",result["status"])
    print("TRIAL_030_COMMON_CALENDAR:",len(common))
    for s in CANDIDATES: print(s,reports[s]["count"],reports[s]["data_start"],reports[s]["data_end"])
    if result["status"]!="PASS": raise SystemExit(1)

if __name__=="__main__": main()
