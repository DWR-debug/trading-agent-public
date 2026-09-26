"""Fixed-rule Q020 Treasury-auction performance runner.

Consumes a frozen, coverage-validated OHLCV snapshot and the already validated
Q019 Treasury signal contract. No parameter, asset, threshold, horizon, or
holdout selection is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from bisect import bisect_right
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from pathlib import Path
from typing import Any

from automation.candidate_validation_50_50_vol_budget import (
    _stats,
    _yahoo_adjclose,
)
from automation.literature_strategy_lab import load_bars
from automation.q019_treasury_auction_signal_contract import (
    STUDY_END,
    STUDY_START,
    _treasury_rows,
    _validate_treasury_contract,
)
from config import settings
from research.asset_universes import get_universe
from research.protocol import dataset_fingerprint

TRIAL_ID = "T-2026-09-26-046R1-PERFORMANCE"
UNIVERSE = "validation_2026_09_26_treasury_auction_performance_repair"
SYMBOLS = ("ACN","AMT","APD","TGT","CME","CTAS","GPC","LLY","MCO","NOC","ROST","SHW")
TARGET_CANDLES = 3500
RESEARCH_PERIODS = 2798
HOLDOUT_PERIODS = 700
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
ROUNDTRIP_COST = 2.0 * (FEE_RATE + SLIPPAGE_RATE)


def _fp(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _xnys_dates() -> list[date]:
    import exchange_calendars as xcals
    import pandas as pd
    sessions = xcals.get_calendar("XNYS").sessions_in_range(
        pd.Timestamp(STUDY_START.isoformat()),
        pd.Timestamp(STUDY_END.isoformat()),
    )
    dates = [stamp.date() for stamp in sessions]
    if len(dates) != 3704:
        raise RuntimeError(f"Unexpected XNYS session count: {len(dates)}")
    return dates


def _signal_events(rows: list[dict], common_dates: list[date]) -> tuple[list[dict], str]:
    valid = []
    seen = set()
    required = {"record_date","security_type","security_term","auction_date","cusip","bid_to_cover_ratio"}
    for row in rows:
        if required - set(row):
            continue
        if row["security_type"] != "Note" or row["security_term"] != "10-Year":
            continue
        key = (row["auction_date"], row["cusip"])
        if key in seen:
            continue
        seen.add(key)
        try:
            record = date.fromisoformat(row["record_date"])
            auction = date.fromisoformat(row["auction_date"])
            ratio = float(row["bid_to_cover_ratio"])
        except (TypeError, ValueError):
            continue
        if record < auction or not (STUDY_START <= record <= STUDY_END):
            continue
        if not math.isfinite(ratio) or ratio <= 0:
            continue
        valid.append((auction, row["cusip"], row["record_date"], row["auction_date"], ratio))
    valid.sort(key=lambda x: (x[0], x[1]))

    previous = None
    dates = sorted(common_dates)
    out = []
    for auction, cusip, record_text, auction_text, ratio in valid:
        signal = None if previous is None else (1 if ratio > previous else -1 if ratio < previous else 0)
        previous = ratio
        idx = bisect_right(dates, date.fromisoformat(record_text))
        next_day = dates[idx] if idx < len(dates) else None
        out.append({
            "auction_date": auction_text,
            "cusip": cusip,
            "record_date": record_text,
            "bid_to_cover_ratio": ratio,
            "signal": signal,
            "next_eligible_common_trading_date": next_day.isoformat() if next_day else None,
        })
    return out, _fp(out)


def _validate_signal_source(expected_fingerprint: str, common_dates: list[date]) -> tuple[list[dict], dict]:
    rows = _treasury_rows()
    contract = _validate_treasury_contract(rows, common_dates)
    if contract["status"] != "COVERAGE_VALIDATED":
        raise RuntimeError(f"Q019 source contract invalid: {contract['status']}")
    events, actual = _signal_events(rows, common_dates)
    if actual != expected_fingerprint or actual != contract["signals_fingerprint"]:
        raise RuntimeError(
            f"Q019 signal fingerprint mismatch: expected {expected_fingerprint}, actual {actual}, contract {contract['signals_fingerprint']}"
        )
    return events, contract


def _load_assets(data_dir: Path, manifest: dict) -> dict[str, tuple]:
    universe = get_universe(UNIVERSE)
    if tuple(manifest["symbols"]) != SYMBOLS or tuple(universe.symbols) != SYMBOLS:
        raise ValueError("Frozen Q020 universe mismatch")
    if manifest["status"].lower() != "coverage_passed":
        raise ValueError("Frozen Q020 coverage is not passed")
    expected = {item["symbol"]: item for item in manifest["data_snapshot"]["datasets"]}
    if set(expected) != set(SYMBOLS):
        raise ValueError("Frozen Q020 snapshot is incomplete")
    assets = {}
    for symbol in SYMBOLS:
        item = expected[symbol]
        bars = load_bars(data_dir / symbol / "1d.csv", expected_count=TARGET_CANDLES)
        if dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"{symbol}: frozen dataset fingerprint mismatch")
        assets[symbol] = bars
    timestamps = [bar.timestamp for bar in assets[SYMBOLS[0]]]
    if any([bar.timestamp for bar in assets[s]] != timestamps for s in SYMBOLS[1:]):
        raise ValueError("Frozen asset timestamps are not aligned")
    return assets


def _positions(events: list[dict]) -> dict[date, int]:
    totals: dict[date, int] = {}
    for event in events:
        signal = event["signal"]
        mapped = event["next_eligible_common_trading_date"]
        if signal in (-1, 1) and mapped:
            day = date.fromisoformat(mapped)
            totals[day] = totals.get(day, 0) + signal
    return {day: (1 if value > 0 else -1 if value < 0 else 0) for day, value in totals.items()}


def _simulate(assets: dict[str, tuple], positions: dict[date, int], multiplier: float) -> tuple[list[dict], dict[str, float]]:
    timestamps = [bar.timestamp for bar in assets[SYMBOLS[0]]]
    by_date = {ts.date(): {symbol: assets[symbol][i] for symbol in SYMBOLS} for i, ts in enumerate(timestamps)}
    cost = ROUNDTRIP_COST * multiplier
    daily = []
    for ts in timestamps[2:]:
        day = ts.date()
        signal = positions.get(day, 0)
        if signal == 0:
            net = 0.0
            turnover = 0.0
        else:
            bars = by_date[day]
            gross = signal * sum((bars[s].close / bars[s].open) - 1.0 for s in SYMBOLS) / len(SYMBOLS)
            net = gross - cost
            turnover = 2.0
        daily.append({"timestamp": ts.isoformat(), "net_return": net, "gross_return": net + (cost if signal else 0.0), "signal": signal, "turnover": turnover, "scale": 1.0})
    return daily, {"trade_days": float(sum(row["signal"] != 0 for row in daily)), "turnover": float(sum(row["turnover"] for row in daily))}


def _rolling(rows: list[dict]) -> dict:
    width = RESEARCH_PERIODS // 5
    windows = []
    start = 0
    for idx in range(5):
        end = RESEARCH_PERIODS if idx == 4 else start + width
        windows.append({"window_index": idx + 1, **_stats(rows, start, end)})
        start = end
    return {
        "windows": windows,
        "window_count": 5,
        "profitable_window_ratio": sum(w["period_return"] > 0 for w in windows) / 5.0,
        "overall_profit_factor": _stats(rows, 0, RESEARCH_PERIODS)["profit_factor"],
        "average_drawdown_percent": sum(w["max_drawdown_percent"] for w in windows) / 5.0,
    }


def _adjusted_holdout_return(
    daily: list[dict], assets: dict[str, tuple], adjusted: dict[str, dict[datetime, float]], positions: dict[date, int], multiplier: float
) -> dict:
    timestamps = [bar.timestamp for bar in assets[SYMBOLS[0]]]
    by_date = {ts.date(): {symbol: assets[symbol][i] for symbol in SYMBOLS} for i, ts in enumerate(timestamps)}
    prev = {timestamps[i].date(): timestamps[i-1].date() for i in range(1, len(timestamps))}
    cost = ROUNDTRIP_COST * multiplier
    returns = []
    for row in daily:
        day = date.fromisoformat(row["timestamp"][:10])
        signal = positions.get(day, 0)
        if not signal:
            returns.append(0.0)
            continue
        pday = prev[day]
        correction = 0.0
        for symbol in SYMBOLS:
            current = by_date[day][symbol].timestamp
            previous = by_date[pday][symbol].timestamp
            adj_return = adjusted[symbol][current] / adjusted[symbol][previous] - 1.0
            close_return = by_date[day][symbol].close / by_date[pday][symbol].close - 1.0
            correction += adj_return - close_return
        returns.append(row["net_return"] + signal * correction / len(SYMBOLS))
    holdout = returns[RESEARCH_PERIODS:RESEARCH_PERIODS + HOLDOUT_PERIODS]
    return _stats(
        [{"net_return": value, "scale": 1.0} for value in holdout],
        0,
        len(holdout),
    )


def _gates(scenarios: dict) -> dict:
    base = scenarios["base"]
    research = base["research"]
    holdout = base["holdout"]
    rolling = base["rolling"]
    stress15 = scenarios["stress_1_5x"]["holdout"]
    stress2 = scenarios["stress_2x"]["holdout"]
    total = base["total_return_sensitivity_holdout"]
    pf = lambda value: float("inf") if value == "inf" else float(value)
    oos_is = holdout["period_return"] / research["period_return"] if research["period_return"] > 0 else 0.0
    checks = {
        "research_return_positive": research["period_return"] > 0,
        "research_max_drawdown_lte_10pct": research["max_drawdown_percent"] <= 10,
        "research_profit_factor_gte_1_1": pf(research["profit_factor"]) >= 1.1,
        "rolling_profit_factor_gte_1_1": pf(rolling["overall_profit_factor"]) >= 1.1,
        "rolling_profitable_window_ratio_gte_0_5": rolling["profitable_window_ratio"] >= 0.5,
        "rolling_average_drawdown_lte_10pct": rolling["average_drawdown_percent"] <= 10,
        "oos_to_is_return_ratio_gte_0_25": oos_is >= 0.25,
        "holdout_return_positive": holdout["period_return"] > 0,
        "holdout_profit_factor_gte_1_1": pf(holdout["profit_factor"]) >= 1.1,
        "holdout_max_drawdown_lte_10pct": holdout["max_drawdown_percent"] <= 10,
        "stress_1_5x_holdout_nonnegative": stress15["period_return"] >= 0,
        "stress_2x_holdout_nonnegative": stress2["period_return"] >= 0,
        "total_return_sensitivity_holdout_nonnegative": total["period_return"] >= 0,
    }
    return {"absolute": checks, "all_absolute_passed": all(checks.values()), "oos_to_is_return_ratio": oos_is}


def run(manifest_path: Path, data_dir: Path, signal_contract_path: Path, authorization_path: Path, output_path: Path) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False or settings.ORDERS_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated")
    manifest = _load_json(manifest_path)
    signal_contract = _load_json(signal_contract_path)
    auth = _load_json(authorization_path)
    if auth.get("trial_id") != TRIAL_ID or auth.get("performance_execution_authorized") is not True:
        raise RuntimeError("Q020 performance authorization missing")
    if auth.get("coverage_artifact_id") != 10905489440 or auth.get("coverage_workflow_run_id") != 36240853419:
        raise RuntimeError("Authorization is not bound to the validated repair artifact")
    if auth.get("snapshot_fingerprint") != manifest.get("snapshot_fingerprint"):
        raise RuntimeError("Snapshot fingerprint mismatch")
    if auth.get("source_contract_fingerprint") != signal_contract.get("fingerprint"):
        raise RuntimeError("Source contract fingerprint mismatch")
    if auth.get("signal_events_fingerprint") != signal_contract["contract"]["signals_fingerprint"]:
        raise RuntimeError("Signal events fingerprint mismatch")
    if auth.get("execution_model") != "open_to_close_same_session":
        raise RuntimeError("Execution model mismatch")

    assets = _load_assets(data_dir, manifest)
    common_dates = _xnys_dates()
    events, source_contract = _validate_signal_source(signal_contract["contract"]["signals_fingerprint"], common_dates)
    positions = _positions(events)
    adjusted = {}
    start = assets[SYMBOLS[0]][0].timestamp
    end = assets[SYMBOLS[0]][-1].timestamp
    with ThreadPoolExecutor(max_workers=len(SYMBOLS)) as pool:
        futures = {pool.submit(_yahoo_adjclose, symbol, start, end): symbol for symbol in SYMBOLS}
        for future in as_completed(futures):
            adjusted[futures[future]] = future.result()

    scenarios = {}
    for name, multiplier in (("base", 1.0), ("stress_1_5x", 1.5), ("stress_2x", 2.0)):
        daily, execution = _simulate(assets, positions, multiplier)
        research = _stats(daily, 0, RESEARCH_PERIODS)
        holdout = _stats(daily, RESEARCH_PERIODS, RESEARCH_PERIODS + HOLDOUT_PERIODS)
        total_sens = _adjusted_holdout_return(daily, assets, adjusted, positions, multiplier)
        scenarios[name] = {
            "research": research,
            "holdout": holdout,
            "rolling": _rolling(daily),
            "total_return_sensitivity_holdout": total_sens,
            "execution": execution,
        }

    result = {
        "schema_version": "1.0",
        "trial_id": TRIAL_ID,
        "status": "ALL_GATES_PASSED" if _gates(scenarios)["all_absolute_passed"] else "NO_PROMOTION_EVIDENCE",
        "research_family": "official_event_alpha_performance",
        "signal_event_count": sum(1 for event in events if event["signal"] in (-1, 1)),
        "active_signal_sessions": sum(1 for value in positions.values() if value),
        "signal_source_fingerprint": source_contract["signals_fingerprint"],
        "snapshot_fingerprint": manifest["snapshot_fingerprint"],
        "evaluation_geometry": {"frozen_candles": 3500, "evaluation_return_periods": 3498, "excluded_initial_return_periods": 1, "research_periods": 2798, "holdout_periods": 700},
        "scenarios": scenarios,
        "gates": _gates(scenarios),
        "selection": {"parameter_search": False, "threshold_search": False, "asset_search": False, "horizon_search": False, "variant_search": False, "holdout_used_for_selection": False},
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    result["result_fingerprint"] = _fp(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"trial_id": TRIAL_ID, "status": result["status"], "result_fingerprint": result["result_fingerprint"]}, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--signal-contract", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.manifest, args.data_dir, args.signal_contract, args.authorization, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
