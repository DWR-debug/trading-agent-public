"""Fixed research-only volatility-regime diagnostic for Wide-Search Round 002.

No PnL/performance selection, no holdout access, no parameter search, no strategy authorization.
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
SHORT_WINDOW = 20
LONG_WINDOW = 60
SHOCK_RATIO = 1.5
FORWARD_WINDOW = 5
SUPPORT_THRESHOLD = 1.10
MIN_EVENTS = 50


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _annualized_vol(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(max(0.0, variance)) * math.sqrt(252.0)


def _summary(values: list[float]) -> dict:
    if not values:
        return {
            "count": 0,
            "mean_forward_to_baseline_vol_ratio": 0.0,
            "median_forward_to_baseline_vol_ratio": 0.0,
            "share_at_or_above_1_10": 0.0,
        }
    return {
        "count": len(values),
        "mean_forward_to_baseline_vol_ratio": sum(values) / len(values),
        "median_forward_to_baseline_vol_ratio": statistics.median(values),
        "share_at_or_above_1_10": sum(
            value >= SUPPORT_THRESHOLD for value in values
        ) / len(values),
    }


def _classify(events: list[float]) -> str:
    if len(events) < MIN_EVENTS:
        return "PRUNE_TOO_FEW_EVENTS"
    midpoint = len(events) // 2
    first = events[:midpoint]
    second = events[midpoint:]
    first_mean = sum(first) / len(first)
    second_mean = sum(second) / len(second)
    if first_mean >= SUPPORT_THRESHOLD and second_mean >= SUPPORT_THRESHOLD:
        return "DISCOVERY_SUPPORT_RISK_REGIME"
    return "PRUNE_NO_RISK_REGIME_SUPPORT"


def _load_common_calendar() -> dict[str, list]:
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
            bar
            for bar in bars
            if STUDY_START <= bar.timestamp.date() <= STUDY_END
        ]
        if len(bars) < TARGET_COMMON_CANDLES:
            raise RuntimeError(
                f"{symbol}: only {len(bars)} bars in fixed study window"
            )
        bars_by_symbol[symbol] = bars[-TARGET_COMMON_CANDLES:]

    common = set.intersection(
        *[{bar.timestamp for bar in bars} for bars in bars_by_symbol.values()]
    )
    if len(common) != TARGET_COMMON_CANDLES:
        raise RuntimeError(
            f"Common calendar is {len(common)}, expected {TARGET_COMMON_CANDLES}"
        )

    timestamps = sorted(common)
    aligned = {}
    for symbol, bars in bars_by_symbol.items():
        lookup = {bar.timestamp: bar for bar in bars}
        aligned[symbol] = [lookup[timestamp] for timestamp in timestamps]
    return aligned


def _probe_symbol(bars: list) -> list[dict]:
    closes = [bar.close for bar in bars]
    returns = [0.0] + [
        closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))
    ]
    events = []
    start = LONG_WINDOW
    end = RESEARCH_CANDLES - FORWARD_WINDOW

    for i in range(start, end):
        long_vol = _annualized_vol(returns[i - LONG_WINDOW:i])
        if long_vol <= 0.0:
            continue

        short_vol = _annualized_vol(returns[i - SHORT_WINDOW:i])
        ratio = short_vol / long_vol
        if ratio < SHOCK_RATIO:
            continue

        forward = _annualized_vol(
            returns[i + 1:i + 1 + FORWARD_WINDOW]
        )
        events.append(
            {
                "event_index": i,
                "state_ratio": ratio,
                "baseline_long_vol": long_vol,
                "forward_5d_vol": forward,
                "forward_to_baseline_ratio": (
                    forward / long_vol if long_vol > 0.0 else 0.0
                ),
            }
        )
    return events


def run(
    *,
    output_path: str | Path
    = "research/runs/wide_search/wide_search_round_002_volatility_regime.json",
) -> dict:
    if (
        settings.PAPER_ONLY is not True
        or settings.LIVE_TRADING_ENABLED is not False
        or settings.ORDERS_ENABLED is not False
    ):
        raise RuntimeError("Round 002 requires the paper-only safety configuration.")

    assets = _load_common_calendar()
    per_symbol = {
        symbol: _probe_symbol(bars) for symbol, bars in assets.items()
    }
    pooled_events = [
        event for events in per_symbol.values() for event in events
    ]
    pooled_events.sort(key=lambda event: event["event_index"])

    ratios = [
        event["forward_to_baseline_ratio"] for event in pooled_events
    ]
    midpoint = len(ratios) // 2
    first = ratios[:midpoint]
    second = ratios[midpoint:]

    result = {
        "schema_version": "1.0",
        "task_id": "WIDE-SEARCH-ROUND-002",
        "hypothesis_id": "H08",
        "recorded_at": date.today().isoformat(),
        "universe": UNIVERSE,
        "research_candles_used": RESEARCH_CANDLES,
        "holdout_candles_unused": TARGET_COMMON_CANDLES - RESEARCH_CANDLES,
        "fixed_rule": {
            "short_realized_vol_window": SHORT_WINDOW,
            "long_realized_vol_window": LONG_WINDOW,
            "shock_ratio_threshold": SHOCK_RATIO,
            "forward_realized_vol_window": FORWARD_WINDOW,
            "primary_support_threshold": SUPPORT_THRESHOLD,
            "minimum_events": MIN_EVENTS,
        },
        "pooled_research_only": {
            "classification": _classify(ratios),
            "overall": _summary(ratios),
            "first_research_half": _summary(first),
            "second_research_half": _summary(second),
        },
        "per_symbol": {
            symbol: {
                "event_count": len(events),
                "mean_forward_to_baseline_ratio": (
                    sum(
                        event["forward_to_baseline_ratio"] for event in events
                    ) / len(events)
                    if events
                    else 0.0
                ),
            }
            for symbol, events in per_symbol.items()
        },
        "governance": {
            "risk_regime_diagnostic": True,
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
    result["fingerprint"] = _fingerprint(result)

    path = Path(output_path)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "task_id": result["task_id"],
                "classification": result["pooled_research_only"]["classification"],
                "events": result["pooled_research_only"]["overall"]["count"],
                "fingerprint": result["fingerprint"],
            },
            sort_keys=True,
        )
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="research/runs/wide_search/"
        "wide_search_round_002_volatility_regime.json",
    )
    args = parser.parse_args()
    run(output_path=args.output)


if __name__ == "__main__":
    main()
