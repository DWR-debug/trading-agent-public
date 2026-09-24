"""Trial 017: descriptive political-event to next-market-day response study."""
from __future__ import annotations
import argparse
import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Callable, Iterable
from config import settings
from data.gdelt_events import GDELTEvent, download_daily_export, parse_event_zip
from research.event_intelligence import aggregate_daily_events, conflict_flag

DEFAULT_ASSETS = ("SPY", "TLT", "GLD")

def _yahoo_daily(symbol: str, start: date, end: date) -> dict[date, float]:
    import urllib.parse
    import urllib.request
    params = {
        "period1": int(datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).timestamp()),
        "period2": int(datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).timestamp()),
        "interval": "1d",
        "events": "div,splits",
    }
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol, safe='')}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "trading-agent-research/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))["chart"]["result"][0]
    return {
        datetime.fromtimestamp(ts, tz=timezone.utc).date(): float(value)
        for ts, value in zip(result["timestamp"], result["indicators"]["adjclose"][0]["adjclose"])
        if value is not None
    }

def _forward_returns(closes: dict[date, float]) -> dict[date, tuple[float, float]]:
    days = sorted(closes)
    return {
        day: (
            closes[days[i + 1]] / closes[day] - 1.0,
            closes[days[min(i + 5, len(days) - 1)]] / closes[day] - 1.0,
        )
        for i, day in enumerate(days[:-1])
    }

def run_trial(
    start: date,
    end: date,
    *,
    event_loader: Callable[[date], Iterable[GDELTEvent]] | None = None,
    market_loader: Callable[[str, date, date], dict[date, float]] | None = None,
    assets: tuple[str, ...] = DEFAULT_ASSETS,
    output_path: str | Path = "research/trial_017_political_event_intelligence/report.json",
) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")
    if end <= start or not assets:
        raise ValueError("end must be after start and assets must be non-empty.")
    raw_dir = Path("research/trial_017_political_event_intelligence/raw")
    if event_loader is None:
        def event_loader(day: date) -> Iterable[GDELTEvent]:
            path = raw_dir / f"{day.isoformat()}.zip"
            if not path.exists():
                download_daily_export(datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc), path)
            return parse_event_zip(path)
    if market_loader is None:
        market_loader = _yahoo_daily
    events: list[GDELTEvent] = []
    day = start
    while day <= end:
        events.extend(event_loader(day))
        day += timedelta(days=1)
    features = {item.event_date: item for item in aggregate_daily_events(events)}
    per_asset = {
        symbol: _forward_returns(market_loader(symbol, start, end + timedelta(days=7)))
        for symbol in assets
    }
    observations = []
    for event_day, item in features.items():
        market = {}
        for symbol in assets:
            value = per_asset[symbol].get(event_day)
            market[symbol] = {"next_day_return": value[0], "five_day_return": value[1]} if value else None
        if any(value is not None for value in market.values()):
            observations.append({
                "event_day": event_day.isoformat(),
                "conflict_flag": conflict_flag(item),
                "event_count": item.event_count,
                "material_conflict_count": item.material_conflict_count,
                "negative_goldstein_sum": item.negative_goldstein_sum,
                "mention_weighted_conflict": item.mention_weighted_conflict,
                "market": market,
            })
    def summarize(flag: bool) -> dict:
        subset = [row for row in observations if row["conflict_flag"] is flag]
        result = {"observation_count": len(subset)}
        for symbol in assets:
            one = [row["market"][symbol]["next_day_return"] for row in subset if row["market"][symbol] is not None]
            five = [row["market"][symbol]["five_day_return"] for row in subset if row["market"][symbol] is not None]
            result[symbol] = {"next_day_mean": mean(one) if one else None, "five_day_mean": mean(five) if five else None}
        return result
    report = {
        "schema_version": 1,
        "trial_id": "017",
        "name": "political_event_intelligence_baseline",
        "status": "COMPLETED",
        "research_only": True,
        "selection_used": False,
        "parameter_search_used": False,
        "data_scope": {"start": start.isoformat(), "end": end.isoformat(), "assets": list(assets), "event_source": "GDELT 2.0 Event exports"},
        "point_in_time_contract": {
            "event_date_features_join_to": "next_available_market_day",
            "same_day_performance_used_for_selection": False,
        },
        "observations": observations,
        "summary": {"conflict_days": summarize(True), "non_conflict_days": summarize(False)},
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False},
    }
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    return report

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--end", default="2025-03-31")
    args = parser.parse_args()
    report = run_trial(date.fromisoformat(args.start), date.fromisoformat(args.end))
    print("TRIAL_017_STATUS:", report["status"])
    print("TRIAL_017_CONFLICT_DAYS:", report["summary"]["conflict_days"]["observation_count"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
