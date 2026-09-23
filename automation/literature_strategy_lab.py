"""Literature-informed, point-in-time strategy-family research lab.

This module is intentionally separate from the production strategy engine.
It evaluates a small pre-registered set of price-only strategy families that
have a documented research tradition, using:
- close-time decisions
- next-session-open execution
- fixed transaction costs
- ATR-based, volatility-scaled exposure
- fixed, non-optimized strategy rules

It is diagnostic research only. It does not alter production parameters,
selection rules, research gates, or enable live trading.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from research.protocol import dataset_fingerprint as protocol_dataset_fingerprint


ASSETS = ("SPY", "QQQ", "IWM")
TARGET_COUNT = 5000
RESEARCH_COUNT = 4500
HOLDOUT_COUNT = 500
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_PER_SIDE = FEE_RATE + SLIPPAGE_RATE

ATR_WINDOW = 20
RISK_TARGET = 0.01
STOP_ATR = 3.0
MAX_EXPOSURE = 1.0
REBALANCE_DAYS = 21

STRATEGIES = (
    "buy_and_hold",
    "tsm_126",
    "tsm_ensemble",
    "donchian_55_20",
    "sma_50_200_long_flat",
    "mean_reversion_20_2",
)


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


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


def load_bars(
    path: Path,
    expected_count: int | None = TARGET_COUNT,
) -> tuple[Bar, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = (
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        )
        if tuple(reader.fieldnames or ()) != required:
            raise ValueError(f"Ungültige Spalten in {path}")

        bars = []
        for row in reader:
            bars.append(
                Bar(
                    timestamp=datetime.fromisoformat(
                        row["timestamp"].replace("Z", "+00:00")
                    ),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            )

    if expected_count is not None and len(bars) != expected_count:
        raise ValueError(
            f"{path}: {len(bars)} Candles statt {expected_count}"
        )
    return tuple(bars)


def dataset_fingerprint(bars: tuple[Bar, ...]) -> str:
    from backtesting.models import Candle

    candles = tuple(
        Candle(
            timestamp=item.timestamp,
            open=item.open,
            high=item.high,
            low=item.low,
            close=item.close,
            volume=item.volume,
        )
        for item in bars
    )
    return protocol_dataset_fingerprint(candles)


def true_range_series(bars: tuple[Bar, ...]) -> list[float]:
    values = []
    previous_close = None
    for bar in bars:
        if previous_close is None:
            values.append(bar.high - bar.low)
        else:
            values.append(
                max(
                    bar.high - bar.low,
                    abs(bar.high - previous_close),
                    abs(bar.low - previous_close),
                )
            )
        previous_close = bar.close
    return values


def atr_percent_series(
    bars: tuple[Bar, ...],
    window: int = ATR_WINDOW,
) -> list[float | None]:
    tr = true_range_series(bars)
    result = [None] * len(bars)
    running = 0.0

    for index, value in enumerate(tr):
        running += value
        if index >= window:
            running -= tr[index - window]
        if index >= window - 1 and bars[index].close > 0:
            result[index] = (running / window) / bars[index].close

    return result


def _tsm_signal(closes: list[float], lookback: int) -> list[int]:
    signal = [0] * len(closes)
    for index in range(lookback, len(closes)):
        change = closes[index] / closes[index - lookback] - 1.0
        signal[index] = 1 if change > 0 else -1 if change < 0 else 0
    return signal


def _tsm_ensemble_signal(
    closes: list[float],
    lookbacks=(63, 126, 252),
) -> list[int]:
    signal = [0] * len(closes)
    minimum = max(lookbacks)
    for index in range(minimum, len(closes)):
        votes = sum(
            1
            if closes[index] / closes[index - lookback] - 1.0 > 0
            else -1
            if closes[index] / closes[index - lookback] - 1.0 < 0
            else 0
            for lookback in lookbacks
        )
        signal[index] = 1 if votes > 0 else -1 if votes < 0 else 0
    return signal


def _donchian_signal(
    closes: list[float],
    entry_window: int = 55,
    exit_window: int = 20,
) -> list[int]:
    signal = [0] * len(closes)
    for index in range(entry_window, len(closes)):
        previous = closes[index - entry_window:index]
        if closes[index] > max(previous):
            signal[index] = 1
        elif closes[index] < min(previous):
            signal[index] = -1
        else:
            signal[index] = signal[index - 1]

        if signal[index] == 1 and index >= exit_window:
            if closes[index] < min(closes[index - exit_window:index]):
                signal[index] = 0
        elif signal[index] == -1 and index >= exit_window:
            if closes[index] > max(closes[index - exit_window:index]):
                signal[index] = 0

    return signal


def _sma_long_flat_signal(
    closes: list[float],
    fast: int = 50,
    slow: int = 200,
) -> list[int]:
    signal = [0] * len(closes)
    fast_sum = 0.0
    slow_sum = 0.0

    for index, value in enumerate(closes):
        fast_sum += value
        slow_sum += value

        if index >= fast:
            fast_sum -= closes[index - fast]
        if index >= slow:
            slow_sum -= closes[index - slow]

        if index >= slow - 1:
            signal[index] = (
                1
                if (fast_sum / fast) > (slow_sum / slow)
                else 0
            )

    return signal


def _mean_reversion_signal(
    closes: list[float],
    window: int = 20,
    entry_z: float = 2.0,
) -> list[int]:
    signal = [0] * len(closes)

    for index in range(window, len(closes)):
        sample = closes[index - window:index]
        mean = sum(sample) / window
        variance = sum(
            (value - mean) ** 2
            for value in sample
        ) / window
        standard_deviation = math.sqrt(variance)

        if standard_deviation <= 0:
            signal[index] = signal[index - 1]
            continue

        z_score = (closes[index] - mean) / standard_deviation

        if signal[index - 1] == 0:
            if z_score <= -entry_z:
                signal[index] = 1
            elif z_score >= entry_z:
                signal[index] = -1
        elif signal[index - 1] == 1:
            signal[index] = 0 if z_score >= 0 else 1
        else:
            signal[index] = 0 if z_score <= 0 else -1

    return signal


def generate_signal(
    bars: tuple[Bar, ...],
    strategy_name: str,
) -> list[int]:
    closes = [item.close for item in bars]

    if strategy_name == "buy_and_hold":
        return [1] * len(bars)
    if strategy_name == "tsm_126":
        return _tsm_signal(closes, 126)
    if strategy_name == "tsm_ensemble":
        return _tsm_ensemble_signal(closes)
    if strategy_name == "donchian_55_20":
        return _donchian_signal(closes)
    if strategy_name == "sma_50_200_long_flat":
        return _sma_long_flat_signal(closes)
    if strategy_name == "mean_reversion_20_2":
        return _mean_reversion_signal(closes)

    raise ValueError(f"Unbekannte Strategie: {strategy_name}")


def build_exposure(
    bars: tuple[Bar, ...],
    signal: list[int],
) -> list[float]:
    atr = atr_percent_series(bars)
    exposure = [0.0] * len(bars)
    current = 0.0
    previous_signal = 0

    for index, target_signal in enumerate(signal):
        if target_signal == 0:
            current = 0.0
        elif (
            target_signal != previous_signal
            or index % REBALANCE_DAYS == 0
        ):
            atr_value = atr[index]
            if atr_value is not None and atr_value > 0:
                current = target_signal * min(
                    MAX_EXPOSURE,
                    RISK_TARGET / (STOP_ATR * atr_value),
                )
            else:
                current = 0.0

        exposure[index] = current
        previous_signal = target_signal

    return exposure


def evaluate(
    bars: tuple[Bar, ...],
    exposure: list[float],
    start_index: int,
    end_index: int,
) -> dict:
    if end_index > len(bars):
        raise ValueError("end_index außerhalb des Datensatzes.")

    returns = []
    previous_exposure = 0.0

    first_decision = max(0, start_index)
    last_decision = min(end_index - 3, len(bars) - 3)

    for decision_index in range(
        first_decision,
        last_decision + 1,
    ):
        next_open_index = decision_index + 1
        exit_open_index = decision_index + 2

        market_return = (
            bars[exit_open_index].open
            / bars[next_open_index].open
            - 1.0
        )
        target_exposure = exposure[decision_index]
        trading_cost = COST_PER_SIDE * abs(
            target_exposure - previous_exposure
        )
        returns.append(
            target_exposure * market_return - trading_cost
        )
        previous_exposure = target_exposure

    if not returns:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "daily_profit_factor": 0.0,
            "positive_day_ratio": 0.0,
            "active_days": 0,
            "turnover_events": 0,
        }

    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    positive_days = 0
    active_days = 0
    turnover_events = 0

    for value in returns:
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

        if value != 0:
            active_days += 1

    for index in range(
        max(1, start_index - 2),
        min(end_index - 1, len(exposure)),
    ):
        if abs(exposure[index] - exposure[index - 1]) > 1e-12:
            turnover_events += 1

    if gross_loss > 0:
        daily_profit_factor = gross_profit / gross_loss
    elif gross_profit > 0:
        daily_profit_factor = "inf"
    else:
        daily_profit_factor = 0.0

    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_drawdown * 100.0,
        "daily_profit_factor": daily_profit_factor,
        "positive_day_ratio": positive_days / len(returns),
        "active_days": active_days,
        "turnover_events": turnover_events,
    }


def _rolling_segments() -> tuple[tuple[int, int], ...]:
    return (
        (0, 4500),
        (2250, 2700),
        (2700, 3150),
        (3150, 3600),
        (3600, 4050),
        (4050, 4500),
    )


def run_asset(bars: tuple[Bar, ...], symbol: str) -> dict:
    strategies = {}

    for strategy_name in STRATEGIES:
        signal = generate_signal(bars, strategy_name)
        exposure = build_exposure(bars, signal)

        strategies[strategy_name] = {
            "research": evaluate(bars, exposure, 0, RESEARCH_COUNT),
            "holdout": evaluate(
                bars,
                exposure,
                RESEARCH_COUNT,
                TARGET_COUNT,
            ),
            "rolling": [
                evaluate(bars, exposure, start, end)
                for start, end in _rolling_segments()[1:]
            ],
            "signal_statistics": {
                "long_days": sum(value > 0 for value in signal),
                "short_days": sum(value < 0 for value in signal),
                "flat_days": sum(value == 0 for value in signal),
            },
        }

    return {
        "symbol": symbol,
        "candle_count": len(bars),
        "data_start": bars[0].timestamp.isoformat(),
        "data_end": bars[-1].timestamp.isoformat(),
        "dataset_fingerprint": dataset_fingerprint(bars),
        "strategies": strategies,
    }


def aggregate(report_assets: dict[str, dict]) -> dict:
    summary = {}

    for strategy_name in STRATEGIES:
        research = [
            report_assets[symbol]["strategies"][strategy_name]["research"]
            for symbol in ASSETS
        ]
        holdout = [
            report_assets[symbol]["strategies"][strategy_name]["holdout"]
            for symbol in ASSETS
        ]
        rolling = [
            window
            for symbol in ASSETS
            for window in report_assets[symbol]["strategies"][strategy_name]["rolling"]
        ]

        summary[strategy_name] = {
            "research_total_return_geometric_sum": (
                math.prod(1.0 + item["period_return"] for item in research)
                - 1.0
            ),
            "research_positive_asset_count": sum(
                item["period_return"] > 0 for item in research
            ),
            "research_max_drawdown_worst_asset": max(
                item["max_drawdown_percent"] for item in research
            ),
            "holdout_total_return_geometric_sum": (
                math.prod(1.0 + item["period_return"] for item in holdout)
                - 1.0
            ),
            "holdout_positive_asset_count": sum(
                item["period_return"] > 0 for item in holdout
            ),
            "rolling_positive_window_count": sum(
                item["period_return"] > 0 for item in rolling
            ),
            "rolling_window_count": len(rolling),
            "rolling_positive_window_ratio": (
                sum(item["period_return"] > 0 for item in rolling)
                / len(rolling)
                if rolling
                else 0.0
            ),
            "rolling_median_max_drawdown_percent": (
                sorted(
                    item["max_drawdown_percent"]
                    for item in rolling
                )[len(rolling) // 2]
                if rolling
                else 0.0
            ),
        }

    return summary


def run_lab(
    data_dir: Path,
    manifest_path: Path,
    output_path: Path,
) -> dict:
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    manifest_assets = {
        item["symbol"]: item
        for item in manifest["datasets"]
    }

    assets = {}
    for symbol in ASSETS:
        bars = load_bars(
            data_dir / symbol / "1d.csv"
        )
        actual_fingerprint = dataset_fingerprint(bars)
        expected_fingerprint = manifest_assets[symbol]["fingerprint"]
        if actual_fingerprint != expected_fingerprint:
            raise ValueError(
                f"{symbol}: Daten-Fingerprint weicht vom Archiv ab."
            )
        assets[symbol] = run_asset(bars, symbol)

    report = {
        "diagnostic_type": "literature_informed_strategy_family_lab",
        "status": "COMPLETED",
        "source": {
            "target_count": TARGET_COUNT,
            "research_candle_count": RESEARCH_COUNT,
            "holdout_candle_count": HOLDOUT_COUNT,
            "manifest_fingerprint": manifest.get("manifest_fingerprint"),
        },
        "methodology": {
            "strategy_rules_are_pre_registered": True,
            "optimization_used": False,
            "selection_profile_used": False,
            "execution": "decision_at_close_t_then_next_session_open_execution",
            "return_interval": "next_open_to_following_open",
            "fee_rate": FEE_RATE,
            "slippage_rate": SLIPPAGE_RATE,
            "atr_window": ATR_WINDOW,
            "risk_target": RISK_TARGET,
            "stop_atr": STOP_ATR,
            "max_exposure": MAX_EXPOSURE,
            "rebalance_days": REBALANCE_DAYS,
            "families": list(STRATEGIES),
        },
        "assets": assets,
        "aggregate": aggregate(assets),
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

    report = run_lab(
        Path(args.data_dir),
        Path(args.manifest),
        Path(args.output),
    )

    print("LITERATURE_STRATEGY_LAB_STATUS:", report["status"])
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])
    for strategy_name, metrics in report["aggregate"].items():
        print(
            strategy_name,
            "RESEARCH_POSITIVE_ASSETS=",
            metrics["research_positive_asset_count"],
            "HOLDOUT_POSITIVE_ASSETS=",
            metrics["holdout_positive_asset_count"],
            "ROLLING_POSITIVE_WINDOW_RATIO=",
            metrics["rolling_positive_window_ratio"],
        )


if __name__ == "__main__":
    main()
