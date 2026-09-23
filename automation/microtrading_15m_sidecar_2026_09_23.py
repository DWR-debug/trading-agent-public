"""Paper-only 15-minute micro-trading sidecar research.

Predeclared opposing hypotheses:
- continuation: long the next bar after a positive prior-bar return
- reversal: long the next bar after a negative prior-bar return

Universe: BTCUSDT and ETHUSDT, equal-weighted.
Execution: signal after completed bar close -> next bar open -> same bar close.
No leverage, no shorting, no parameter search, no selection.

This sidecar is methodologically separate from the validated daily ETF candidate.
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

SYMBOLS = ("BTCUSDT", "ETHUSDT")
INTERVAL = "15m"
TARGET_COUNT = 100_000
RESEARCH_RATIO = 0.80
COST_RATE = 0.0015
COST_MULTIPLIERS = (1.0, 2.0, 4.0)
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
    return hashlib.sha256(_canon(value).encode()).hexdigest()


def _stats(rows: list[dict[str, Any]], start: int, end: int) -> dict[str, Any]:
    seg = rows[start:end]
    if not seg:
        return {"bar_count": 0}

    equity = peak = 1.0
    max_dd = 0.0
    gp = gl = 0.0
    values: list[float] = []
    turnover = 0.0
    exposure = 0.0
    trades = 0

    for row in seg:
        value = row["net_return"]
        values.append(value)
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak if equity > 0 else 1.0)
        gp += max(value, 0.0)
        gl += max(-value, 0.0)
        turnover += row["turnover"]
        exposure += row["gross_exposure"]
        trades += int(row["trade_opened"])

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    vol = math.sqrt(variance) * ANNUALIZATION
    sharpe = mean * ANNUALIZATION / vol if vol > 0 else 0.0

    return {
        "bar_count": len(seg),
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": gp / gl if gl > 0 else ("inf" if gp > 0 else 0.0),
        "mean_bar_return": mean,
        "annualized_volatility": vol,
        "sharpe_like": sharpe,
        "turnover": turnover,
        "trade_open_count": trades,
        "average_gross_exposure": exposure / len(seg),
        "positive_bar_fraction": sum(x > 0 for x in values) / len(values),
    }


def _rolling(rows: list[dict[str, Any]], research_end: int) -> list[dict[str, Any]]:
    width = research_end // 5
    out = []
    start = 0
    for index in range(5):
        end = research_end if index == 4 else start + width
        out.append({"window_index": index + 1, **_stats(rows, start, end)})
        start = end
    return out


def _simulate_asset(
    candles: list[Candle],
    mode: str,
    multiplier: float,
) -> list[dict[str, Any]]:
    if mode not in {"continuation", "reversal", "buy_and_hold"}:
        raise ValueError("Unknown mode")
    if len(candles) < 3:
        raise ValueError("Need at least three candles")

    cost_rate = COST_RATE * multiplier
    previous_position = 0.0
    out = []

    for index in range(2, len(candles)):
        prior_return = candles[index - 1].close / candles[index - 2].close - 1.0

        if mode == "continuation":
            position = 1.0 if prior_return > 0.0 else 0.0
        elif mode == "reversal":
            position = 1.0 if prior_return < 0.0 else 0.0
        else:
            position = 1.0

        bar_return = candles[index].close / candles[index].open - 1.0
        turnover = abs(position - previous_position)
        trade_opened = int(previous_position == 0.0 and position > 0.0)
        net = position * bar_return - cost_rate * turnover

        out.append(
            {
                "timestamp": candles[index].timestamp,
                "net_return": net,
                "gross_return": position * bar_return,
                "turnover": turnover,
                "gross_exposure": position,
                "trade_opened": trade_opened,
            }
        )
        previous_position = position

    return out


def _align_assets(asset_rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    common = sorted(
        {row["timestamp"] for row in asset_rows[SYMBOLS[0]]}
        & {row["timestamp"] for row in asset_rows[SYMBOLS[1]]}
    )
    lookup = {
        symbol: {row["timestamp"]: row for row in rows}
        for symbol, rows in asset_rows.items()
    }

    return [
        {
            "timestamp": timestamp,
            "net_return": (
                0.5 * lookup[SYMBOLS[0]][timestamp]["net_return"]
                + 0.5 * lookup[SYMBOLS[1]][timestamp]["net_return"]
            ),
            "gross_return": (
                0.5 * lookup[SYMBOLS[0]][timestamp]["gross_return"]
                + 0.5 * lookup[SYMBOLS[1]][timestamp]["gross_return"]
            ),
            "turnover": (
                0.5 * lookup[SYMBOLS[0]][timestamp]["turnover"]
                + 0.5 * lookup[SYMBOLS[1]][timestamp]["turnover"]
            ),
            "gross_exposure": (
                0.5 * lookup[SYMBOLS[0]][timestamp]["gross_exposure"]
                + 0.5 * lookup[SYMBOLS[1]][timestamp]["gross_exposure"]
            ),
            "trade_opened": (
                lookup[SYMBOLS[0]][timestamp]["trade_opened"]
                + lookup[SYMBOLS[1]][timestamp]["trade_opened"]
            ),
        }
        for timestamp in common
    ]


def _load_or_download(symbol: str, data_dir: Path) -> tuple[list[Candle], dict[str, Any]]:
    store = MarketDataStore(data_dir)
    candles = store.load(symbol, INTERVAL) if store.path_for(symbol, INTERVAL).exists() else []

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

    assets: dict[str, list[Candle]] = {}
    manifests: dict[str, dict[str, Any]] = {}

    for symbol in SYMBOLS:
        candles, manifest = _load_or_download(symbol, data_dir)
        assets[symbol] = candles
        manifests[symbol] = manifest

    expected_rows = min(len(v) for v in assets.values()) - 2
    research_end = int(expected_rows * RESEARCH_RATIO)

    results: dict[str, Any] = {}
    for mode in ("continuation", "reversal", "buy_and_hold"):
        mode_results: dict[str, Any] = {}

        for multiplier in COST_MULTIPLIERS:
            simulated = {
                symbol: _simulate_asset(assets[symbol], mode, multiplier)
                for symbol in SYMBOLS
            }
            rows = _align_assets(simulated)

            if len(rows) != expected_rows:
                raise ValueError(
                    f"Unexpected aligned row count: {len(rows)} != {expected_rows}"
                )

            mode_results[f"cost_{multiplier:g}x"] = {
                "research": _stats(rows, 0, research_end),
                "holdout": _stats(rows, research_end, len(rows)),
                "rolling_research": _rolling(rows, research_end),
            }

        results[mode] = mode_results

    result = {
        "schema_version": 1,
        "research_type": "microtrading_15m_sidecar",
        "status": "COMPLETED",
        "scope": {
            "universe": list(SYMBOLS),
            "interval": INTERVAL,
            "target_count_per_asset": TARGET_COUNT,
            "research_ratio": RESEARCH_RATIO,
            "research_bar_count": research_end,
            "holdout_bar_count": expected_rows - research_end,
            "execution": (
                "signal after prior completed bar close -> next bar open "
                "-> same bar close"
            ),
            "position_type": "long_flat",
            "portfolio_weighting": "equal_weight_50_50",
            "baseline_cost_rate": COST_RATE,
            "cost_multipliers": list(COST_MULTIPLIERS),
        },
        "hypotheses": {
            "continuation": (
                "long next bar after positive prior-bar close-to-close return"
            ),
            "reversal": (
                "long next bar after negative prior-bar close-to-close return"
            ),
            "benchmark": "equal-weight buy-and-hold, no tactical exit",
            "selection_between_hypotheses": False,
            "parameter_search": False,
        },
        "data": manifests,
        "results": results,
        "interpretation_limits": {
            "separate_from_daily_etf_candidate": True,
            "not_a_production_candidate": True,
            "descriptive_not_causal": True,
            "not_an_hft_latency_strategy": True,
            "paper_only": True,
            "no_orders": True,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
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
    parser.add_argument("--data-dir", default="data/micro_market_data")
    parser.add_argument(
        "--output",
        default="research/microtrading_15m_sidecar_2026_09_23.json",
    )
    args = parser.parse_args()

    result = analyze(Path(args.data_dir), Path(args.output))

    print("MICRO_SIDECAR_STATUS:", result["status"])
    print("RESULT_FINGERPRINT:", result["result_fingerprint"])

    for mode in ("continuation", "reversal", "buy_and_hold"):
        for cost in ("cost_1x", "cost_2x", "cost_4x"):
            values = result["results"][mode][cost]
            print(
                f"{mode.upper()}_{cost}_RESEARCH_RETURN:",
                values["research"]["period_return"],
            )
            print(
                f"{mode.upper()}_{cost}_HOLDOUT_RETURN:",
                values["holdout"]["period_return"],
            )
            print(
                f"{mode.upper()}_{cost}_HOLDOUT_DD:",
                values["holdout"]["max_drawdown_percent"],
            )
            print(
                f"{mode.upper()}_{cost}_HOLDOUT_PF:",
                values["holdout"]["profit_factor"],
            )
            print(
                f"{mode.upper()}_{cost}_TURNOVER:",
                values["holdout"]["turnover"],
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
