"""Fixed risk-normalized multi-asset trend portfolio control.

Diagnostic only. The signal families are fixed and come from the
literature-informed lab. Portfolio weights are determined mechanically from
inverse ATR risk across assets with active signals, normalized to 100 percent
gross exposure.

No parameter optimization, selection profiles, gate changes, or live trading.
The weighting rule is pre-registered for this diagnostic control and is not tuned
against the holdout segment.
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
    atr_percent_series,
    dataset_fingerprint,
    generate_signal,
    load_bars,
)

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_PER_SIDE = FEE_RATE + SLIPPAGE_RATE

STRATEGIES = (
    "buy_and_hold",
    "tsm_ensemble_risk_normalized",
    "sma_50_200_risk_normalized",
    "blend_tsm_sma_risk_normalized",
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


def _verify_assets(data_dir: Path, manifest_path: Path):
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )
    expected = {
        item["symbol"]: item
        for item in manifest.get("datasets", [])
        if isinstance(item, dict) and "symbol" in item
    }

    assets = {}
    for symbol in ASSETS:
        if symbol not in expected:
            raise ValueError(f"Manifest enthält {symbol} nicht.")

        bars = load_bars(data_dir / symbol / "1d.csv")
        actual = dataset_fingerprint(bars)
        if actual != expected[symbol].get("fingerprint"):
            raise ValueError(
                f"{symbol}: Dataset-Fingerprint stimmt nicht mit dem Archiv überein."
            )
        assets[symbol] = bars

    return manifest, assets


def _signal_by_strategy(
    bars,
    strategy: str,
) -> list[int]:
    if strategy == "tsm_ensemble_risk_normalized":
        return generate_signal(bars, "tsm_ensemble")
    if strategy == "sma_50_200_risk_normalized":
        return generate_signal(bars, "sma_50_200_long_flat")
    if strategy == "blend_tsm_sma_risk_normalized":
        tsm = generate_signal(bars, "tsm_ensemble")
        sma = generate_signal(bars, "sma_50_200_long_flat")
        return [
            1 if (a + b) > 0 else -1 if (a + b) < 0 else 0
            for a, b in zip(tsm, sma)
        ]
    raise ValueError(f"Unbekannte Strategie: {strategy}")


def _target_weights(
    assets: dict,
    signals: dict[str, list[int]],
    strategy: str,
    index: int,
) -> dict[str, float]:
    if strategy == "buy_and_hold":
        return {
            symbol: 1.0 / len(ASSETS)
            for symbol in ASSETS
        }

    raw = {}
    for symbol in ASSETS:
        signal = signals[symbol][index]
        if signal == 0:
            continue

        atr = atr_percent_series(assets[symbol])[index]
        if atr is None or atr <= 0:
            continue

        raw[symbol] = signal / atr

    normalizer = sum(
        abs(value)
        for value in raw.values()
    )
    if normalizer <= 0:
        return {
            symbol: 0.0
            for symbol in ASSETS
        }

    return {
        symbol: (
            raw.get(symbol, 0.0)
            / normalizer
        )
        for symbol in ASSETS
    }


def _daily_returns(
    assets: dict,
    strategy: str,
) -> list[float]:
    length = min(
        len(bars)
        for bars in assets.values()
    )
    if length < 3:
        return []

    signals = {
        symbol: _signal_by_strategy(
            bars,
            strategy,
        )
        if strategy != "buy_and_hold"
        else [1] * len(bars)
        for symbol, bars in assets.items()
    }

    previous = {
        symbol: 0.0
        for symbol in ASSETS
    }
    returns = []

    for decision_index in range(length - 2):
        weights = _target_weights(
            assets,
            signals,
            strategy,
            decision_index,
        )
        portfolio_return = 0.0
        turnover = 0.0

        for symbol in ASSETS:
            target = weights[symbol]
            previous_weight = previous[symbol]
            bars = assets[symbol]

            market_return = (
                bars[decision_index + 2].open
                / bars[decision_index + 1].open
                - 1.0
            )

            portfolio_return += target * market_return
            turnover += abs(
                target - previous_weight
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

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0
        else "inf"
        if gross_profit > 0
        else 0.0
    )

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


def run_control(
    data_dir: Path,
    manifest_path: Path,
    output_path: Path,
) -> dict:
    manifest, assets = _verify_assets(
        data_dir,
        manifest_path,
    )

    strategy_results = {}
    for strategy in STRATEGIES:
        returns = _daily_returns(
            assets,
            strategy,
        )
        rolling = _rolling(returns)
        strategy_results[strategy] = {
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

    report = {
        "diagnostic_type": "risk_normalized_trend_portfolio_control",
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
            "strategies": list(STRATEGIES),
            "optimization_used": False,
            "selection_profile_used": False,
            "weighting": (
                "inverse_ATR_over_active_signals_normalized_to_100_percent_gross"
            ),
            "signal_sources": {
                "tsm": "63/126/252-day ensemble",
                "sma": "50/200-day long/flat",
                "blend": "fixed equal blend of the two directions",
            },
            "execution": (
                "decision_at_close_t_then_next_session_open_to_following_open"
            ),
            "fee_rate": FEE_RATE,
            "slippage_rate": SLIPPAGE_RATE,
            "holdout_is_blind_to_selection": True,
        },
        "strategies": strategy_results,
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

    print("RISK_NORMALIZED_PORTFOLIO_STATUS:", report["status"])
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
