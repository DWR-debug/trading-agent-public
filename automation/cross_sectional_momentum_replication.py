"""Independent replication of the pre-registered 12-1 cross-sectional momentum rule.

Primary replication hypothesis from the small-cap control:
- 12-month formation proxy: 252 trading sessions
- skip the most recent 21 sessions
- monthly rebalance every 21 sessions
- buy the top 2 of 5 assets, equal-weighted
- no short positions
- point-in-time: close(t) decision -> next open execution
- fixed base costs and 2x cost stress
- no optimization, no selection profiles
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from backtesting.models import Candle
from research.protocol import dataset_fingerprint as protocol_dataset_fingerprint
from research.asset_universes import get_universe


UNIVERSE = "liquid_high_volatility"
ASSETS = ("NVDA", "AMD", "TSLA", "COIN", "PLTR")

TARGET_COUNT = 1300
RESEARCH_COUNT = 1040
HOLDOUT_COUNT = 260

LOOKBACK = 252
SKIP = 21
REBALANCE_DAYS = 21
TOP_N = 2

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_MULTIPLIERS = (
    ("base", 1.0),
    ("stress_2x_cost", 2.0),
)

STRATEGIES = (
    "cs_momentum_252_long_only_top2",
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
    import csv

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

    universe = get_universe(UNIVERSE)
    expected_assets = tuple(universe.symbols)

    if tuple(expected_assets) != ASSETS:
        raise ValueError(
            "Universe-Symbolsatz und Replications-Symbolsatz weichen ab."
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

    first_timestamps = {
        bars[0].timestamp
        for bars in assets.values()
    }
    last_timestamps = {
        bars[-1].timestamp
        for bars in assets.values()
    }
    if len(first_timestamps) != 1 or len(last_timestamps) != 1:
        raise ValueError(
            "Asset-Zeitachsen haben unterschiedliche Start-/Endpunkte."
        )

    return assets, manifest


def _ranking(
    assets: dict[str, tuple[Bar, ...]],
    decision_index: int,
) -> list[str]:
    if decision_index < LOOKBACK + SKIP:
        return []

    scores = {}
    for symbol, bars in assets.items():
        anchor = decision_index - SKIP
        origin = anchor - LOOKBACK
        scores[symbol] = (
            bars[anchor].close
            / bars[origin].close
            - 1.0
        )

    return sorted(
        scores,
        key=scores.get,
        reverse=True,
    )


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

    if strategy != "cs_momentum_252_long_only_top2":
        raise ValueError(f"Unbekannte Strategie: {strategy}")

    ranking = _ranking(
        assets,
        decision_index,
    )

    if not ranking:
        return {
            symbol: 0.0
            for symbol in ASSETS
        }

    winners = set(ranking[:TOP_N])
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
    cost_multiplier: float,
) -> list[float]:
    length = min(
        len(bars)
        for bars in assets.values()
    )

    previous = {
        symbol: 0.0
        for symbol in ASSETS
    }
    current = {
        symbol: 0.0
        for symbol in ASSETS
    }

    cost_per_side = (
        FEE_RATE + SLIPPAGE_RATE
    ) * cost_multiplier

    returns = []

    for decision_index in range(length - 2):
        if (
            strategy == "equal_weight_buy_and_hold"
            or decision_index % REBALANCE_DAYS == 0
        ):
            current = target_weights(
                assets,
                strategy,
                decision_index,
            )

        portfolio_return = 0.0
        turnover = 0.0

        for symbol in ASSETS:
            target = current[symbol]
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
            - cost_per_side * turnover
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


def _rolling(
    returns: list[float],
) -> list[dict]:
    width = RESEARCH_COUNT // 5
    windows = tuple(
        (
            index * width,
            (index + 1) * width,
        )
        for index in range(5)
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
        strategies[strategy] = {}

        for scenario, multiplier in COST_MULTIPLIERS:
            returns = daily_returns(
                assets,
                strategy,
                multiplier,
            )
            rolling = _rolling(returns)

            strategies[strategy][scenario] = {
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
        "diagnostic_type": (
            "cross_sectional_momentum_independent_replication"
        ),
        "status": "COMPLETED",
        "source": {
            "universe": UNIVERSE,
            "assets": list(ASSETS),
            "target_count": TARGET_COUNT,
            "research_candle_count": RESEARCH_COUNT,
            "holdout_candle_count": HOLDOUT_COUNT,
            "manifest_fingerprint": manifest[
                "manifest_fingerprint"
            ],
            "source_run_id": manifest.get(
                "provenance",
                {},
            ).get("run_id"),
        },
        "methodology": {
            "primary_rule": (
                "12-1 cross-sectional momentum, top-2 long-only"
            ),
            "formation_window_sessions": LOOKBACK,
            "skip_sessions": SKIP,
            "rebalance_sessions": REBALANCE_DAYS,
            "top_n": TOP_N,
            "optimization_used": False,
            "selection_profile_used": False,
            "execution": (
                "decision_at_close_t_then_next_session_open_to_following_open"
            ),
            "fee_rate": FEE_RATE,
            "slippage_rate": SLIPPAGE_RATE,
            "cost_stress_multiplier": 2.0,
            "holdout_is_blind_to_selection": True,
            "independent_universe": True,
        },
        "strategies": strategies,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }

    report["report_fingerprint"] = _fingerprint(report)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
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

    print(
        "CS_MOMENTUM_REPLICATION_STATUS:",
        report["status"],
    )
    print(
        "REPORT_FINGERPRINT:",
        report["report_fingerprint"],
    )

    for strategy, scenarios in report["strategies"].items():
        for scenario, result in scenarios.items():
            print(
                strategy,
                scenario,
                "HOLDOUT_RETURN=",
                result["holdout"]["period_return"],
                "HOLDOUT_DD=",
                result["holdout"]["max_drawdown_percent"],
                "HOLDOUT_PF=",
                result["holdout"]["profit_factor"],
                "ROLLING_POSITIVE_RATIO=",
                result["rolling_positive_window_ratio"],
            )


if __name__ == "__main__":
    main()
