"""Q014: one-year fixed GDELT mechanism/redundancy diagnostic with resumable chunks."""
from __future__ import annotations
import argparse, hashlib, json
from datetime import date, timedelta
from pathlib import Path
from config import settings
from automation.information_alpha_discovery import DEFAULT_ASSETS, FIXED_FEATURES, _daily_event_features, _load_events, _window_features, _yahoo_daily
from automation.information_alpha_redundancy import analyze_redundancy_base

DEFAULT_START = date(2025, 9, 25)
DEFAULT_END = date(2026, 9, 24)
MIN_TOTAL_OBSERVATIONS = 80
MIN_EVENT_WINDOWS = 40
CHUNK_WINDOWS = (
    ("01", date(2025, 9, 25), date(2025, 12, 25)),
    ("02", date(2025, 12, 26), date(2026, 3, 25)),
    ("03", date(2026, 3, 26), date(2026, 6, 25)),
    ("04", date(2026, 6, 26), date(2026, 9, 24)),
)

def _assert_safety():
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False: raise RuntimeError("Paper-only safety contract violated.")

def _chunk_spec(chunk_id):
    for spec in CHUNK_WINDOWS:
        if spec[0] == chunk_id: return spec
    raise ValueError(f"Unknown Q014 chunk id: {chunk_id}")

def _build_observations(start, end, daily, prices):
    price_maps = {symbol: {date.fromisoformat(day): value for day, value in values.items()} for symbol, values in prices.items()}
    market_days_by_asset = {symbol: sorted(day for day in values if start <= day <= end) for symbol, values in price_maps.items()}
    common_market_days = sorted(set.intersection(*[set(days) for days in market_days_by_asset.values()]))
    if len(common_market_days) < 10: raise ValueError(f"Q014 requires at least 10 common market days; found {len(common_market_days)}.")
    observations=[]
    for index in range(1, len(common_market_days)):
        previous_day, target_day = common_market_days[index-1], common_market_days[index]
        feature_values = _window_features(daily, previous_day, target_day)
        market={}
        for symbol in DEFAULT_ASSETS:
            days=sorted(price_maps[symbol]); pos=days.index(target_day); five_pos=pos+5
            five_return=None if five_pos >= len(days) else price_maps[symbol][days[five_pos]] / price_maps[symbol][target_day] - 1.0
            market[symbol]={"next_market_day_return": price_maps[symbol][target_day] / price_maps[symbol][previous_day] - 1.0, "five_market_day_forward_return": five_return}
        observations.append({"target_market_day":target_day.isoformat(),"event_window_start_exclusive":previous_day.isoformat(),"event_window_end_exclusive":target_day.isoformat(),"has_information_event":feature_values["event_count"]>0,"features":feature_values,"market":market})
    return observations

def collect_q014_chunk(chunk_id, *, output_dir="research/runs/information_alpha_redundancy/q014_chunks"):
    _assert_safety(); _, start, end = _chunk_spec(chunk_id); root=Path(output_dir); root.mkdir(parents=True,exist_ok=True)
    events, parse_stats = _load_events(start,end,None); daily=_daily_event_features(events)
    prices={symbol:_yahoo_daily(symbol,start-timedelta(days=7),end+timedelta(days=10)) for symbol in DEFAULT_ASSETS}
    payload={"schema_version":"1.0","task_id":"Q-014-INFORMATION-ALPHA-MECHANISM-REDUNDANCY-LONG-WINDOW","chunk_id":chunk_id,"start":start.isoformat(),"end":end.isoformat(),"assets":list(DEFAULT_ASSETS),"fixed_features":list(FIXED_FEATURES),"daily_event_features":{day.isoformat():values for day,values in sorted(daily.items())},"prices":{symbol:{day.isoformat():value for day,value in sorted(values.items())} for symbol,values in sorted(prices.items())},"data_quality":{"event_rows_seen":parse_stats["rows_seen"],"event_rows_skipped":parse_stats["rows_skipped"]},"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False,"selection_used":False,"holdout_used":False,"parameter_search_used":False,"feature_selection_used":False,"asset_selection_used":False,"horizon_selection_used":False}
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=True); payload["fingerprint"]=hashlib.sha256(canonical.encode()).hexdigest()
    (root/f"q014_chunk_{chunk_id}.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8"); return payload

def _load_chunks(chunk_dir):
    root=Path(chunk_dir); reports=[]; expected=[]
    for chunk_id,start,end in CHUNK_WINDOWS:
        expected.append((chunk_id,start.isoformat(),end.isoformat())); path=root/f"q014_chunk_{chunk_id}.json"
        if not path.exists(): raise FileNotFoundError(f"Missing Q014 chunk: {path}")
        reports.append(json.loads(path.read_text(encoding="utf-8")))
    actual=[(r["chunk_id"],r["start"],r["end"]) for r in reports]
    if actual!=expected: raise ValueError("Q014 chunk window contract mismatch.")
    return reports

def aggregate_q014_chunks(*,chunk_dir="research/runs/information_alpha_redundancy/q014_chunks",output_dir="research/runs/information_alpha_redundancy/q014"):
    _assert_safety(); reports=_load_chunks(chunk_dir); daily={}; prices={symbol:{} for symbol in DEFAULT_ASSETS}; rows_seen=rows_skipped=0
    for report in reports:
        rows_seen += report["data_quality"]["event_rows_seen"]; rows_skipped += report["data_quality"]["event_rows_skipped"]
        for day,payload in report["daily_event_features"].items():
            if day in daily and daily[day]!=payload: raise ValueError(f"Conflicting event features for duplicate day {day}.")
            daily[day]=payload
        for symbol in DEFAULT_ASSETS:
            for day,value in report["prices"][symbol].items():
                existing=prices[symbol].get(day)
                if existing is not None and existing!=value: raise ValueError(f"Conflicting price for {symbol} on {day}.")
                prices[symbol][day]=value
    observations=_build_observations(DEFAULT_START,DEFAULT_END,daily,prices)
    base={"observations":observations,"point_in_time_contract":{"event_feature_window":"previous_market_day < event_day < target_market_day","target_return":"previous_market_close -> target_market_close","five_day_horizon":"target_market_close -> fifth subsequent market_close","same_day_return_used":False},"data_quality":{"event_rows_seen":rows_seen,"event_rows_skipped":rows_skipped,"source":"Q014 resumable four-chunk collection"}}
    root=Path(output_dir); report=analyze_redundancy_base(base,DEFAULT_START,DEFAULT_END,output_dir=root)
    report.update({"task_id":"Q-014-INFORMATION-ALPHA-MECHANISM-REDUNDANCY-LONG-WINDOW","source_task":"Q-013-INFORMATION-ALPHA-MECHANISM-REDUNDANCY-DIAGNOSTIC","status":"COMPLETED_DISCOVERY_ONLY" if report["observations"]["total"]>=MIN_TOTAL_OBSERVATIONS and report["observations"]["event_windows"]>=MIN_EVENT_WINDOWS else "DATA_INSUFFICIENT","window_contract":{"calendar_days":365,"start":DEFAULT_START.isoformat(),"end":DEFAULT_END.isoformat(),"min_total_observations":MIN_TOTAL_OBSERVATIONS,"min_event_windows":MIN_EVENT_WINDOWS,"chunk_count":len(CHUNK_WINDOWS),"chunk_ids":[x[0] for x in CHUNK_WINDOWS]},"performance_trial_authorized":False})
    for key in ("selection_used","holdout_used","parameter_search_used","feature_selection_used","asset_selection_used","horizon_selection_used"): report[key]=False
    canonical=json.dumps({k:v for k,v in report.items() if k!="fingerprint"},sort_keys=True,separators=(",",":"),ensure_ascii=True); report["fingerprint"]=hashlib.sha256(canonical.encode()).hexdigest()
    root.mkdir(parents=True,exist_ok=True); (root/"q014_redundancy_long_window.json").write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8"); return report

def run_q014(start=DEFAULT_START,end=DEFAULT_END,*,output_dir="research/runs/information_alpha_redundancy/q014"):
    _assert_safety()
    if (end-start).days!=364 or start!=DEFAULT_START or end!=DEFAULT_END: raise ValueError("Q014 window is preregistered and requires the exact 365-calendar-day interval.")
    root=Path(output_dir); chunk_dir=root/"chunks"
    for chunk_id,_,_ in CHUNK_WINDOWS: collect_q014_chunk(chunk_id,output_dir=chunk_dir)
    return aggregate_q014_chunks(chunk_dir=chunk_dir,output_dir=root)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--mode",choices=("run","collect_chunk","aggregate"),default="run"); parser.add_argument("--chunk-id"); parser.add_argument("--chunk-dir",default="research/runs/information_alpha_redundancy/q014_chunks"); parser.add_argument("--output-dir",default="research/runs/information_alpha_redundancy/q014"); args=parser.parse_args()
    if args.mode=="collect_chunk":
        if args.chunk_id is None: raise ValueError("--chunk-id is required for collect_chunk")
        report=collect_q014_chunk(args.chunk_id,output_dir=args.chunk_dir); print("Q014_CHUNK:",report["chunk_id"]); print("Q014_CHUNK_FINGERPRINT:",report["fingerprint"]); return 0
    report=aggregate_q014_chunks(chunk_dir=args.chunk_dir,output_dir=args.output_dir) if args.mode=="aggregate" else run_q014(output_dir=args.output_dir)
    print("Q014_STATUS:",report["status"]); print("Q014_FINGERPRINT:",report["fingerprint"]); print("Q014_OBSERVATIONS:",report["observations"]["total"]); print("Q014_EVENT_WINDOWS:",report["observations"]["event_windows"]); return 0 if report["status"]!="DATA_INSUFFICIENT" else 3

if __name__ == "__main__": raise SystemExit(main())