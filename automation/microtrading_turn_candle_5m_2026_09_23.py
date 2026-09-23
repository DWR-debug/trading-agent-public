"""Paper-only 5-minute turn-of-the-candle research control.

Tests a fixed calendar-time effect inspired by Shanaev, Vasenin, and Stepanov:
trade only candles starting at UTC minute 00, 15, 30, or 45.

This is deliberately different from the prior bar-direction family:
the signal is determined by the UTC clock, not prior returns.

Four previously unused symbols are tested with fixed Long and Short directions
and fixed 1x/2x/3x exposure. No optimization, no selection, no production use.
Short remains a price-return proxy; funding, borrow, liquidation, spread,
and latency are not modeled.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import timezone
from pathlib import Path
from typing import Any

from backtesting.models import Candle
from config import settings
from data.binance_loader import load_binance_history
from data.market_store import MarketDataStore
from research.data_quality import validate_research_dataset
from research.protocol import dataset_fingerprint

SYMBOLS = ("AAVEUSDT", "XLMUSDT", "ALGOUSDT", "FILUSDT")
PREVIOUS_MICRO_SYMBOLS = {
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "DOGEUSDT", "LTCUSDT", "LINKUSDT", "AVAXUSDT", "DOTUSDT", "ATOMUSDT",
    "UNIUSDT", "NEARUSDT",
}
INTERVAL = "5m"
TARGET_COUNT = 100_000
RESEARCH_RATIO = 0.80
TURN_MINUTES = (0, 15, 30, 45)
EXPOSURE_LEVELS = (1.0, 2.0, 3.0)
COST_RATE = 0.0015
COST_MULTIPLIERS = (0.0, 0.25, 0.5, 1.0, 2.0, 4.0)
BARS_PER_DAY = 288
ANNUALIZATION = math.sqrt(365.0 * BARS_PER_DAY)


def _canon(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _is_turn_of_candle(candle: Candle) -> bool:
    timestamp = candle.timestamp.astimezone(timezone.utc)
    return (
        timestamp.second == 0
        and timestamp.microsecond == 0
        and timestamp.minute in TURN_MINUTES
    )


def _stats(rows: list[dict[str, Any]], start: int, end: int) -> dict[str, Any]:
    seg = rows[start:end]
    if not seg:
        return {"bar_count": 0}

    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    gross_equity = 1.0
    gross_peak = 1.0
    gross_max_dd = 0.0
    net_profit = net_loss = 0.0
    gross_profit = gross_loss = 0.0
    values: list[float] = []
    gross_values: list[float] = []
    trade_returns: list[float] = []
    gross_trade_returns: list[float] = []
    turnover = 0.0
    turn_bars = 0
    ruin_bar = None

    for offset, row in enumerate(seg):
        net_value = float(row["net_return"])
        gross_value = float(row["gross_return"])
        applied_net = max(-1.0, net_value)
        applied_gross = max(-1.0, gross_value)

        equity = equity * (1.0 + applied_net) if equity > 0.0 else 0.0
        gross_equity *= 1.0 + applied_gross

        peak = max(peak, equity)
        gross_peak = max(gross_peak, gross_equity)
        max_dd = max(
            max_dd,
            1.0 - equity / peak if equity > 0.0 else 1.0,
        )
        gross_max_dd = max(
            gross_max_dd,
            1.0 - gross_equity / gross_peak
            if gross_equity > 0.0
            else 1.0,
        )

        values.append(applied_net)
        gross_values.append(gross_value)
        net_profit += max(applied_net, 0.0)
        net_loss += max(-applied_net, 0.0)
        gross_profit += max(gross_value, 0.0)
        gross_loss += max(-gross_value, 0.0)

        if bool(row["is_turn"]):
            turn_bars += 1
            turnover += float(row["turnover"])
            trade_returns.append(applied_net)
            gross_trade_returns.append(gross_value)

        if ruin_bar is None and equity <= 0.0:
            ruin_bar = offset

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    vol = math.sqrt(variance) * ANNUALIZATION
    sharpe_like = mean * ANNUALIZATION / vol if vol > 0.0 else 0.0

    gross_mean = sum(gross_values) / len(gross_values)
    gross_variance = sum(
        (x - gross_mean) ** 2 for x in gross_values
    ) / len(gross_values)
    gross_vol = math.sqrt(gross_variance) * ANNUALIZATION
    gross_sharpe_like = (
        gross_mean * ANNUALIZATION / gross_vol
        if gross_vol > 0.0
        else 0.0
    )

    trade_mean = sum(trade_returns) / len(trade_returns) if trade_returns else 0.0
    trade_variance = (
        sum((x - trade_mean) ** 2 for x in trade_returns) / len(trade_returns)
        if trade_returns
        else 0.0
    )
    trade_std = math.sqrt(trade_variance)
    trade_t_stat = (
        trade_mean / (trade_std / math.sqrt(len(trade_returns)))
        if trade_std > 0.0 and len(trade_returns) > 1
        else 0.0
    )
    gross_trade_mean = (
        sum(gross_trade_returns) / len(gross_trade_returns)
        if gross_trade_returns
        else 0.0
    )

    return {
        "bar_count": len(seg),
        "turn_bar_count": turn_bars,
        "period_return": equity - 1.0,
        "gross_period_return": gross_equity - 1.0,
        "cost_drag_period_return": (
            gross_equity - equity
        ),
        "max_drawdown_percent": max_dd * 100.0,
        "gross_max_drawdown_percent": gross_max_dd * 100.0,
        "profit_factor": (
            net_profit / net_loss
            if net_loss > 0.0
            else ("inf" if net_profit > 0.0 else 0.0)
        ),
        "gross_profit_factor": (
            gross_profit / gross_loss
            if gross_loss > 0.0
            else ("inf" if gross_profit > 0.0 else 0.0)
        ),
        "mean_bar_return": mean,
        "gross_mean_bar_return": gross_mean,
        "annualized_volatility": vol,
        "gross_annualized_volatility": gross_vol,
        "sharpe_like": sharpe_like,
        "gross_sharpe_like": gross_sharpe_like,
        "mean_turn_trade_return": trade_mean,
        "mean_turn_trade_return_bps": trade_mean * 10_000.0,
        "mean_turn_trade_gross_return_bps": gross_trade_mean * 10_000.0,
        "turn_trade_t_stat": trade_t_stat,
        "turnover": turnover,
        "average_gross_exposure": sum(
            abs(float(row["gross_exposure"])) for row in seg
        ) / len(seg),
        "ruined": ruin_bar is not None,
        "ruin_bar_index": ruin_bar,
    }


def _rolling(rows: list[dict[str, Any]], research_end: int) -> list[dict[str, Any]]:
    width = research_end // 5
    out: list[dict[str, Any]] = []
    start = 0
    for index in range(5):
        end = research_end if index == 4 else start + width
        out.append({
            "window_index": index + 1,
            **_stats(rows, start, end),
        })
        start = end
    return out


def _simulate_asset(
    candles: list[Candle],
    direction: float,
    exposure: float,
    cost_multiplier: float,
) -> list[dict[str, Any]]:
    if direction not in {-1.0, 1.0}:
        raise ValueError("direction must be -1.0 or 1.0")
    if exposure not in EXPOSURE_LEVELS:
        raise ValueError("Unsupported exposure")
    if len(candles) < 1:
        raise ValueError("Need at least one candle")

    cost_rate = COST_RATE * cost_multiplier
    out: list[dict[str, Any]] = []

    for candle in candles:
        is_turn = _is_turn_of_candle(candle)
        position = direction * exposure if is_turn else 0.0
        bar_return = candle.close / candle.open - 1.0
        turnover = 2.0 * abs(position) if is_turn else 0.0
        gross_return = position * bar_return if is_turn else 0.0
        net_return = gross_return - cost_rate * turnover

        out.append({
            "timestamp": candle.timestamp,
            "is_turn": is_turn,
            "net_return": net_return,
            "gross_return": gross_return,
            "turnover": turnover,
            "gross_exposure": position,
        })

    return out


def _align_assets(
    asset_rows: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    common = sorted(
        set.intersection(
            *[
                {row["timestamp"] for row in asset_rows[symbol]}
                for symbol in SYMBOLS
            ]
        )
    )
    lookup = {
        symbol: {row["timestamp"]: row for row in rows}
        for symbol, rows in asset_rows.items()
    }

    return [
        {
            "timestamp": timestamp,
            "is_turn": all(
                lookup[symbol][timestamp]["is_turn"]
                for symbol in SYMBOLS
            ),
            "net_return": sum(
                lookup[symbol][timestamp]["net_return"]
                for symbol in SYMBOLS
            ) / len(SYMBOLS),
            "gross_return": sum(
                lookup[symbol][timestamp]["gross_return"]
                for symbol in SYMBOLS
            ) / len(SYMBOLS),
            "turnover": sum(
                lookup[symbol][timestamp]["turnover"]
                for symbol in SYMBOLS
            ) / len(SYMBOLS),
            "gross_exposure": sum(
                lookup[symbol][timestamp]["gross_exposure"]
                for symbol in SYMBOLS
            ) / len(SYMBOLS),
        }
        for timestamp in common
    ]


def _benchmark_rows(assets: dict[str, list[Candle]]) -> list[dict[str, Any]]:
    common = sorted(
        set.intersection(
            *[
                {candle.timestamp for candle in candles}
                for candles in assets.values()
            ]
        )
    )
    lookup = {
        symbol: {candle.timestamp: candle for candle in candles}
        for symbol, candles in assets.items()
    }

    rows = []
    for timestamp in common:
        returns = [
            lookup[symbol][timestamp].close
            / lookup[symbol][timestamp].open
            - 1.0
            for symbol in SYMBOLS
        ]
        rows.append({
            "timestamp": timestamp,
            "is_turn": False,
            "net_return": sum(returns) / len(returns),
            "gross_return": sum(returns) / len(returns),
            "turnover": 0.0,
            "gross_exposure": 1.0,
        })
    return rows


def _load_or_download(
    symbol: str,
    data_dir: Path,
) -> tuple[list[Candle], dict[str, Any]]:
    store = MarketDataStore(data_dir)
    path = store.path_for(symbol, INTERVAL)
    candles = store.load(symbol, INTERVAL) if path.exists() else []

    if not candles:
        candles = load_binance_history(symbol, INTERVAL, TARGET_COUNT)
        store.save(symbol, INTERVAL, candles)

    if len(candles) != TARGET_COUNT:
        raise ValueError(
            f"{symbol}: expected {TARGET_COUNT}, got {len(candles)}"
        )

    validate_research_dataset(
        candles,
        INTERVAL,
        expected_count=TARGET_COUNT,
        max_age_intervals=8,
    )

    return candles, {
        "symbol": symbol,
        "interval": INTERVAL,
        "candle_count": len(candles),
        "data_start": candles[0].timestamp.isoformat(),
        "data_end": candles[-1].timestamp.isoformat(),
        "fingerprint": dataset_fingerprint(tuple(candles)),
    }


def analyze(data_dir: Path, output_path: Path) -> dict[str, Any]:
    if (
        settings.PAPER_ONLY is not True
        or settings.LIVE_TRADING_ENABLED is not False
    ):
        raise RuntimeError("Paper-only safety contract violated.")
    if max(EXPOSURE_LEVELS) > float(settings.MAX_LEVERAGE):
        raise RuntimeError(
            "Research exposure exceeds configured project maximum."
        )
    if PREVIOUS_MICRO_SYMBOLS & set(SYMBOLS):
        raise RuntimeError(
            "Universe is not symbol-disjoint from previous micro controls."
        )

    assets: dict[str, list[Candle]] = {}
    manifests: dict[str, dict[str, Any]] = {}
    for symbol in SYMBOLS:
        candles, manifest = _load_or_download(symbol, data_dir)
        assets[symbol] = candles
        manifests[symbol] = manifest

    common_timestamps = set.intersection(
        *[
            {candle.timestamp for candle in candles}
            for candles in assets.values()
        ]
    )
    expected_rows = len(common_timestamps)
    if expected_rows < TARGET_COUNT - 10:
        raise ValueError(
            "Too few common timestamps across assets: "
            f"{expected_rows} < {TARGET_COUNT - 10}"
        )

    research_end = int(expected_rows * RESEARCH_RATIO)
    results: dict[str, Any] = {}

    for name, direction in (("long", 1.0), ("short", -1.0)):
        direction_results: dict[str, Any] = {}
        for exposure in EXPOSURE_LEVELS:
            exposure_results: dict[str, Any] = {}
            for multiplier in COST_MULTIPLIERS:
                simulated = {
                    symbol: _simulate_asset(
                        assets[symbol],
                        direction,
                        exposure,
                        multiplier,
                    )
                    for symbol in SYMBOLS
                }
                rows = _align_assets(simulated)
                if len(rows) != expected_rows:
                    raise ValueError(
                        "Unexpected aligned row count: "
                        f"{len(rows)} != {expected_rows}"
                    )
                exposure_results[f"cost_{multiplier:g}x"] = {
                    "research": _stats(rows, 0, research_end),
                    "holdout": _stats(rows, research_end, len(rows)),
                    "rolling_research": _rolling(rows, research_end),
                }
            direction_results[f"exposure_{exposure:g}x"] = exposure_results
        results[name] = direction_results

    benchmark = _benchmark_rows(assets)
    result = {
        "schema_version": 1,
        "research_type": "microtrading_turn_candle_5m_2026_09_23",
        "status": "COMPLETED",
        "scope": {
            "universe": list(SYMBOLS),
            "symbol_disjoint_from_prior_micro_controls": True,
            "prior_micro_symbols": sorted(PREVIOUS_MICRO_SYMBOLS),
            "interval": INTERVAL,
            "target_count_per_asset": TARGET_COUNT,
            "research_ratio": RESEARCH_RATIO,
            "research_bar_count": research_end,
            "holdout_bar_count": expected_rows - research_end,
            "turn_minutes_utc": list(TURN_MINUTES),
            "execution": (
                "calendar-time signal at 00/15/30/45 UTC candle open -> "
                "same 5m candle close"
            ),
            "position_type": "directional_long_or_short_on_turn_bars_only",
            "portfolio_weighting": "equal_weight_25_25_25_25",
            "exposure_levels": list(EXPOSURE_LEVELS),
            "baseline_cost_rate": COST_RATE,
            "cost_multipliers": list(COST_MULTIPLIERS),
        },
        "hypotheses": {
            "long": "long only on UTC 00/15/30/45 turn bars",
            "short": "short only on UTC 00/15/30/45 turn bars",
            "selection_between_directions": False,
            "parameter_search": False,
        },
        "benchmarks": {
            "equal_weight_buy_and_hold_proxy": {
                "note": (
                    "Equal-weight per-bar close/open benchmark on the same "
                    "common timestamps; not the turn-bar strategy."
                ),
                "research": _stats(benchmark, 0, research_end),
                "holdout": _stats(benchmark, research_end, len(benchmark)),
            }
        },
        "modeling_limits": {
            "turn_signal_is_calendar_time_only": True,
            "short_is_price_return_proxy_not_execution_model": True,
            "funding_cost_modeled": False,
            "borrow_cost_modeled": False,
            "spread_cost_modeled": False,
            "latency_model": False,
            "liquidation_model": False,
            "production_candidate": False,
            "production_integration": False,
            "orders_enabled": False,
        },
        "data": manifests,
        "results": results,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "max_research_exposure": max(EXPOSURE_LEVELS),
        },
    }

    result["result_fingerprint"] = _fp(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        default="data/micro_turn_candle_5m_market_data",
    )
    parser.add_argument(
        "--output",
        default="research/microtrading_turn_candle_5m_2026_09_23.json",
    )
    args = parser.parse_args()

    result = analyze(Path(args.data_dir), Path(args.output))
    print("MICRO_TURN_CANDLE_STATUS:", result["status"])
    print("TURN_MINUTES_UTC:", TURN_MINUTES)
    print("RESULT_FINGERPRINT:", result["result_fingerprint"])

    for direction in ("long", "short"):
        for exposure in EXPOSURE_LEVELS:
            for multiplier in COST_MULTIPLIERS:
                holdout = result["results"][direction][
                    f"exposure_{exposure:g}x"
                ][f"cost_{multiplier:g}x"]["holdout"]
                print(
                    f"{direction.upper()}_{exposure:g}X_COST_{multiplier:g}X_HOLDOUT_RETURN:",
                    holdout["period_return"],
                )
                print(
                    f"{direction.upper()}_{exposure:g}X_COST_{multiplier:g}X_HOLDOUT_DD:",
                    holdout["max_drawdown_percent"],
                )
                print(
                    f"{direction.upper()}_{exposure:g}X_COST_{multiplier:g}X_HOLDOUT_PF:",
                    holdout["profit_factor"],
                )
                print(
                    f"{direction.upper()}_{exposure:g}X_COST_{multiplier:g}X_TURN_T_STAT:",
                    holdout["turn_trade_t_stat"],
                )
                print(
                    f"{direction.upper()}_{exposure:g}X_COST_{multiplier:g}X_TURNOVER:",
                    holdout["turnover"],
                )

    print(
        "BUY_HOLD_HOLDOUT_RETURN:",
        result["benchmarks"]["equal_weight_buy_and_hold_proxy"][
            "holdout"
        ]["period_return"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
