"""Trial 017b: non-overlapping political event window control."""
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
        "interval": "1d", "events": "div,splits",
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


def _event_window_feature(daily_features: dict[date, object], start_exclusive: date, end_exclusive: date) -> dict:
    selected = [f for day, f in daily_features.items() if start_exclusive < day < end_exclusive]
    if not selected:
        return {
            "event_day_count": 0, "international_event_count": 0,
            "high_confidence_international_count": 0,
            "international_material_conflict_count": 0,
            "negative_goldstein_sum": 0.0, "mention_weighted_conflict": 0.0,
            "source_count": 0, "mean_tone": 0.0, "international_conflict_flag": False,
        }
    tones = [f.mean_tone for f in selected]
    return {
        "event_day_count": len(selected),
        "international_event_count": sum(f.international_event_count for f in selected),
        "high_confidence_international_count": sum(f.high_confidence_international_count for f in selected),
        "international_material_conflict_count": sum(f.international_material_conflict_count for f in selected),
        "negative_goldstein_sum": sum(f.negative_goldstein_sum for f in selected),
        "mention_weighted_conflict": sum(f.mention_weighted_conflict for f in selected),
        "source_count": sum(f.source_count for f in selected),
        "mean_tone": mean(tones),
        "international_conflict_flag": any(conflict_flag(f) for f in selected),
    }


def _target_observations(prices: dict[date, float], daily_features: dict[date, object], start: date, end: date) -> list[dict]:
    market_days = [d for d in sorted(prices) if start <= d <= end]
    out = []
    for i in range(1, len(market_days)):
        previous_day, target_day = market_days[i - 1], market_days[i]
        feature = _event_window_feature(daily_features, previous_day, target_day)
        horizon = i + 4
        five = prices[market_days[horizon]] / prices[target_day] - 1.0 if horizon < len(market_days) else None
        out.append({
            "target_market_day": target_day.isoformat(),
            "event_window_start_exclusive": previous_day.isoformat(),
            "event_window_end_exclusive": target_day.isoformat(),
            **feature,
            "market": {
                "next_market_day_return": prices[target_day] / prices[previous_day] - 1.0,
                "five_market_day_forward_return": five,
            },
        })
    return out


def run_trial(start: date, end: date, *, event_loader: Callable[[date], Iterable[GDELTEvent]] | None = None, market_loader: Callable[[str, date, date], dict[date, float]] | None = None, assets: tuple[str, ...] = DEFAULT_ASSETS, output_path: str | Path = "research/trial_017b_event_window/report.json") -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")
    if end <= start or not assets:
        raise ValueError("end must be after start and assets must be non-empty.")
    raw_dir = Path("research/trial_017b_event_window/raw")
    using_downloaded = event_loader is None
    if market_loader is None:
        market_loader = _yahoo_daily
    events: list[GDELTEvent] = []
    parse_stats = {"rows_seen": 0, "rows_skipped": 0}
    day = start
    while day <= end:
        if using_downloaded:
            path = raw_dir / f"{day.isoformat()}.zip"
            if not path.exists():
                download_daily_export(datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc), path)
            stats = {"rows_seen": 0, "rows_skipped": 0}
            events.extend(parse_event_zip(path, strict=False, stats=stats))
            parse_stats["rows_seen"] += stats["rows_seen"]
            parse_stats["rows_skipped"] += stats["rows_skipped"]
        else:
            events.extend(event_loader(day))
        day += timedelta(days=1)
    daily_features = {f.event_date: f for f in aggregate_daily_events(events, international_only=True, high_confidence_only=True)}
    prices = {symbol: market_loader(symbol, start - timedelta(days=7), end + timedelta(days=10)) for symbol in assets}
    per_asset = {symbol: _target_observations(values, daily_features, start, end) for symbol, values in prices.items()}
    targets = sorted(set.intersection(*[{r["target_market_day"] for r in rows} for rows in per_asset.values()]))
    by_asset = {symbol: {r["target_market_day"]: r for r in rows} for symbol, rows in per_asset.items()}
    observations = []
    for target in targets:
        ref = by_asset[assets[0]][target]
        observations.append({
            k: ref[k] for k in ("target_market_day", "event_window_start_exclusive", "event_window_end_exclusive", "event_day_count", "international_event_count", "high_confidence_international_count", "international_material_conflict_count", "negative_goldstein_sum", "mention_weighted_conflict", "source_count", "mean_tone", "international_conflict_flag")
        } | {
            "has_qualifying_event": ref["high_confidence_international_count"] > 0,
            "market": {symbol: by_asset[symbol][target]["market"] for symbol in assets},
        })
    def summary(predicate: Callable[[dict], bool]) -> dict:
        subset = [r for r in observations if predicate(r)]
        result = {"observation_count": len(subset)}
        for symbol in assets:
            one = [r["market"][symbol]["next_market_day_return"] for r in subset]
            five = [r["market"][symbol]["five_market_day_forward_return"] for r in subset if r["market"][symbol]["five_market_day_forward_return"] is not None]
            result[symbol] = {"next_market_day_mean": mean(one) if one else None, "five_market_day_forward_mean": mean(five) if five else None}
        return result
    report = {
        "schema_version": 1, "trial_id": "017b", "name": "political_event_window_control",
        "status": "COMPLETED", "research_only": True, "selection_used": False, "parameter_search_used": False,
        "data_scope": {"start": start.isoformat(), "end": end.isoformat(), "assets": list(assets), "event_source": "GDELT 2.0 daily event exports", "event_filter": "international actors, num_articles >= 3"},
        "point_in_time_contract": {"window": "previous_market_day < event_date < target_market_day", "target_return": "previous_market_close -> target_market_close", "five_day_horizon": "target_market_close -> fifth subsequent market_close", "same_target_market_return_reused_for_multiple_event_dates": False, "same_day_performance_used_for_selection": False},
        "data_quality": {"event_rows_seen": parse_stats["rows_seen"], "event_rows_skipped": parse_stats["rows_skipped"], "event_row_skip_rate": parse_stats["rows_skipped"] / parse_stats["rows_seen"] if parse_stats["rows_seen"] else 0.0},
        "observations": observations,
        "summary": {"all_market_days": summary(lambda _: True), "qualifying_event_windows": summary(lambda r: r["has_qualifying_event"]), "no_qualifying_event_windows": summary(lambda r: not r["has_qualifying_event"]), "conflict_windows": summary(lambda r: r["international_conflict_flag"]), "non_conflict_windows": summary(lambda r: not r["international_conflict_flag"])},
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
    print("TRIAL_017B_STATUS:", report["status"])
    print("TRIAL_017B_OBSERVATIONS:", len(report["observations"]))
    print("TRIAL_017B_EVENT_WINDOWS:", report["summary"]["qualifying_event_windows"]["observation_count"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())