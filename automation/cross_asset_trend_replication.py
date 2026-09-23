"""Independent cross-asset trend-following replication control.

This is a research-only laboratory. It is deliberately separate from the
production strategy engine.

Design:
- 8 liquid ETF proxies spanning equities, fixed income, commodities/currency
- monthly rebalance
- point-in-time: close(t) decision -> next-session open execution
- TSM horizons: 1, 3 and 12 months approximated by 21/63/252 trading days
- fixed SMA 50/200 long/flat control
- fixed inverse-volatility allocation with 25% per-asset cap
- equal-weight and inverse-volatility variants
- base costs and a pre-registered 2x cost stress
- no optimization, no selection profiles, no gate changes
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from automation.literature_strategy_lab import (
    dataset_fingerprint,
    load_bars,
)
from research.asset_universes import get_universe


RESEARCH_SHARE = 0.80
HOLDOUT_SHARE = 0.20

LOOKBACKS = (21, 63, 252)
VOL_WINDOW = 60
MAX_ASSET_WEIGHT = 0.25

BASE_FEE = 0.001
BASE_SLIPPAGE = 0.0005
STRESS_MULTIPLIER = 2.0

STRATEGIES = (
    "buy_and_hold_equal",
    "tsm_monthly_equal",
    "tsm_monthly_inverse_vol",
    "sma_50_200_inverse_vol",
    "blend_tsm_sma_inverse_vol",
)

COST_SCENARIOS = (
    ("base", 1.0),
    ("stress_2x_cost", STRESS_MULTIPLIER),
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


def _load_manifest(path: Path) -> dict:
    manifest = json.loads(
        path.read_text(encoding="utf-8")
    )

    universe = get_universe("cross_asset_trend")
    symbols = tuple(universe.symbols)

    if manifest.get("universe") != universe.name:
        raise ValueError("Unerwartetes Cross-Asset-Forschungsuniversum.")

    expected_symbols = tuple(
        item["symbol"]
        for item in manifest.get("datasets", [])
    )
    if expected_symbols != symbols:
        raise ValueError(
            f"Manifest-Symbole weichen ab: {expected_symbols}"
        )

    if manifest.get("source") != "yahoo_chart":
        raise ValueError("Unerwartete Datenquelle.")

    if manifest.get("target_count") != universe.target_count:
        raise ValueError("Unerwartete Zielhistorie.")

    return manifest


def _load_assets(
    data_dir: Path,
    manifest: dict,
) -> dict[str, tuple]:
    assets = {}

    for item in manifest["datasets"]:
        symbol = item["symbol"]
        expected_count = item["candle_count"]
        bars = load_bars(
            data_dir / symbol / "1d.csv",
            expected_count=expected_count,
        )

        if len(bars) != expected_count:
            raise ValueError(
                f"{symbol}: Manifest/Data Count passt nicht."
            )

        actual = dataset_fingerprint(bars)
        if actual != item["fingerprint"]:
            raise ValueError(
                f"{symbol}: Dataset-Fingerprint stimmt nicht."
            )

        assets[symbol] = bars

    common_timestamps = set.intersection(
        *[
            {bar.timestamp for bar in bars}
            for bars in assets.values()
        ]
    )

    if len(common_timestamps) < 3000:
        raise ValueError(
            f"Zu wenige gemeinsame Handelstage: {len(common_timestamps)}"
        )

    common = sorted(common_timestamps)

    aligned: dict[str, tuple] = {}
    for symbol, bars in assets.items():
        by_timestamp = {
            bar.timestamp: bar
            for bar in bars
        }
        aligned[symbol] = tuple(
            by_timestamp[timestamp]
            for timestamp in common
        )

    return aligned


def _month_end_indices(bars: tuple) -> tuple[int, ...]:
    indices = []

    previous_key = None
    previous_index = None

    for index, bar in enumerate(bars):
        key = (bar.timestamp.year, bar.timestamp.month)
        if previous_key is not None and key != previous_key:
            indices.append(previous_index)

        previous_key = key
        previous_index = index

    if previous_index is not None:
        indices.append(previous_index)

    return tuple(indices)


def _tsm_signal(
    closes: list[float],
    index: int,
) -> float:
    if index < max(LOOKBACKS):
        return 0.0

    votes = 0
    for lookback in LOOKBACKS:
        change = closes[index] / closes[index - lookback] - 1.0
        if change > 0:
            votes += 1
        elif change < 0:
            votes -= 1

    if votes > 0:
        return 1.0
    if votes < 0:
        return -1.0
    return 0.0


def _sma_signal(
    closes: list[float],
    index: int,
) -> float:
    if index < 199:
        return 0.0

    fast = sum(
        closes[index - 49:index + 1]
    ) / 50.0
    slow = sum(
        closes[index - 199:index + 1]
    ) / 200.0

    return 1.0 if fast > slow else 0.0


def _annualized_vol(
    closes: list[float],
    index: int,
) -> float:
    if index < VOL_WINDOW:
        return 0.0

    returns = []
    for cursor in range(
        index - VOL_WINDOW + 1,
        index + 1,
    ):
        previous = closes[cursor - 1]
        current = closes[cursor]
        if previous > 0:
            returns.append(current / previous - 1.0)

    if len(returns) < VOL_WINDOW // 2:
        return 0.0

    mean = sum(returns) / len(returns)
    variance = sum(
        (value - mean) ** 2
        for value in returns
    ) / len(returns)

    return math.sqrt(variance) * math.sqrt(252.0)


def _inverse_vol_weights(
    signals: dict[str, float],
    vols: dict[str, float],
) -> dict[str, float]:
    active = {
        symbol
        for symbol, signal in signals.items()
        if signal != 0.0 and vols.get(symbol, 0.0) > 0.0
    }

    fixed: dict[str, float] = {}
    remaining = 1.0

    while active and remaining > 1e-12:
        raw = {
            symbol: signals[symbol] / vols[symbol]
            for symbol in active
        }
        denominator = sum(
            abs(value)
            for value in raw.values()
        )

        if denominator <= 0:
            break

        proposals = {
            symbol: raw[symbol] / denominator * remaining
            for symbol in active
        }

        capped = {
            symbol
            for symbol, value in proposals.items()
            if abs(value) > MAX_ASSET_WEIGHT
        }

        if not capped:
            fixed.update(proposals)
            remaining = 0.0
            break

        for symbol in capped:
            fixed[symbol] = (
                MAX_ASSET_WEIGHT
                if proposals[symbol] > 0
                else -MAX_ASSET_WEIGHT
            )
            remaining -= MAX_ASSET_WEIGHT
            active.remove(symbol)

    return {
        symbol: fixed.get(symbol, 0.0)
        for symbol in signals
    }


def _weights_at_rebalance(
    assets: dict[str, tuple],
    strategy: str,
    index: int,
) -> dict[str, float]:
    symbols = tuple(assets)

    if strategy == "buy_and_hold_equal":
        return {
            symbol: 1.0 / len(symbols)
            for symbol in symbols
        }

    closes = {
        symbol: [
            bar.close
            for bar in bars
        ]
        for symbol, bars in assets.items()
    }

    tsm = {
        symbol: _tsm_signal(
            closes[symbol],
            index,
        )
        for symbol in symbols
    }

    sma = {
        symbol: _sma_signal(
            closes[symbol],
            index,
        )
        for symbol in symbols
    }

    if strategy == "tsm_monthly_equal":
        active = [
            symbol
            for symbol in symbols
            if tsm[symbol] != 0.0
        ]
        if not active:
            return {
                symbol: 0.0
                for symbol in symbols
            }
        return {
            symbol: (
                tsm[symbol] / len(active)
                if symbol in active
                else 0.0
            )
            for symbol in symbols
        }

    if strategy == "tsm_monthly_inverse_vol":
        signals = tsm
    elif strategy == "sma_50_200_inverse_vol":
        signals = sma
    elif strategy == "blend_tsm_sma_inverse_vol":
        signals = {
            symbol: (
                tsm[symbol] + sma[symbol]
            ) / 2.0
            for symbol in symbols
        }
    else:
        raise ValueError(
            f"Unbekannte Strategie: {strategy}"
        )

    vols = {
        symbol: _annualized_vol(
            closes[symbol],
            index,
        )
        for symbol in symbols
    }

    return _inverse_vol_weights(
        signals,
        vols,
    )


def _build_weight_path(
    assets: dict[str, tuple],
    strategy: str,
) -> tuple[dict[str, float], ...]:
    length = len(next(iter(assets.values())))
    month_ends = _month_end_indices(
        next(iter(assets.values()))
    )

    weights = [
        {
            symbol: 0.0
            for symbol in assets
        }
        for _ in range(length)
    ]

    current = {
        symbol: 0.0
        for symbol in assets
    }

    for index in range(length):
        if index in month_ends:
            candidate = _weights_at_rebalance(
                assets,
                strategy,
                index,
            )
            current = candidate

        weights[index] = dict(current)

    return tuple(weights)


def _daily_returns(
    assets: dict[str, tuple],
    weights: tuple[dict[str, float], ...],
    cost_multiplier: float,
) -> list[float]:
    length = len(next(iter(assets.values())))
    symbols = tuple(assets)

    cost_per_side = (
        BASE_FEE + BASE_SLIPPAGE
    ) * cost_multiplier

    previous = {
        symbol: 0.0
        for symbol in symbols
    }

    returns = []

    for decision_index in range(length - 2):
        portfolio_return = 0.0
        turnover = 0.0
        target = weights[decision_index]

        for symbol in symbols:
            bars = assets[symbol]
            market_return = (
                bars[decision_index + 2].open
                / bars[decision_index + 1].open
                - 1.0
            )

            target_weight = target[symbol]
            portfolio_return += (
                target_weight * market_return
            )

            turnover += abs(
                target_weight - previous[symbol]
            )
            previous[symbol] = target_weight

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


def _rolling(
    returns: list[float],
    research_count: int,
) -> list[dict]:
    width = research_count // 5
    windows = tuple(
        (
            index * width,
            research_count
            if index == 4
            else (index + 1) * width,
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


def _evaluate_strategy(
    assets: dict[str, tuple],
    strategy: str,
    research_count: int,
    target_count: int,
) -> dict:
    weights = _build_weight_path(
        assets,
        strategy,
    )

    by_cost = {}

    for scenario, multiplier in COST_SCENARIOS:
        returns = _daily_returns(
            assets,
            weights,
            multiplier,
        )

        rolling = _rolling(
            returns,
            research_count,
        )

        by_cost[scenario] = {
            "research": _stats(
                returns,
                0,
                research_count,
            ),
            "holdout": _stats(
                returns,
                research_count,
                target_count,
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
            "month_end_rebalance_count": sum(
                _month_end_indices(
                    next(iter(assets.values()))
                )[1:]
            )
            if False
            else len(
                _month_end_indices(
                    next(iter(assets.values()))
                )
            ),
            "gross_exposure_max": max(
                sum(abs(value) for value in weight.values())
                for weight in weights
            ),
            "gross_exposure_median": sorted(
                sum(abs(value) for value in weight.values())
                for weight in weights
            )[len(weights) // 2],
        }

    return by_cost


def run_control(
    data_dir: Path,
    manifest_path: Path,
    output_path: Path,
) -> dict:
    manifest = _load_manifest(manifest_path)
    assets = _load_assets(
        data_dir,
        manifest,
    )

    target_count = len(
        next(iter(assets.values()))
    )
    research_count = int(
        target_count * RESEARCH_SHARE
    )
    holdout_count = target_count - research_count

    strategies = {
        strategy: _evaluate_strategy(
            assets,
            strategy,
            research_count,
            target_count,
        )
        for strategy in STRATEGIES
    }

    report = {
        "diagnostic_type": "cross_asset_trend_replication",
        "status": "COMPLETED",
        "source": {
            "universe": manifest["universe"],
            "symbols": list(assets),
            "manifest_fingerprint": manifest[
                "manifest_fingerprint"
            ],
            "manifest_generated_at": manifest[
                "generated_at"
            ],
            "common_aligned_count": target_count,
            "research_candle_count": research_count,
            "holdout_candle_count": holdout_count,
        },
        "methodology": {
            "strategy_rules_are_pre_registered": True,
            "optimization_used": False,
            "selection_profile_used": False,
            "rebalance_frequency": "monthly",
            "tsm_lookbacks_trading_days": list(LOOKBACKS),
            "volatility_window": VOL_WINDOW,
            "inverse_vol_weight_cap": MAX_ASSET_WEIGHT,
            "portfolio_gross_target": 1.0,
            "execution": (
                "close_t_decision_then_next_open_execution_and_following_open_return"
            ),
            "base_fee": BASE_FEE,
            "base_slippage": BASE_SLIPPAGE,
            "stress_cost_multiplier": STRESS_MULTIPLIER,
            "holdout_is_blind_to_selection": True,
            "common_date_alignment": True,
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
        "CROSS_ASSET_TREND_STATUS:",
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
