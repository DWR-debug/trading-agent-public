"""Cross-sectional equity momentum control on a fresh archived universe.

Pre-registered diagnostic only:
- universe: small_cap_high_volatility
- five assets, common 1,000 daily candles
- 6-1 and 12-1 formation variants
- long-only top-2 and long-short top-2 vs bottom-2
- 21-session rebalance
- close(t) decision -> next-open execution
- fixed costs, no optimization, no selection profiles
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from backtesting.models import Candle
from research.protocol import dataset_fingerprint as protocol_dataset_fingerprint

UNIVERSE = "small_cap_high_volatility"
ASSETS = ("SOUN", "RKLB", "IONQ", "ASTS", "HIMS")

TARGET_COUNT = 1000
RESEARCH_COUNT = 800
HOLDOUT_COUNT = 200

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_PER_SIDE = FEE_RATE + SLIPPAGE_RATE

SKIP = 21
REBALANCE_DAYS = 21
TOP_N = 2

STRATEGIES = (
    "cs_momentum_126_long_only_top2",
    "cs_momentum_252_long_only_top2",
    "cs_momentum_126_long_short_2x2",
    "cs_momentum_252_long_short_2x2",
    "equal_weight_buy_and_hold",
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


def load_bars(path: Path, expected_count: int) -> tuple[Bar, ...]:
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

        bars = tuple(
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
            for row in reader
        )

    if len(bars) != expected_count:
        raise ValueError(
            f"{path}: {len(bars)} Candles statt {expected_count}"
        )
    return bars


def dataset_fingerprint(bars: tuple[Bar, ...]) -> str:
    candles = tuple(
        Candle(
            timestamp=bar.timestamp,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
        )
        for bar in bars
    )
    return protocol_dataset_fingerprint(candles)


def load_assets(
    data_dir: Path,
    manifest_path: Path,
) -> tuple[dict[str, tuple[Bar, ...]], dict]:
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    if manifest.get("universe") != UNIVERSE:
        raise ValueError("Unerwartetes Research-Universum.")
    if manifest.get("target_count") != TARGET_COUNT:
        raise ValueError("Unerwartete Zielhistorie.")

    manifest_assets = {
        item["symbol"]: item
        for item in manifest.get("datasets", [])
    }
    if tuple(manifest_assets) != ASSETS:
        raise ValueError(
            f"Unerwartete Asset-Reihenfolge: {tuple(manifest_assets)}"
        )

    assets = {}
    for symbol in ASSETS:
        item = manifest_assets[symbol]
        bars = load_bars(
            data_dir / symbol / "1d.csv",
            int(item["candle_count"]),
        )
        actual = dataset_fingerprint(bars)
        if actual != item["fingerprint"]:
            raise ValueError(
                f"{symbol}: Dataset-Fingerprint stimmt nicht."
            )
        assets[symbol] = bars

    first_dates = {
        bars[0].timestamp
        for bars in assets.values()
    }
    last_dates = {
        bars[-1].timestamp
        for bars in assets.values()
    }
    if len(first_dates) != 1 or len(last_dates) != 1:
        raise ValueError(
            "Asset-Zeitachsen sind nicht identisch."
        )

    return assets, manifest


def _score(
    assets: dict[str, tuple[Bar, ...]],
    decision_index: int,
    lookback: int,
) -> dict[str, float]:
    if decision_index < lookback:
        return {}

    score = {}
    for symbol, bars in assets.items():
        score[symbol] = (
            bars[decision_index - SKIP].close
            / bars[decision_index - lookback].close
            - 1.0
        )
    return score


def target_weights(
    assets: dict[str, tuple[Bar, ...]],
    strategy: str,
    decision_index: int,
) -> dict[str, float]:
    if strategy == "equal_weight_buy_and_hold":
        return {
            symbol: 1.0 / len(ASSETS)
            for symbol in ASSETS
        }

    lookback = (
        126
        if "126" in strategy
        else 252
    )
    score = _score(
        assets,
        decision_index,
        lookback,
    )
    if not score:
        return {
            symbol: 0.0
            for symbol in ASSETS
        }

    ranking = sorted(
        score,
        key=score.get,
        reverse=True,
    )
    winners = ranking[:TOP_N]

    if "long_short" in strategy:
        losers = ranking[-TOP_N:]
        weights = {
            symbol: 0.0
            for symbol in ASSETS
        }
        for symbol in winners:
            weights[symbol] = 0.5 / TOP_N
        for symbol in losers:
            weights[symbol] = -0.5 / TOP_N
        return weights

    return {
        symbol: (
            1.0 / TOP_N
            if symbol in winners
            else 0.0
        )
        for symbol in ASSETS
    }


def daily_returns(
    assets: dict[str, tuple[Bar, ...]],
    strategy: str,
) -> list[float]:
    length = min(len(bars) for bars in assets.values())
    if length < 3:
        return []

    previous = {
        symbol: 0.0
        for symbol in ASSETS
    }
    current_weights = {
        symbol: 0.0
        for symbol in ASSETS
    }
    returns = []

    for decision_index in range(length - 2):
        if (
            strategy == "equal_weight_buy_and_hold"
            or decision_index % REBALANCE_DAYS == 0
        ):
            current_weights = target_weights(
                assets,
                strategy,
                decision_index,
            )

        portfolio_return = 0.0
        turnover = 0.0

        for symbol in ASSETS:
            target = current_weights[symbol]
            bars = assets[symbol]

            market_return = (
                bars[decision_index + 2].open
                / bars[decision_index + 1].open
                - 1.0
            )

            portfolio_return += (
                target * market_return
            )
            turnover += abs(
                target - previous[symbol]
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


def rolling_stats(
    returns: list[float],
) -> list[dict]:
    windows = (
        (300, 400),
        (400, 500),
        (500, 600),
        (600, 700),
        (700, 800),
    )

    return [
        {
            "window_index": index,
            "start_index": start,
            "end_index": end,
            **_stats(returns, start, end),
        }
        for index, (start, end) in enumerate(
            windows,
            start=1,
        )
    ]


def run_control(
    data_dir: Path,
    manifest_path: Path,
    output_path: Path,
) -> dict:
    assets, manifest = load_assets(
        data_dir,
        manifest_path,
    )

    strategies = {}
    for strategy in STRATEGIES:
        returns = daily_returns(
            assets,
            strategy,
        )
        rolling = rolling_stats(returns)
        strategies[strategy] = {
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
        "diagnostic_type": "cross_sectional_momentum_control",
        "status": "COMPLETED",
        "source": {
            "universe": UNIVERSE,
            "assets": list(ASSETS),
            "target_count": TARGET_COUNT,
            "research_candle_count": RESEARCH_COUNT,
            "holdout_candle_count": HOLDOUT_COUNT,
            "manifest_fingerprint": manifest["manifest_fingerprint"],
            "source_run_id": manifest.get(
                "provenance",
                {},
            ).get("run_id"),
        },
        "methodology": {
            "strategies": list(STRATEGIES),
            "formation_windows": ["6-1", "12-1"],
            "skip_sessions": SKIP,
            "rebalance_sessions": REBALANCE_DAYS,
            "top_n": TOP_N,
            "long_short_gross_exposure": 1.0,
            "optimization_used": False,
            "selection_profile_used": False,
            "execution": (
                "decision_at_close_t_then_next_session_open_to_following_open"
            ),
            "fee_rate": FEE_RATE,
            "slippage_rate": SLIPPAGE_RATE,
            "holdout_is_blind_to_selection": True,
            "exploratory_small_sample": True,
        },
        "strategies": strategies,
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

    print("CROSS_SECTIONAL_MOMENTUM_STATUS:", report["status"])
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
