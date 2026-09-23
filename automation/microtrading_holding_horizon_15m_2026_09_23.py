"""Paper-only 15-minute holding-horizon control.

Purpose:
Test whether the prior directional reversal signal is overwhelmed mainly by
per-bar turnover. Both predeclared directional hypotheses are kept, together
with fixed holding horizons and fixed 1x/2x/3x exposure.

Universe is symbol-disjoint from both prior micro controls:
DOGEUSDT, LTCUSDT, LINKUSDT, AVAXUSDT.

Execution:
signal after prior completed close -> next bar open -> fixed H-bar holding ->
exit at the final held bar close.

No parameter search, no hypothesis selection, no production integration.
Short is a price-return proxy; funding, borrow, liquidation, and latency are
not modeled.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from backtesting.models import Candle
from config import settings
from data.binance_loader import load_binance_history
from data.market_store import MarketDataStore
from research.data_quality import validate_research_dataset
from research.protocol import dataset_fingerprint

SYMBOLS = ("DOGEUSDT", "LTCUSDT", "LINKUSDT", "AVAXUSDT")
PREVIOUS_MICRO_SYMBOLS = {
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "ADAUSDT",
}
INTERVAL = "15m"
TARGET_COUNT = 100_000
RESEARCH_RATIO = 0.80
HOLDING_HORIZONS = (1, 4, 16)
LEVERAGE_LEVELS = (1.0, 2.0, 3.0)
COST_RATE = 0.0015
COST_MULTIPLIERS = (0.0, 0.1, 0.25, 0.5, 1.0)
BARS_PER_DAY = 96
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


def _stats(rows: list[dict[str, Any]], start: int, end: int) -> dict[str, Any]:
    seg = rows[start:end]
    if not seg:
        return {"bar_count": 0}

    equity = peak = 1.0
    gross_equity = 1.0
    gross_peak = 1.0
    max_dd = 0.0
    gross_max_dd = 0.0
    net_profit = net_loss = 0.0
    gross_profit = gross_loss = 0.0
    values: list[float] = []
    gross_values: list[float] = []
    turnover = 0.0
    exposure = 0.0
    block_count = 0
    ruin_bar = None

    for offset, row in enumerate(seg):
        net_value = float(row["net_return"])
        gross_value = float(row["gross_return"])
        applied = max(-1.0, net_value)
        gross_applied = max(-1.0, gross_value)

        if equity > 0.0:
            equity *= 1.0 + applied
        else:
            equity = 0.0

        gross_equity *= 1.0 + gross_applied
        peak = max(peak, equity)
        gross_peak = max(gross_peak, gross_equity)
        max_dd = max(max_dd, 1.0 - equity / peak if equity > 0 else 1.0)
        gross_max_dd = max(
            gross_max_dd,
            1.0 - gross_equity / gross_peak if gross_equity > 0 else 1.0,
        )

        values.append(applied)
        gross_values.append(gross_value)
        net_profit += max(applied, 0.0)
        net_loss += max(-applied, 0.0)
        gross_profit += max(gross_value, 0.0)
        gross_loss += max(-gross_value, 0.0)
        turnover += float(row["turnover"])
        exposure += abs(float(row["gross_exposure"]))
        block_count += int(row["block_opened"])

        if ruin_bar is None and equity <= 0.0:
            ruin_bar = offset

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    vol = math.sqrt(variance) * ANNUALIZATION
    sharpe = mean * ANNUALIZATION / vol if vol > 0 else 0.0

    gross_mean = sum(gross_values) / len(gross_values)
    gross_variance = sum((x - gross_mean) ** 2 for x in gross_values) / len(
        gross_values
    )
    gross_vol = math.sqrt(gross_variance) * ANNUALIZATION
    gross_sharpe = (
        gross_mean * ANNUALIZATION / gross_vol if gross_vol > 0 else 0.0
    )

    return {
        "bar_count": len(seg),
        "period_return": equity - 1.0,
        "gross_period_return": gross_equity - 1.0,
        "cost_drag_period_return": (gross_equity - 1.0) - (equity - 1.0),
        "max_drawdown_percent": max_dd * 100.0,
        "gross_max_drawdown_percent": gross_max_dd * 100.0,
        "profit_factor": (
            net_profit / net_loss
            if net_loss > 0
            else ("inf" if net_profit > 0 else 0.0)
        ),
        "gross_profit_factor": (
            gross_profit / gross_loss
            if gross_loss > 0
            else ("inf" if gross_profit > 0 else 0.0)
        ),
        "mean_bar_return": mean,
        "gross_mean_bar_return": gross_mean,
        "annualized_volatility": vol,
        "gross_annualized_volatility": gross_vol,
        "sharpe_like": sharpe,
        "gross_sharpe_like": gross_sharpe,
        "turnover": turnover,
        "block_open_count": block_count,
        "average_gross_exposure": exposure / len(seg),
        "ruined": ruin_bar is not None,
        "ruin_bar_index": ruin_bar,
    }


def _rolling(rows: list[dict[str, Any]], research_end: int) -> list[dict[str, Any]]:
    width = research_end // 5
    out: list[dict[str, Any]] = []
    start = 0
    for index in range(5):
        end = research_end if index == 4 else start + width
        out.append({"window_index": index + 1, **_stats(rows, start, end)})
        start = end
    return out


def _signal_direction(prior_return: float, mode: str) -> float:
    if mode == "continuation":
        return 1.0 if prior_return > 0.0 else -1.0
    if mode == "reversal":
        return -1.0 if prior_return > 0.0 else 1.0
    raise ValueError("Unknown mode")


def _simulate_asset(
    candles: list[Candle],
    mode: str,
    horizon: int,
    leverage: float,
    cost_multiplier: float,
) -> list[dict[str, Any]]:
    if mode not in {"continuation", "reversal"}:
        raise ValueError("Unknown mode")
    if horizon not in HOLDING_HORIZONS:
        raise ValueError("Unsupported holding horizon")
    if leverage not in LEVERAGE_LEVELS:
        raise ValueError("Unsupported leverage")
    if len(candles) < horizon + 2:
        raise ValueError("Need enough candles for one complete holding block")

    cost_rate = COST_RATE * cost_multiplier
    out: list[dict[str, Any]] = []

    start = 2
    while start + horizon <= len(candles):
        prior_return = candles[start - 1].close / candles[start - 2].close - 1.0
        direction = _signal_direction(prior_return, mode)
        position = leverage * direction
        end = start + horizon

        for index in range(start, end):
            bar_return = candles[index].close / candles[index].open - 1.0
            entry_cost = cost_rate * abs(position) if index == start else 0.0
            exit_cost = cost_rate * abs(position) if index == end - 1 else 0.0
            turnover = (
                abs(position) if index == start else 0.0
            ) + (abs(position) if index == end - 1 else 0.0)

            net_return = position * bar_return - entry_cost - exit_cost
            out.append(
                {
                    "timestamp": candles[index].timestamp,
                    "net_return": net_return,
                    "gross_return": position * bar_return,
                    "turnover": turnover,
                    "gross_exposure": position,
                    "block_opened": int(index == start),
                }
            )

        start = end

    return out


def _align_assets(asset_rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
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
            "net_return": sum(
                lookup[symbol][timestamp]["net_return"] for symbol in SYMBOLS
            )
            / len(SYMBOLS),
            "gross_return": sum(
                lookup[symbol][timestamp]["gross_return"] for symbol in SYMBOLS
            )
            / len(SYMBOLS),
            "turnover": sum(
                lookup[symbol][timestamp]["turnover"] for symbol in SYMBOLS
            )
            / len(SYMBOLS),
            "gross_exposure": sum(
                lookup[symbol][timestamp]["gross_exposure"] for symbol in SYMBOLS
            )
            / len(SYMBOLS),
            "block_opened": sum(
                lookup[symbol][timestamp]["block_opened"] for symbol in SYMBOLS
            ),
        }
        for timestamp in common
    ]


def _load_or_download(symbol: str, data_dir: Path) -> tuple[list[Candle], dict[str, Any]]:
    store = MarketDataStore(data_dir)
    path = store.path_for(symbol, INTERVAL)
    candles = store.load(symbol, INTERVAL) if path.exists() else []

    if not candles:
        candles = load_binance_history(symbol, INTERVAL, TARGET_COUNT)
        store.save(symbol, INTERVAL, candles)

    if len(candles) != TARGET_COUNT:
        raise ValueError(f"{symbol}: expected {TARGET_COUNT}, got {len(candles)}")

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
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")
    if max(LEVERAGE_LEVELS) > float(settings.MAX_LEVERAGE):
        raise RuntimeError("Research leverage exceeds configured project maximum.")
    if PREVIOUS_MICRO_SYMBOLS & set(SYMBOLS):
        raise RuntimeError("Universe is not symbol-disjoint from previous micro controls.")

    assets: dict[str, list[Candle]] = {}
    manifests: dict[str, dict[str, Any]] = {}

    for symbol in SYMBOLS:
        candles, manifest = _load_or_download(symbol, data_dir)
        assets[symbol] = candles
        manifests[symbol] = manifest

    common_timestamps = set.intersection(
        *[
            {candle.timestamp for candle in candles[2:]}
            for candles in assets.values()
        ]
    )
    expected_rows = len(common_timestamps)
    if expected_rows < TARGET_COUNT - 10:
        raise ValueError(
            f"Too few common timestamps across assets: {expected_rows} < {TARGET_COUNT - 10}"
        )
    research_end = int(expected_rows * RESEARCH_RATIO)

    results: dict[str, Any] = {}
    for mode in ("continuation", "reversal"):
        horizon_results: dict[str, Any] = {}
        for horizon in HOLDING_HORIZONS:
            lev_results: dict[str, Any] = {}
            for leverage in LEVERAGE_LEVELS:
                cost_results: dict[str, Any] = {}
                for multiplier in COST_MULTIPLIERS:
                    simulated = {
                        symbol: _simulate_asset(
                            assets[symbol],
                            mode,
                            horizon,
                            leverage,
                            multiplier,
                        )
                        for symbol in SYMBOLS
                    }
                    rows = _align_assets(simulated)
                    horizon_expected = min(len(v) for v in simulated.values())
                    if len(rows) != horizon_expected:
                        raise ValueError(
                            f"Unexpected aligned row count: {len(rows)} != {horizon_expected}"
                        )

                    cost_results[f"cost_{multiplier:g}x"] = {
                        "research": _stats(rows, 0, research_end),
                        "holdout": _stats(rows, research_end, len(rows)),
                        "rolling_research": _rolling(rows, research_end),
                    }
                lev_results[f"leverage_{leverage:g}x"] = cost_results
            horizon_results[f"horizon_{horizon}bars"] = lev_results
        results[mode] = horizon_results

    result = {
        "schema_version": 1,
        "research_type": "microtrading_holding_horizon_15m",
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
            "execution": (
                "signal after prior completed close -> next open -> fixed holding "
                "horizon -> exit at final held close"
            ),
            "holding_horizons_bars": list(HOLDING_HORIZONS),
            "holding_horizons_minutes": [h * 15 for h in HOLDING_HORIZONS],
            "position_type": "directional_long_short",
            "portfolio_weighting": "equal_weight_25_25_25_25",
            "leverage_levels": list(LEVERAGE_LEVELS),
            "baseline_cost_rate": COST_RATE,
            "cost_multipliers": list(COST_MULTIPLIERS),
        },
        "hypotheses": {
            "continuation": "positive prior return -> long; negative -> short",
            "reversal": "positive prior return -> short; negative -> long",
            "selection_between_hypotheses": False,
            "parameter_search": False,
        },
        "modeling_limits": {
            "short_is_price_return_proxy_not_execution_model": True,
            "funding_cost_modeled": False,
            "borrow_cost_modeled": False,
            "liquidation_model": False,
            "latency_model": False,
            "production_candidate": False,
            "production_integration": False,
        },
        "data": manifests,
        "results": results,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "max_research_leverage": max(LEVERAGE_LEVELS),
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
        "--data-dir", default="data/micro_holding_horizon_market_data"
    )
    parser.add_argument(
        "--output",
        default="research/microtrading_holding_horizon_15m_2026_09_23.json",
    )
    args = parser.parse_args()

    result = analyze(Path(args.data_dir), Path(args.output))
    print("MICRO_HOLDING_HORIZON_STATUS:", result["status"])
    print("RESULT_FINGERPRINT:", result["result_fingerprint"])

    for mode in ("continuation", "reversal"):
        for horizon in HOLDING_HORIZONS:
            for leverage in LEVERAGE_LEVELS:
                for multiplier in COST_MULTIPLIERS:
                    block = result["results"][mode][f"horizon_{horizon}bars"][
                        f"leverage_{leverage:g}x"
                    ][f"cost_{multiplier:g}x"]
                    holdout = block["holdout"]
                    print(
                        f"{mode.upper()}_H{horizon}_{leverage:g}X_COST_{multiplier:g}X_HOLDOUT_RETURN:",
                        holdout["period_return"],
                    )
                    print(
                        f"{mode.upper()}_H{horizon}_{leverage:g}X_COST_{multiplier:g}X_HOLDOUT_GROSS_RETURN:",
                        holdout["gross_period_return"],
                    )
                    print(
                        f"{mode.upper()}_H{horizon}_{leverage:g}X_COST_{multiplier:g}X_HOLDOUT_DD:",
                        holdout["max_drawdown_percent"],
                    )
                    print(
                        f"{mode.upper()}_H{horizon}_{leverage:g}X_COST_{multiplier:g}X_HOLDOUT_PF:",
                        holdout["profit_factor"],
                    )
                    print(
                        f"{mode.upper()}_H{horizon}_{leverage:g}X_COST_{multiplier:g}X_TURNOVER:",
                        holdout["turnover"],
                    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
