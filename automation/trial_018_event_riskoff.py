"""Trial 018: fixed market-neutral event risk-off overlay with PIT timing."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Iterable

from config import settings
from data.gdelt_events import GDELTEvent, download_daily_export, parse_event_zip
from research.event_intelligence import aggregate_daily_events, conflict_flag

ASSETS = ("SPY", "TLT", "GLD")
RISK_OFF_WEIGHTS = {"SPY": -0.50, "TLT": 0.25, "GLD": 0.25}
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
RESEARCH_END = date(2025, 3, 31)
HOLDOUT_START = date(2025, 4, 1)
HOLDOUT_END = date(2025, 6, 30)

@dataclass(frozen=True)
class OHLC:
    open: float
    close: float

def _yahoo_daily_ohlc(symbol: str, start: date, end: date) -> dict[date, OHLC]:
    import urllib.parse
    import urllib.request
    params = {
        "period1": int(datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).timestamp()),
        "period2": int(datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).timestamp()),
        "interval": "1d", "events": "div,splits",
    }
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol, safe='')}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "trading-agent-research/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))["chart"]["result"][0]
    opens = result["indicators"]["quote"][0]["open"]
    closes = result["indicators"]["quote"][0]["close"]
    return {
        datetime.fromtimestamp(ts, tz=timezone.utc).date(): OHLC(float(o), float(c))
        for ts, o, c in zip(result["timestamp"], opens, closes)
        if o is not None and c is not None
    }

def _event_windows(events: Iterable[GDELTEvent], market_days: list[date]) -> dict[date, bool]:
    features = {f.event_date: f for f in aggregate_daily_events(list(events), international_only=True, high_confidence_only=True)}
    result: dict[date, bool] = {}
    for index in range(1, len(market_days)):
        previous_day = market_days[index - 1]
        target_day = market_days[index]
        selected = [f for day, f in features.items() if previous_day < day < target_day]
        result[target_day] = any(conflict_flag(f) for f in selected)
    return result

def _event_signal(event_flag: bool) -> dict[str, float]:
    return dict(RISK_OFF_WEIGHTS) if event_flag else {symbol: 0.0 for symbol in ASSETS}

def _simulate(prices: dict[str, dict[date, OHLC]], signals: dict[date, bool], start: date, end: date, cost_multiplier: float = 1.0, delay_days: int = 0) -> dict:
    market_days = sorted(set.intersection(*[{d for d in values if start - timedelta(days=7) <= d <= end + timedelta(days=7)} for values in prices.values()]))
    targets = [d for d in market_days if start <= d <= end]
    rows = []
    previous = {symbol: 0.0 for symbol in ASSETS}
    cost_rate = (FEE_RATE + SLIPPAGE_RATE) * cost_multiplier
    for index, target in enumerate(targets[:-1]):
        effective_index = index - delay_days
        flag = signals.get(target, False) if effective_index >= 0 else False
        if delay_days > 0 and effective_index >= 0:
            source_day = targets[effective_index]
            flag = signals.get(source_day, False)
        weights = _event_signal(flag)
        next_day = targets[index + 1]
        gross = sum(weights[symbol] * (prices[symbol][next_day].open / prices[symbol][target].open - 1.0) for symbol in ASSETS)
        turnover = sum(abs(weights[symbol] - previous[symbol]) for symbol in ASSETS)
        net = gross - cost_rate * turnover
        rows.append({"target_market_day": target.isoformat(), "signal": flag, "gross_return": gross, "turnover": turnover, "net_return": net})
        previous = weights
    equity = peak = 1.0
    max_dd = 0.0
    gross_profit = gross_loss = 0.0
    active = 0
    for row in rows:
        equity *= 1.0 + row["net_return"]
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak if equity > 0 else 1.0)
        if row["signal"]: active += 1
        if row["net_return"] > 0: gross_profit += row["net_return"]
        elif row["net_return"] < 0: gross_loss -= row["net_return"]
    return {
        "observation_count": len(rows),
        "active_signal_days": active,
        "cumulative_return": equity - 1.0,
        "max_drawdown_percent": 100.0 * max_dd,
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else ("inf" if gross_profit > 0 else 0.0),
        "mean_daily_return": mean([r["net_return"] for r in rows]) if rows else None,
        "total_turnover": sum(r["turnover"] for r in rows),
        "rows": rows,
    }

def run_trial(start: date, end: date, *, event_loader=None, market_loader=None, output_path: str | Path = "research/trial_018_event_riskoff/report.json") -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")
    if start > RESEARCH_END or end < HOLDOUT_START or end > HOLDOUT_END:
        raise ValueError("Trial 018 requires the fixed 2025 Q1 research / Q2 holdout range.")
    if event_loader is None:
        raw = Path("research/trial_018_event_riskoff/raw")
        def event_loader(day):
            path = raw / f"{day.isoformat()}.zip"
            if not path.exists():
                download_daily_export(datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc), path)
            return parse_event_zip(path, strict=False)
    if market_loader is None:
        market_loader = _yahoo_daily_ohlc
    events = []
    day = start
    while day <= end:
        events.extend(event_loader(day))
        day += timedelta(days=1)
    prices = {symbol: market_loader(symbol, start - timedelta(days=7), end + timedelta(days=10)) for symbol in ASSETS}
    market_days = sorted(set.intersection(*[set(values) for values in prices.values()]))
    signals = _event_windows(events, market_days)
    research = _simulate(prices, signals, start, RESEARCH_END, 1.0, 0)
    holdout = _simulate(prices, signals, HOLDOUT_START, HOLDOUT_END, 1.0, 0)
    stress2 = _simulate(prices, signals, HOLDOUT_START, HOLDOUT_END, 2.0, 0)
    delayed = _simulate(prices, signals, HOLDOUT_START, HOLDOUT_END, 1.0, 1)
    report = {
        "schema_version": 1, "trial_id": "018", "name": "fixed_event_riskoff_overlay",
        "status": "COMPLETED", "research_only": True, "selection_used": False, "parameter_search_used": False,
        "fixed_policy": {"weights": RISK_OFF_WEIGHTS, "gross_exposure": 1.0, "net_exposure": 0.0, "entry": "target_market_open", "exit": "next_market_open"},
        "fixed_costs": {"fee_rate": FEE_RATE, "slippage_rate": SLIPPAGE_RATE},
        "splits": {"research": [start.isoformat(), RESEARCH_END.isoformat()], "holdout": [HOLDOUT_START.isoformat(), HOLDOUT_END.isoformat()]},
        "point_in_time_contract": {"event_window": "previous_market_day < event_date < target_market_day", "signal_available_before_target_open": True, "return_model": "target_open -> next_market_open", "same_day_market_close_not_used_for_signal": True},
        "scenarios": {"research_base": research, "holdout_base": holdout, "holdout_2x_cost": stress2, "holdout_1_market_day_delay": delayed},
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False},
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
    }
    report["summary"] = {k: {m: v[m] for m in ("cumulative_return", "max_drawdown_percent", "profit_factor", "active_signal_days", "total_turnover") if m in v} for k, v in report["scenarios"].items()}
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    return report

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--end", default="2025-06-30")
    args = parser.parse_args()
    report = run_trial(date.fromisoformat(args.start), date.fromisoformat(args.end))
    print("TRIAL_018_STATUS:", report["status"])
    print("TRIAL_018_RESEARCH:", json.dumps(report["summary"]["research_base"], sort_keys=True))
    print("TRIAL_018_HOLDOUT:", json.dumps(report["summary"]["holdout_base"], sort_keys=True))
    print("TRIAL_018_STRESS2:", json.dumps(report["summary"]["holdout_2x_cost"], sort_keys=True))
    print("TRIAL_018_DELAY1:", json.dumps(report["summary"]["holdout_1_market_day_delay"], sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())