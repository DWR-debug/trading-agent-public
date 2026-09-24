"""Exploratory observer for current/updated market data.

Not a trading strategy. Reads completed daily Yahoo bars, computes fixed diagnostics,
and writes a fingerprinted observation report. No orders and no holdout selection.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from data.yahoo_loader import load_yahoo_history
from research.asset_universes import get_universe


def _mean(values: Iterable[float]) -> float:
    values = tuple(values)
    return sum(values) / len(values) if values else float("nan")


def _std(values: Iterable[float]) -> float:
    values = tuple(values)
    if len(values) < 2:
        return float("nan")
    mean = _mean(values)
    return math.sqrt(sum((x - mean) ** 2 for x in values) / (len(values) - 1))


def _returns(closes: list[float]) -> list[float]:
    return [
        (closes[index] / closes[index - 1]) - 1.0
        for index in range(1, len(closes))
        if closes[index - 1] > 0
    ]


def _corr(left: list[float], right: list[float]) -> float:
    n = min(len(left), len(right))
    if n < 3:
        return float("nan")
    left = left[-n:]
    right = right[-n:]
    ml, mr = _mean(left), _mean(right)
    dl = math.sqrt(sum((x - ml) ** 2 for x in left))
    dr = math.sqrt(sum((x - mr) ** 2 for x in right))
    if dl == 0 or dr == 0:
        return float("nan")
    correlation = sum((a - ml) * (b - mr) for a, b in zip(left, right)) / (dl * dr)
    # Floating-point arithmetic can turn exact +/-1 correlations into values
    # such as 0.9999999999999998; clamp numerically saturated results.
    if abs(correlation - 1.0) < 1e-12:
        return 1.0
    if abs(correlation + 1.0) < 1e-12:
        return -1.0
    return correlation


def _lagged_corr(target: list[float], peer: list[float], lag: int) -> float:
    if lag < 1 or len(target) <= lag or len(peer) <= lag:
        return float("nan")
    n = min(len(target), len(peer))
    target = target[-n:]
    peer = peer[-n:]
    return _corr(target[lag:], peer[:-lag])


def _clean(value: float) -> float | None:
    return None if not math.isfinite(value) else round(value, 8)


def observe_universe(
    universe: str,
    *,
    total: int | None = None,
    output: str | Path = "research/observations/latest_market_observation.json",
) -> dict:
    spec = get_universe(universe)
    requested = total or min(spec.target_count, 1000)
    loaded: dict[str, list] = {}
    errors: dict[str, str] = {}

    for symbol in spec.symbols:
        try:
            loaded[symbol] = load_yahoo_history(
                symbol,
                spec.interval,
                requested,
                allow_partial=True,
                skip_invalid_ohlc=True,
            )
        except ValueError as exc:
            errors[symbol] = str(exc)

    if not loaded:
        raise RuntimeError("Keine beobachtbaren Daten für " + universe + ".")

    timestamp_sets = [
        set(c.timestamp for c in candles) for candles in loaded.values()
    ]
    common = set.intersection(*timestamp_sets)
    common_sorted = sorted(common)

    observations: dict[str, dict] = {}
    return_series: dict[str, list[float]] = {}

    for symbol, candles in loaded.items():
        by_ts = {c.timestamp: c for c in candles}
        aligned = [by_ts[ts] for ts in common_sorted if ts in by_ts]
        closes = [c.close for c in aligned]
        returns = _returns(closes)
        return_series[symbol] = returns
        observations[symbol] = {
            "last_closed_timestamp": (
                aligned[-1].timestamp.isoformat() if aligned else None
            ),
            "last_close": _clean(closes[-1]) if closes else None,
            "return_1": _clean(returns[-1]) if returns else None,
            "annualized_vol_21": (
                _clean(_std(returns[-21:]) * math.sqrt(252))
                if len(returns) >= 21 else None
            ),
            "trend_return_252": (
                _clean((closes[-1] / closes[-253]) - 1.0)
                if len(closes) >= 253 else None
            ),
            "common_candles": len(aligned),
        }

    pairwise = []
    symbols = tuple(sorted(return_series))
    for index, left in enumerate(symbols):
        for right in symbols[index + 1:]:
            for lag in (1, 5, 21):
                pairwise.append({
                    "left": left,
                    "right": right,
                    "lag_sessions": lag,
                    "correlation": _clean(
                        _lagged_corr(
                            return_series[left],
                            return_series[right],
                            lag,
                        )
                    ),
                })

    discovery = [
        item
        for item in pairwise
        if item["correlation"] is not None
    ]
    discovery.sort(
        key=lambda item: (
            -abs(item["correlation"]),
            item["left"],
            item["right"],
            item["lag_sessions"],
        )
    )
    hypothesis_candidates = [
        {
            **item,
            "classification": "DISCOVERY_ONLY",
            "requires_preregistration": True,
            "holdout_used": False,
        }
        for item in discovery[:10]
    ]

    payload = {
        "schema_version": "1.1",
        "status": "OBSERVATION_ONLY",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "universe": universe,
        "interval": spec.interval,
        "requested_candles": requested,
        "loaded_symbols": symbols,
        "errors": errors,
        "common_calendar_count": len(common_sorted),
        "observations": observations,
        "pairwise_fixed_lag_correlations": pairwise,
        "hypothesis_candidates": hypothesis_candidates,
        "selection_used": False,
        "holdout_used": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    payload["observation_fingerprint"] = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False)
        + "\\n",
        encoding="utf-8",
    )
    return payload
