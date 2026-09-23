"""Fixed multi-asset trend-portfolio control.

Diagnostic only. Uses the exact archived benchmark datasets and the fixed
strategies already defined by the literature strategy lab.

The portfolio is constructed without optimization:
- SPY, QQQ, IWM
- equal capital allocation across assets
- per-asset ATR-based exposure from the literature lab
- trend families: TSM ensemble, SMA 50/200, and a fixed 50/50 blend
- buy-and-hold equal-weight reference
- close(t) decision -> open(t+1) -> open(t+2) return
- fixed costs and no live execution
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from automation.literature_strategy_lab import (
    ASSETS,
    HOLDOUT_COUNT,
    RESEARCH_COUNT,
    TARGET_COUNT,
    build_exposure,
    dataset_fingerprint,
    generate_signal,
    load_bars,
)

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_PER_SIDE = FEE_RATE + SLIPPAGE_RATE

PORTFOLIO_STRATEGIES = (
    "buy_and_hold",
    "tsm_ensemble",
    "sma_50_200_long_flat",
    "blend_tsm_sma",
)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


def _verify_assets(
    data_dir: Path,
    manifest_path: Path,
):
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )
    expected = {
        item["symbol"]: item
        for item in manifest.get("datasets", [])
        if isinstance(item, dict) and "symbol" in item
    }

    loaded = {}
    for symbol in ASSETS:
        if symbol not in expected:
            raise ValueError(f"Manifest enthält {symbol} nicht.")

        bars = load_bars(
            data_dir / symbol / "1d.csv"
        )
        actual = dataset_fingerprint(bars)
        if actual != expected[symbol].get("fingerprint"):
            raise ValueError(
                f"{symbol}: Dataset-Fingerprint stimmt nicht mit dem "
                "Archiv überein."
            )
        loaded[symbol] = bars

    return manifest, loaded


def _asset_exposures(assets: dict) -> dict:
    exposures = {}

    for symbol, bars in assets.items():
        tsm_signal = generate_signal(
            bars,
            "tsm_ensemble",
        )
        sma_signal = generate_signal(
            bars,
            "sma_50_200_long_flat",
        )
        exposures[symbol] = {
            "tsm_ensemble": build_exposure(
                bars,
                tsm_signal,
            ),
            "sma_50_200_long_flat": build_exposure(
                bars,
                sma_signal,
            ),
            "buy_and_hold": [1.0] * len(bars),
        }

    return exposures


def _target_exposure(
    exposures: dict,
    symbol: str,
    strategy: str,
    index: int,
) -> float:
    if strategy == "blend_tsm_sma":
        return (
            exposures[symbol]["tsm_ensemble"][index]
            + exposures[symbol]["sma_50_200_long_flat"][index]
        ) / 2.0

    return exposures[symbol][strategy][index]


def _daily_returns(
    assets: dict,
    exposures: dict,
    strategy: str,
) -> list[float]:
    length = min(
        len(bars)
        for bars in assets.values()
    )
    if length < 3:
        return []

    previous = {
        symbol: 0.0
        for symbol in ASSETS
    }
    returns = []

    for decision_index in range(length - 2):
        portfolio_return = 0.0
        turnover = 0.0

        for symbol in ASSETS:
            bars = assets[symbol]
            target = _target_exposure(
                exposures,
                symbol,
                strategy,
                decision_index,
            )

            market_return = (
                bars[decision_index + 2].open
                / bars[decision_index + 1].open
                - 1.0
            )

            portfolio_return += (
                target / len(ASSETS)
            ) * market_return
            turnover += (
                abs(target - previous[symbol])
                / len(ASSETS)
            )
            previous[symbol] = target

        returns.append(
            portfolio_return
            - COST_PER_SIDE * turnover
        )

    return returns


def _stats(
    returns: list[float],
    start_index: int,
    end_index: int,
) -> dict:
    first = max(0, start_index)
    last = min(
        end_index - 3,
        len(returns) - 1,
    )

    segment = (
        returns[first:last + 1]
        if last >= first
        else []
    )

    if not segment:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "positive_day_ratio": 0.0,
            "day_count": 0,
        }

    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    positive_days = 0

    for value in segment:
        equity *= 1.0 + value
        peak = max(peak, equity)
        if peak > 0:
            max_drawdown = max(
                max_drawdown,
                1.0 - equity / peak,
            )

        if value > 0:
            gross_profit += value
            positive_days += 1
        elif value < 0:
            gross_loss -= value

    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    elif gross_profit > 0:
        profit_factor = "inf"
    else:
        profit_factor = 0.0

    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_drawdown * 100.0,
        "profit_factor": profit_factor,
        "positive_day_ratio": positive_days / len(segment),
        "day_count": len(segment),
    }


def _rolling(returns: list[float]) -> list[dict]:
    windows = (
        (2250, 2700),
        (2700, 3150),
        (3150, 3600),
        (3600, 4050),
        (4050, 4500),
    )
    return [
        {
            "window_index": index,
            "start_index": start,
            "end_index": end,
            **_stats(returns, start, end),
        }
        for index, (start, end) in enumerate(windows, start=1)
    ]


def _aggregate_strategy(returns: list[float]) -> dict:
    rolling = _rolling(returns)
    return {
        "research": _stats(
            returns,
            0,
            RESEARCH_COUNT,
        ),
        "holdout": _stats(
            returns,
            RESEARCH_COUNT,
            TARGET_COUNT,
        ),
        "rolling": rolling,
        "rolling_positive_window_count": sum(
            item["period_return"] > 0
            for item in rolling
        ),
        "rolling_positive_window_ratio": (
            sum(
                item["period_return"] > 0
                for item in rolling
            )
            / len(rolling)
        ),
    }


def run_control(
    data_dir: Path,
    manifest_path: Path,
    output_path: Path,
) -> dict:
    manifest, assets = _verify_assets(
        data_dir,
        manifest_path,
    )
    exposures = _asset_exposures(assets)

    results = {}
    for strategy in PORTFOLIO_STRATEGIES:
        daily_returns = _daily_returns(
            assets,
            exposures,
            strategy,
        )
        results[strategy] = _aggregate_strategy(
            daily_returns
        )

    report = {
        "diagnostic_type": "multi_asset_trend_portfolio_control",
        "status": "COMPLETED",
        "source": {
            "target_count": TARGET_COUNT,
            "research_candle_count": RESEARCH_COUNT,
            "holdout_candle_count": HOLDOUT_COUNT,
            "manifest_fingerprint": manifest.get(
                "manifest_fingerprint"
            ),
            "manifest_run_id": manifest.get(
                "provenance",
                {},
            ).get("run_id"),
        },
        "methodology": {
            "assets": list(ASSETS),
            "strategies": list(PORTFOLIO_STRATEGIES),
            "optimization_used": False,
            "selection_profile_used": False,
            "portfolio_weighting": (
                "equal capital weight across the three assets"
            ),
            "asset_exposure_model": (
                "ATR-based volatility scaling from the fixed literature lab"
            ),
            "execution": (
                "decision_at_close_t_then_next_session_open_to_following_open"
            ),
            "fee_rate": FEE_RATE,
            "slippage_rate": SLIPPAGE_RATE,
            "rolling_geometry": {
                "train_candles": 2250,
                "test_candles": 450,
                "step_candles": 450,
                "window_count": 5,
            },
            "holdout_is_blind_to_selection": True,
        },
        "strategies": results,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }

    report["report_fingerprint"] = _fingerprint(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_control(
        Path(args.data_dir),
        Path(args.manifest),
        Path(args.output),
    )

    print("MULTI_ASSET_PORTFOLIO_STATUS:", report["status"])
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])
    for strategy, result in report["strategies"].items():
        print(
            strategy,
            "RESEARCH_RETURN=",
            result["research"]["period_return"],
            "HOLDOUT_RETURN=",
            result["holdout"]["period_return"],
            "ROLLING_POSITIVE_RATIO=",
            result["rolling_positive_window_ratio"],
        )


if __name__ == "__main__":
    main()
