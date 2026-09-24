"""Single preregistered political-event relative-value alpha validation."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from config import settings
from research.asset_universes import get_universe
from research.event_intelligence import aggregate_daily_events
from research.protocol import dataset_fingerprint
from research.event_alpha import EventRelativeValuePolicy

TARGET_UNIVERSE = "validation_2026_09_24_event_alpha"
TARGET_COUNT = 3500
RESEARCH_START = date(2025, 4, 1)
RESEARCH_END = date(2025, 6, 30)
HOLDOUT_START = date(2025, 7, 1)
HOLDOUT_END = date(2025, 9, 30)
ASSETS = ("IWB", "GDX", "BIL")
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005

def _fp(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _yahoo_daily(symbol: str, start: date, end: date) -> dict[date, float]:
    import urllib.parse
    import urllib.request
    params = {
        "period1": int(datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).timestamp()),
        "period2": int(datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).timestamp()),
        "interval": "1d",
        "events": "div,splits",
    }
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{urllib.parse.quote(symbol, safe='')}?{urllib.parse.urlencode(params)}"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "trading-agent-research/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))["chart"]["result"][0]
    return {
        datetime.fromtimestamp(ts, tz=timezone.utc).date(): float(value)
        for ts, value in zip(
            result["timestamp"], result["indicators"]["adjclose"][0]["adjclose"]
        )
        if value is not None
    }

def _event_features(start: date, end: date, raw_dir: Path) -> tuple[dict[date, object], dict[str, int]]:
    from data.gdelt_events import download_daily_export, parse_event_zip
    events = []
    parse_stats = {"rows_seen": 0, "rows_skipped": 0}
    day = start
    while day <= end:
        path = raw_dir / f"{day.isoformat()}.zip"
        if not path.exists():
            download_daily_export(
                datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc),
                path,
            )
        stats = {"rows_seen": 0, "rows_skipped": 0}
        events.extend(parse_event_zip(path, strict=False, stats=stats))
        parse_stats["rows_seen"] += stats["rows_seen"]
        parse_stats["rows_skipped"] += stats["rows_skipped"]
        day += timedelta(days=1)
    return ({
        item.event_date: item
        for item in aggregate_daily_events(
            events,
            international_only=True,
            high_confidence_only=True,
        )
    }, parse_stats)

def _build_rows(
    prices: dict[str, dict[date, float]],
    features: dict[date, object],
    start: date,
    end: date,
    policy: EventRelativeValuePolicy,
) -> list[dict]:
    common = set.intersection(*[set(values) for values in prices.values()])
    days = [day for day in sorted(common) if start <= day <= end]
    previous_days = [day for day in sorted(common) if day < start]
    if not previous_days or not days:
        raise ValueError("Insufficient market history.")
    days.insert(0, previous_days[-1])

    previous_weights: dict[str, float] = {}
    rows: list[dict] = []
    for index in range(1, len(days)):
        previous_day, target_day = days[index - 1], days[index]
        window_features = [
            item
            for event_day, item in features.items()
            if previous_day <= event_day < target_day
        ]
        qualifying = any(
            item.international_material_conflict_count > 0
            and item.high_confidence_international_count > 0
            for item in window_features
        )
        weights = dict(policy.weights) if qualifying else {}
        gross = sum(
            weights.get(symbol, 0.0)
            * (prices[symbol][target_day] / prices[symbol][previous_day] - 1.0)
            for symbol in policy.symbols
        )
        turnover = sum(
            abs(weights.get(symbol, 0.0) - previous_weights.get(symbol, 0.0))
            for symbol in policy.symbols
        )
        rows.append(
            {
                "target_day": target_day.isoformat(),
                "previous_market_day": previous_day.isoformat(),
                "qualifying_event": qualifying,
                "event_day_count": len(window_features),
                "gross_return": gross,
                "turnover": turnover,
            }
        )
        previous_weights = weights

    if previous_weights:
        rows.append(
            {
                "target_day": (end + timedelta(days=1)).isoformat(),
                "previous_market_day": days[-1].isoformat(),
                "qualifying_event": False,
                "event_day_count": 0,
                "gross_return": 0.0,
                "turnover": sum(abs(value) for value in previous_weights.values()),
                "liquidation": True,
            }
        )
    return rows

def _stats(rows: list[dict], cost_multiplier: float) -> dict:
    equity = peak = 1.0
    max_dd = 0.0
    gross_profit = gross_loss = 0.0
    turnover = 0.0
    active_days = 0
    event_returns: list[float] = []

    for row in rows:
        net = (
            float(row["gross_return"])
            - cost_multiplier * (FEE_RATE + SLIPPAGE_RATE) * float(row["turnover"])
        )
        equity *= 1.0 + net
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak)
        if net > 0.0:
            gross_profit += net
        elif net < 0.0:
            gross_loss -= net
        turnover += float(row["turnover"])
        if row.get("qualifying_event"):
            active_days += 1
            event_returns.append(net)

    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": (
            gross_profit / gross_loss
            if gross_loss > 0.0
            else ("inf" if gross_profit > 0.0 else 0.0)
        ),
        "turnover": turnover,
        "active_event_days": active_days,
        "event_day_mean_net_return": (
            sum(event_returns) / len(event_returns)
            if event_returns
            else None
        ),
        "day_count": len(rows),
    }

def run_validation(
    *,
    market_dir: Path,
    market_manifest: Path,
    event_raw_dir: Path,
    output: Path,
) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")
    universe = get_universe(TARGET_UNIVERSE)
    if tuple(universe.symbols) != ASSETS:
        raise ValueError("Event-alpha universe registration mismatch.")

    manifest = json.loads(market_manifest.read_text(encoding="utf-8"))
    manifest_symbols = tuple(item["symbol"] for item in manifest.get("datasets", []))
    if (
        manifest.get("universe") != TARGET_UNIVERSE
        or manifest.get("target_count") != TARGET_COUNT
        or manifest_symbols != ASSETS
        or manifest.get("source") != "yahoo_chart"
    ):
        raise ValueError("Event-alpha market manifest contract mismatch.")
    safety_manifest = manifest.get("safety", {})
    if (
        safety_manifest.get("paper_only") is not True
        or safety_manifest.get("live_trading_enabled") is not False
    ):
        raise RuntimeError("Market manifest safety contract violated.")

    from automation.candidate_validation_50_50_vol_budget import load_bars

    prices: dict[str, dict[date, float]] = {}
    adjusted_price_fingerprints: dict[str, str] = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = load_bars(
            market_dir / symbol / "1d.csv",
            expected_count=int(item["candle_count"]),
        )
        if (
            len(bars) != TARGET_COUNT
            or dataset_fingerprint(bars) != item["fingerprint"]
        ):
            raise ValueError(f"{symbol}: dataset fingerprint mismatch")
        adjusted = _yahoo_daily(
            symbol,
            RESEARCH_START - timedelta(days=7),
            HOLDOUT_END + timedelta(days=7),
        )
        prices[symbol] = adjusted
        adjusted_price_fingerprints[symbol] = _fp(
            sorted((day.isoformat(), value) for day, value in adjusted.items())
        )

    event_feature_start = RESEARCH_START - timedelta(days=7)
    features, event_parse_stats = _event_features(
        event_feature_start,
        HOLDOUT_END,
        event_raw_dir,
    )
    policy = EventRelativeValuePolicy()

    research_rows = _build_rows(
        prices,
        features,
        RESEARCH_START,
        RESEARCH_END,
        policy,
    )
    holdout_rows = _build_rows(
        prices,
        features,
        HOLDOUT_START,
        HOLDOUT_END,
        policy,
    )

    scenarios = {
        name: {
            "research": _stats(research_rows, multiplier),
            "holdout": _stats(holdout_rows, multiplier),
        }
        for name, multiplier in (
            ("base", 1.0),
            ("cost_1_5x", 1.5),
            ("cost_2x", 2.0),
        )
    }

    report = {
        "schema_version": 1,
        "trial_id": "EVENT-ALPHA-2026-09-24-001",
        "status": "COMPLETED",
        "research_only": True,
        "selection_used": False,
        "parameter_search_used": False,
        "data_scope": {
            "market_assets": list(ASSETS),
            "market_candles_per_asset": TARGET_COUNT,
            "market_manifest_fingerprint": manifest.get("manifest_fingerprint"),
            "adjusted_price_series_fingerprints": adjusted_price_fingerprints,
            "event_research_start": RESEARCH_START.isoformat(),
            "event_research_end": RESEARCH_END.isoformat(),
            "event_holdout_start": HOLDOUT_START.isoformat(),
            "event_holdout_end": HOLDOUT_END.isoformat(),
            "event_feature_start": event_feature_start.isoformat(),
            "fully_symbol_disjoint_validation_set": True,
        },
        "policy": {
            "risk_asset": policy.risk_asset,
            "defensive_asset_a": policy.defensive_asset_a,
            "defensive_asset_b": policy.defensive_asset_b,
            "weights": dict(policy.weights),
            "gross_exposure": 1.0,
            "net_exposure": 0.0,
            "activation": (
                "international_material_conflict_count > 0 AND "
                "high_confidence_international_count > 0 "
                "inside the prior-market-day-to-target-day event window"
            ),
        },
        "methodology": {
            "execution": "previous_market_close -> target_market_close",
            "cost_scenarios": ["base", "cost_1_5x", "cost_2x"],
            "holdout_used_for_selection": False,
            "strategy_variants": 1,
            "parameter_search": False,
        },
        "event_data_quality": {
            "event_rows_seen": event_parse_stats["rows_seen"],
            "event_rows_skipped": event_parse_stats["rows_skipped"],
            "event_row_skip_rate": (
                event_parse_stats["rows_skipped"] / event_parse_stats["rows_seen"]
                if event_parse_stats["rows_seen"] else 0.0
            ),
        },
        "scenarios": scenarios,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    report["report_fingerprint"] = _fp(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return report

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market-dir", required=True)
    parser.add_argument("--market-manifest", required=True)
    parser.add_argument("--event-raw-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run_validation(
        market_dir=Path(args.market_dir),
        market_manifest=Path(args.market_manifest),
        event_raw_dir=Path(args.event_raw_dir),
        output=Path(args.output),
    )
    print("EVENT_ALPHA_STATUS:", report["status"])
    print("EVENT_ALPHA_REPORT_FINGERPRINT:", report["report_fingerprint"])

if __name__ == "__main__":
    main()
