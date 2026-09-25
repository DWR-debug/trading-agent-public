"""Cheap, deterministic research-only signal probes for the wide-search lane.

The probe uses only the fixed research segment of a common daily calendar. It never
reads the final 700-bar holdout and never authorizes a formal trial.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from datetime import date
from pathlib import Path

from config import settings
from data.yahoo_loader import load_yahoo_history
from research.asset_universes import get_universe

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = "wide_search_probe_2026_09_25"
STUDY_START = date(2011, 1, 1)
STUDY_END = date(2025, 9, 24)
TARGET_COMMON_CANDLES = 3500
RESEARCH_CANDLES = 2798
REQUESTED_CANDLES = 4200


def _sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def _rolling_median(values: list[float], index: int, width: int) -> float:
    if index < width:
        return 0.0
    return _median(values[index - width:index])


def _rolling_mean(values: list[float], index: int, width: int) -> float:
    if index < width:
        return 0.0
    return sum(values[index - width:index]) / width


def _annualized_vol(values: list[float], index: int, width: int) -> float:
    if index < width:
        return 0.0
    sample = values[index - width:index]
    mean = sum(sample) / width
    variance = sum((x - mean) ** 2 for x in sample) / width
    return math.sqrt(max(0.0, variance)) * math.sqrt(252.0)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _sign_consistency(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(1 for value in values if value > 0.0) / len(values)


def _event_summary(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "mean_return": 0.0, "hit_rate": 0.0, "median_return": 0.0}
    return {
        "count": len(values),
        "mean_return": _mean(values),
        "hit_rate": sum(1 for value in values if value > 0.0) / len(values),
        "median_return": _median(values),
    }


def _classify(events: list[float]) -> str:
    if len(events) < 50:
        return "PRUNE_TOO_FEW_EVENTS"
    midpoint = len(events) // 2
    first = _mean(events[:midpoint])
    second = _mean(events[midpoint:])
    overall = _mean(events)
    same_sign = (first > 0 and second > 0) or (first < 0 and second < 0)
    if same_sign and abs(first) >= 0.001 and abs(second) >= 0.001 and abs(overall) >= 0.001:
        return "DISCOVERY_SUPPORT"
    return "PRUNE_NO_RESEARCH_SUPPORT"


def _load_common_calendar() -> dict[str, list[dict]]:
    universe = get_universe(UNIVERSE)
    bars_by_symbol: dict[str, list] = {}
    for symbol in universe.symbols:
        bars = load_yahoo_history(
            symbol,
            "1d",
            REQUESTED_CANDLES,
            allow_partial=True,
            skip_invalid_ohlc=True,
        )
        bars = [
            bar for bar in bars
            if STUDY_START <= bar.timestamp.date() <= STUDY_END
        ]
        if len(bars) < TARGET_COMMON_CANDLES:
            raise RuntimeError(f"{symbol}: only {len(bars)} candles in fixed study window")
        bars_by_symbol[symbol] = bars[-TARGET_COMMON_CANDLES:]

    common = set.intersection(*[{bar.timestamp for bar in bars} for bars in bars_by_symbol.values()])
    if len(common) != TARGET_COMMON_CANDLES:
        raise RuntimeError(f"Common calendar is {len(common)}, expected {TARGET_COMMON_CANDLES}")

    aligned = {}
    timestamps = sorted(common)
    for symbol, bars in bars_by_symbol.items():
        lookup = {bar.timestamp: bar for bar in bars}
        aligned[symbol] = [lookup[timestamp] for timestamp in timestamps]
    return aligned


def _probe_assets(assets: dict[str, list]) -> dict[str, list[float]]:
    closes = {s: [bar.close for bar in bars] for s, bars in assets.items()}
    volumes = {s: [bar.volume for bar in bars] for s, bars in assets.items()}
    ranges = {
        s: [max(bar.high - bar.low, 0.0) for bar in bars]
        for s, bars in assets.items()
    }
    returns = {
        s: [0.0] + [closes[s][i] / closes[s][i - 1] - 1.0 for i in range(1, TARGET_COMMON_CANDLES)]
        for s in assets
    }

    probes = {
        "abnormal_turnover_liquidity_shock": [],
        "cross_asset_lead_lag": [],
        "gap_reversal": [],
        "volume_price_imbalance": [],
    }

    symbols = tuple(assets)
    start = 60
    end = RESEARCH_CANDLES - 5

    for i in range(start, end):
        for symbol in symbols:
            # H03: fixed volume/range shock; forward return is the next research-bar close return.
            volume_ratio = volumes[symbol][i] / max(_rolling_median(volumes[symbol], i, 20), 1e-12)
            range_ratio = ranges[symbol][i] / max(_rolling_median(ranges[symbol], i, 20), 1e-12)
            if volume_ratio >= 2.5 and range_ratio >= 1.5:
                probes["abnormal_turnover_liquidity_shock"].append(returns[symbol][i + 1])

            # H09: fixed 2% overnight gap, testing reversal on the next eligible bar.
            gap = assets[symbol][i].open / max(closes[symbol][i - 1], 1e-12) - 1.0
            if abs(gap) >= 0.02:
                probes["gap_reversal"].append(-math.copysign(returns[symbol][i + 1], gap))

            # H10: fixed close-location/volume interaction threshold.
            bar_range = max(assets[symbol][i].high - assets[symbol][i].low, 1e-12)
            clv = ((assets[symbol][i].close - assets[symbol][i].low) - (assets[symbol][i].high - assets[symbol][i].close)) / bar_range
            imbalance = clv * volume_ratio
            if abs(imbalance) >= 1.5:
                probes["volume_price_imbalance"].append(math.copysign(returns[symbol][i + 1], imbalance))

        # H07: fixed equal-weight cross-asset 21-day lead signal, excluding the target.
        peer_values = {
            s: (closes[s][i] / closes[s][i - 21] - 1.0)
            for s in symbols
        }
        for target in symbols:
            peers = [peer_values[s] for s in symbols if s != target]
            signal = _mean(peers)
            if abs(signal) >= 0.015:
                probes["cross_asset_lead_lag"].append(math.copysign(returns[target][i + 1], signal))

    return probes


def run(*, output_path: str | Path = "research/runs/wide_search/wide_search_probe.json") -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False or settings.ORDERS_ENABLED is not False:
        raise RuntimeError("Wide-search probe requires the paper-only safety configuration.")

    assets = _load_common_calendar()
    probes = _probe_assets(assets)
    results = {}
    for family, events in probes.items():
        midpoint = len(events) // 2
        results[family] = {
            "classification": _classify(events),
            "research_observations_only": True,
            "holdout_used": False,
            "selection_used": False,
            "performance_trial_authorized": False,
            "overall": _event_summary(events),
            "first_research_half": _event_summary(events[:midpoint]),
            "second_research_half": _event_summary(events[midpoint:]),
        }

    report = {
        "schema_version": "1.0",
        "task_id": "WIDE-SEARCH-PROBE-001",
        "recorded_at": date.today().isoformat(),
        "universe": UNIVERSE,
        "research_candles_used": RESEARCH_CANDLES,
        "holdout_candles_unused": TARGET_COMMON_CANDLES - RESEARCH_CANDLES,
        "fixed_rules": {
            "turnover_volume_ratio": 2.5,
            "turnover_range_ratio": 1.5,
            "gap_threshold": 0.02,
            "lead_lag_lookback": 21,
            "lead_lag_threshold": 0.015,
            "volume_price_imbalance": 1.5,
            "minimum_events": 50,
            "minimum_half_mean_abs_return": 0.001,
        },
        "results": results,
        "governance": {
            "performance_evaluation": False,
            "holdout_evaluation": False,
            "holdout_used_for_selection": False,
            "selection_used": False,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    report["fingerprint"] = _sha256(report)

    path = Path(output_path)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_id": report["task_id"],
        "classifications": {key: value["classification"] for key, value in results.items()},
        "fingerprint": report["fingerprint"],
    }, sort_keys=True))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="research/runs/wide_search/wide_search_probe.json")
    args = parser.parse_args()
    run(output_path=args.output)


if __name__ == "__main__":
    main()
