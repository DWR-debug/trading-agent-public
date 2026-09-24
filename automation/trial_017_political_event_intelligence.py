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
from research.event_intelligence import (
    aggregate_daily_events,
    conflict_flag,
    is_high_confidence_international_event,
)

DEFAULT_ASSETS = ("SPY", "TLT", "GLD")


def _yahoo_daily(symbol: str, start: date, end: date) -> dict[date, float]:
    import urllib.parse
    import urllib.request

    params = {
        "period1": int(
            datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).timestamp()
        ),
        "period2": int(
            datetime.combine(
                end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc
            ).timestamp()
        ),
        "interval": "1d",
        "events": "div,splits",
    }
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{urllib.parse.quote(symbol, safe='')}?{urllib.parse.urlencode(params)}"
    )
    request = urllib.request.Request(
        url, headers={"User-Agent": "trading-agent-research/1.0"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))["chart"]["result"][0]
    return {
        datetime.fromtimestamp(ts, tz=timezone.utc).date(): float(value)
        for ts, value in zip(
            result["timestamp"], result["indicators"]["adjclose"][0]["adjclose"]
        )
        if value is not None
    }


def _event_forward_returns(
    closes: dict[date, float], event_day: date
) -> tuple[float, float | None] | None:
    days = sorted(closes)
    if not days:
        return None
    next_index = next((i for i, day in enumerate(days) if day > event_day), None)
    if next_index is None:
        return None
    origin_index = next_index - 1
    if origin_index < 0:
        return None
    horizon_index = next_index + 4
    origin = closes[days[origin_index]]
    five_day = (
        closes[days[horizon_index]] / origin - 1.0
        if horizon_index < len(days)
        else None
    )
    return (
        closes[days[next_index]] / origin - 1.0,
        five_day,
    )


def _market_forward_returns(
    closes: dict[date, float]
) -> dict[date, tuple[float, float]]:
    days = sorted(closes)
    return {
        days[i]: (
            closes[days[i + 1]] / closes[days[i]] - 1.0,
            closes[days[min(i + 5, len(days) - 1)]] / closes[days[i]] - 1.0,
        )
        for i in range(len(days) - 1)
    }


def _mean(rows: list[float]) -> float | None:
    return mean(rows) if rows else None


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
                download_daily_export(
                    datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc),
                    path,
                )
            return parse_event_zip(path)

    if market_loader is None:
        market_loader = _yahoo_daily

    events: list[GDELTEvent] = []
    parse_stats = {"rows_seen": 0, "rows_skipped": 0}
    day = start
    while day <= end:
        if event_loader is None:
            day_stats = {"rows_seen": 0, "rows_skipped": 0}
            events.extend(parse_event_zip(raw_dir / f"{day.isoformat()}.zip", strict=False, stats=day_stats))
            parse_stats["rows_seen"] += day_stats["rows_seen"]
            parse_stats["rows_skipped"] += day_stats["rows_skipped"]
        else:
            events.extend(event_loader(day))
        day += timedelta(days=1)

    features = {
        item.event_date: item
        for item in aggregate_daily_events(
            events,
            international_only=True,
            high_confidence_only=True,
        )
    }

    market_start = start - timedelta(days=7)
    market_end = end + timedelta(days=10)
    prices = {
        symbol: market_loader(symbol, market_start, market_end)
        for symbol in assets
    }
    all_market_returns = {
        symbol: _market_forward_returns(values)
        for symbol, values in prices.items()
    }

    observations = []
    for event_day, item in features.items():
        market = {}
        for symbol in assets:
            value = _event_forward_returns(prices[symbol], event_day)
            market[symbol] = (
                {
                    "next_market_day_return": value[0],
                    "five_market_day_return": value[1],
                }
                if value is not None
                else None
            )
        if any(value is not None for value in market.values()):
            observations.append(
                {
                    "event_day": event_day.isoformat(),
                    "international_event_count": item.international_event_count,
                    "high_confidence_international_count": item.high_confidence_international_count,
                    "international_conflict_flag": conflict_flag(item),
                    "international_material_conflict_count": item.international_material_conflict_count,
                    "negative_goldstein_sum": item.negative_goldstein_sum,
                    "mention_weighted_conflict": item.mention_weighted_conflict,
                    "source_count": item.source_count,
                    "mean_tone": item.mean_tone,
                    "market": market,
                }
            )

    def summarize(predicate: Callable[[dict], bool]) -> dict:
        subset = [row for row in observations if predicate(row)]
        result = {"observation_count": len(subset)}
        for symbol in assets:
            one = [
                row["market"][symbol]["next_market_day_return"]
                for row in subset
                if row["market"][symbol] is not None
            ]
            five = [
                row["market"][symbol]["five_market_day_return"]
                for row in subset
                if row["market"][symbol] is not None
            ]
            result[symbol] = {
                "next_market_day_mean": _mean(one),
                "five_market_day_mean": _mean(five),
            }
        return result

    baseline = {}
    for symbol in assets:
        one = [value[0] for value in all_market_returns[symbol].values()]
        five = [value[1] for value in all_market_returns[symbol].values()]
        baseline[symbol] = {
            "observation_count": len(one),
            "next_market_day_mean": _mean(one),
            "five_market_day_mean": _mean(five),
        }

    conflict = summarize(lambda row: row["international_conflict_flag"])
    non_conflict = summarize(lambda row: not row["international_conflict_flag"])

    abnormal = {}
    for symbol in assets:
        event_values = [
            row["market"][symbol]["next_market_day_return"]
            for row in observations
            if row["market"][symbol] is not None
        ]
        event_mean = _mean(event_values)
        baseline_mean = baseline[symbol]["next_market_day_mean"]
        abnormal[symbol] = (
            None if event_mean is None or baseline_mean is None
            else event_mean - baseline_mean
        )

    report = {
        "schema_version": 2,
        "trial_id": "017",
        "name": "political_event_intelligence_baseline",
        "status": "COMPLETED",
        "research_only": True,
        "selection_used": False,
        "parameter_search_used": False,
        "data_quality": {
            "event_rows_seen": parse_stats["rows_seen"],
            "event_rows_skipped": parse_stats["rows_skipped"],
            "event_row_skip_rate": (
                parse_stats["rows_skipped"] / parse_stats["rows_seen"]
                if parse_stats["rows_seen"] else 0.0
            ),
        },
        "data_scope": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "assets": list(assets),
            "event_source": "GDELT 2.0 Event exports",
            "event_filter": "international actors, num_articles >= 3",
        },
        "point_in_time_contract": {
            "event_timestamp_field": "DATEADDED UTC",
            "event_day_features_join_to": "first market day strictly after event day",
            "five_day_horizon": "fifth market day strictly after event day",
            "weekend_events_use_previous_market_close_as_origin": True,
            "same_day_performance_used_for_selection": False,
        },
        "observations": observations,
        "summary": {
            "all_market_days": baseline,
            "international_conflict_days": conflict,
            "international_non_conflict_days": non_conflict,
            "event_day_next_market_day_excess_vs_market_baseline": abnormal,
        },
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--end", default="2025-03-31")
    args = parser.parse_args()
    report = run_trial(date.fromisoformat(args.start), date.fromisoformat(args.end))
    print("TRIAL_017_STATUS:", report["status"])
    print(
        "TRIAL_017_CONFLICT_DAYS:",
        report["summary"]["international_conflict_days"]["observation_count"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
