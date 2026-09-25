"""Discovery-only Q011: point-in-time global information-intensity relationships.

This is hypothesis discovery, not a trading strategy and not a performance trial.
It uses a fixed date window, fixed assets, fixed event filter and fixed feature set.
No holdout selection, parameter search, promotion or orders are allowed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Callable, Iterable

from config import settings
from data.gdelt_events import GDELTEvent, download_daily_export, parse_event_zip
from research.event_intelligence import event_importance, is_high_confidence_international_event

DEFAULT_START = date(2026, 8, 24)
DEFAULT_END = date(2026, 9, 24)
DEFAULT_ASSETS = ("SPY", "TLT", "GLD")
FIXED_FEATURES = (
    "event_count",
    "attention_score",
    "source_breadth",
    "article_count",
    "negative_goldstein",
    "mean_tone",
)


def _yahoo_daily(symbol: str, start: date, end: date) -> dict[date, float]:
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
            result["timestamp"],
            result["indicators"]["adjclose"][0]["adjclose"],
        )
        if value is not None
    }


def _daily_event_features(events: Iterable[GDELTEvent]) -> dict[date, dict[str, float]]:
    grouped: dict[date, list[GDELTEvent]] = defaultdict(list)
    for event in events:
        if is_high_confidence_international_event(event):
            grouped[event.date_added.date()].append(event)

    result: dict[date, dict[str, float]] = {}
    for event_day, values in grouped.items():
        tones = [event.avg_tone for event in values]
        result[event_day] = {
            "event_count": float(len(values)),
            "attention_score": float(sum(event_importance(e) for e in values)),
            "source_breadth": float(sum(max(0, e.num_sources) for e in values)),
            "article_count": float(sum(max(0, e.num_articles) for e in values)),
            "negative_goldstein": float(
                sum(-e.goldstein_scale for e in values if e.goldstein_scale < 0)
            ),
            "mean_tone": float(mean(tones)) if tones else 0.0,
        }
    return result


def _window_features(
    daily: dict[date, dict[str, float]],
    start_exclusive: date,
    end_exclusive: date,
) -> dict[str, float]:
    values = [
        payload
        for event_day, payload in daily.items()
        if start_exclusive < event_day < end_exclusive
    ]
    if not values:
        return {feature: 0.0 for feature in FIXED_FEATURES}
    out = {feature: 0.0 for feature in FIXED_FEATURES}
    for payload in values:
        for feature in FIXED_FEATURES:
            out[feature] += payload[feature]
    out["mean_tone"] /= len(values)
    return out


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = min(len(xs), len(ys))
    if n < 3:
        return None
    xs, ys = xs[:n], ys[:n]
    mx, my = mean(xs), mean(ys)
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0.0 or dy == 0.0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (dx * dy)


def _ranks(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][1] == ordered[index][1]:
            end += 1
        rank = (index + end - 1) / 2.0 + 1.0
        for position in range(index, end):
            ranks[ordered[position][0]] = rank
        index = end
    return ranks


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    if min(len(xs), len(ys)) < 3:
        return None
    return _pearson(_ranks(xs), _ranks(ys))


def _load_events(
    start: date,
    end: date,
    event_loader: Callable[[date], Iterable[GDELTEvent]] | None,
) -> tuple[list[GDELTEvent], dict[str, int]]:
    stats = {"rows_seen": 0, "rows_skipped": 0}
    if event_loader is not None:
        events: list[GDELTEvent] = []
        day = start
        while day <= end:
            events.extend(event_loader(day))
            day += timedelta(days=1)
        return events, stats

    raw_dir = Path("research/q011_information_alpha/raw")
    events = []
    day = start
    while day <= end:
        path = raw_dir / f"{day.isoformat()}.zip"
        if not path.exists():
            download_daily_export(
                datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc),
                path,
            )
        day_stats = {"rows_seen": 0, "rows_skipped": 0}
        events.extend(parse_event_zip(path, strict=False, stats=day_stats))
        stats["rows_seen"] += day_stats["rows_seen"]
        stats["rows_skipped"] += day_stats["rows_skipped"]
        day += timedelta(days=1)
    return events, stats


def run_discovery(
    start: date = DEFAULT_START,
    end: date = DEFAULT_END,
    *,
    event_loader: Callable[[date], Iterable[GDELTEvent]] | None = None,
    market_loader: Callable[[str, date, date], dict[date, float]] | None = None,
    assets: tuple[str, ...] = DEFAULT_ASSETS,
    output_path: str | Path = "research/runs/information_alpha_discovery/q011.json",
) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")
    if end <= start or not assets:
        raise ValueError("end must be after start and assets must be non-empty.")

    market_loader = market_loader or _yahoo_daily
    events, parse_stats = _load_events(start, end, event_loader)
    daily = _daily_event_features(events)

    prices = {
        symbol: market_loader(symbol, start - timedelta(days=7), end + timedelta(days=10))
        for symbol in assets
    }

    market_days_by_asset = {
        symbol: sorted(day for day in values if start <= day <= end)
        for symbol, values in prices.items()
    }
    common_market_days = sorted(set.intersection(
        *[set(days) for days in market_days_by_asset.values()]
    ))
    if len(common_market_days) < 10:
        raise ValueError(
            f"Q011 requires at least 10 common market days; found {len(common_market_days)}."
        )

    observations: list[dict] = []
    for index in range(1, len(common_market_days)):
        previous_day = common_market_days[index - 1]
        target_day = common_market_days[index]
        feature_values = _window_features(daily, previous_day, target_day)
        market: dict[str, dict[str, float]] = {}
        for symbol in assets:
            days = sorted(prices[symbol])
            pos = days.index(target_day)
            if pos < 1:
                continue
            five_pos = pos + 5
            if five_pos >= len(days):
                five_return = None
            else:
                five_return = prices[symbol][days[five_pos]] / prices[symbol][target_day] - 1.0
            market[symbol] = {
                "next_market_day_return": prices[symbol][target_day] / prices[symbol][previous_day] - 1.0,
                "five_market_day_forward_return": five_return,
            }
        observations.append({
            "target_market_day": target_day.isoformat(),
            "event_window_start_exclusive": previous_day.isoformat(),
            "event_window_end_exclusive": target_day.isoformat(),
            "has_information_event": feature_values["event_count"] > 0,
            "features": feature_values,
            "market": market,
        })

    relationships: dict[str, dict[str, dict[str, float | int | None]]] = {}
    for symbol in assets:
        relationships[symbol] = {}
        for feature in FIXED_FEATURES:
            x = [row["features"][feature] for row in observations]
            one = [row["market"][symbol]["next_market_day_return"] for row in observations if symbol in row["market"]]
            five_pairs = [
                (row["features"][feature], row["market"][symbol]["five_market_day_forward_return"])
                for row in observations
                if symbol in row["market"] and row["market"][symbol]["five_market_day_forward_return"] is not None
            ]
            five_x = [pair[0] for pair in five_pairs]
            five_y = [pair[1] for pair in five_pairs]
            relationships[symbol][feature] = {
                "sample_next_day": len(one),
                "pearson_next_day": _pearson(x[:len(one)], one),
                "spearman_next_day": _spearman(x[:len(one)], one),
                "sample_five_day": len(five_y),
                "pearson_five_day": _pearson(five_x, five_y),
                "spearman_five_day": _spearman(five_x, five_y),
            }

    event_days = [row for row in observations if row["has_information_event"]]
    no_event_days = [row for row in observations if not row["has_information_event"]]

    def mean_return(rows: list[dict], symbol: str, horizon: str) -> float | None:
        values = [
            row["market"][symbol][horizon]
            for row in rows
            if symbol in row["market"] and row["market"][symbol][horizon] is not None
        ]
        return mean(values) if values else None

    report = {
        "schema_version": "1.0",
        "task_id": "Q-011-ORTHOGONAL-INFORMATION-ALPHA-DISCOVERY",
        "status": "DISCOVERY_ONLY",
        "research_only": True,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "assets": list(assets),
        "event_filter": "international event with num_articles >= 3",
        "point_in_time_contract": {
            "event_feature_window": "previous_market_day < event_day < target_market_day",
            "target_return": "previous_market_close -> target_market_close",
            "five_day_horizon": "target_market_close -> fifth subsequent market_close",
            "same_day_return_used": False,
        },
        "fixed_features": list(FIXED_FEATURES),
        "observations": observations,
        "feature_relationships": relationships,
        "event_presence_summary": {
            "observation_count": len(observations),
            "event_window_count": len(event_days),
            "no_event_window_count": len(no_event_days),
            "event_window_next_day_mean": {
                symbol: mean_return(event_days, symbol, "next_market_day_return")
                for symbol in assets
            },
            "no_event_window_next_day_mean": {
                symbol: mean_return(no_event_days, symbol, "next_market_day_return")
                for symbol in assets
            },
        },
        "data_quality": {
            "event_rows_seen": parse_stats["rows_seen"],
            "event_rows_skipped": parse_stats["rows_skipped"],
        },
        "selection_used": False,
        "holdout_used": False,
        "parameter_search_used": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
    }
    canonical = json.dumps(
        report, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    report["fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=DEFAULT_START.isoformat())
    parser.add_argument("--end", default=DEFAULT_END.isoformat())
    args = parser.parse_args()
    report = run_discovery(
        date.fromisoformat(args.start),
        date.fromisoformat(args.end),
    )
    print("Q011_STATUS:", report["status"])
    print("Q011_FINGERPRINT:", report["fingerprint"])
    print("Q011_OBSERVATIONS:", len(report["observations"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
