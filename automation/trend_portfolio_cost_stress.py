"""Fixed transaction-cost stress control for trend portfolios.

This control replays the same deterministic trend portfolio rules under two
pre-registered cost scenarios:
- base: 0.10% fee + 0.05% slippage per unit turnover
- stress: exactly 2x the base cost

No optimization, selection profiles, or gate changes are performed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from automation.risk_normalized_trend_portfolio_control import (
    ASSETS,
    _signal_by_strategy,
    _target_weights,
)
from automation.literature_strategy_lab import (
    RESEARCH_COUNT,
    TARGET_COUNT,
    dataset_fingerprint,
    load_bars,
)

BASE_FEE_RATE = 0.001
BASE_SLIPPAGE_RATE = 0.0005
STRESS_MULTIPLIER = 2.0

STRATEGIES = (
    "tsm_ensemble_risk_normalized",
    "sma_50_200_risk_normalized",
)

SCENARIOS = (
    ("base", BASE_FEE_RATE + BASE_SLIPPAGE_RATE),
    (
        "stress_2x_cost",
        (BASE_FEE_RATE + BASE_SLIPPAGE_RATE) * STRESS_MULTIPLIER,
    ),
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
        bars = load_bars(data_dir / symbol / "1d.csv")
        if dataset_fingerprint(bars) != expected[symbol]["fingerprint"]:
            raise ValueError(
                f"{symbol}: Dataset-Fingerprint stimmt nicht mit dem Archiv überein."
            )
        assets[symbol] = bars

    return manifest, assets


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


def _daily_returns(
    assets: dict,
    strategy: str,
    cost_per_turnover: float,
) -> tuple[list[float], float]:
    length = min(
        len(bars)
        for bars in assets.values()
    )
    signals = {
        symbol: _signal_by_strategy(
            bars,
            strategy,
        )
        for symbol, bars in assets.items()
    }
    previous = {
        symbol: 0.0
        for symbol in ASSETS
    }

    returns = []
    total_turnover = 0.0

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
            bars = assets[symbol]
            market_return = (
                bars[decision_index + 2].open
                / bars[decision_index + 1].open
                - 1.0
            )

            portfolio_return += target * market_return
            turnover += abs(
                target - previous[symbol]
            )
            previous[symbol] = target

        total_turnover += turnover
        returns.append(
            portfolio_return
            - cost_per_turnover * turnover
        )

    return returns, total_turnover


def run_control(
    data_dir: Path,
    manifest_path: Path,
    output_path: Path,
) -> dict:
    manifest, assets = _verify_assets(
        data_dir,
        manifest_path,
    )

    results = {}
    for strategy in STRATEGIES:
        scenarios = {}

        for scenario_name, cost in SCENARIOS:
            returns, total_turnover = _daily_returns(
                assets,
                strategy,
                cost,
            )
            rolling = [
                {
                    "window_index": index,
                    "start_index": start,
                    "end_index": end,
                    **_stats(returns, start, end),
                }
                for index, (start, end) in enumerate(
                    (
                        (2250, 2700),
                        (2700, 3150),
                        (3150, 3600),
                        (3600, 4050),
                        (4050, 4500),
                    ),
                    start=1,
                )
            ]

            scenarios[scenario_name] = {
                "cost_per_turnover": cost,
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
                "total_turnover": total_turnover,
            }

        results[strategy] = scenarios

    report = {
        "diagnostic_type": "trend_portfolio_cost_stress_control",
        "status": "COMPLETED",
        "source": {
            "target_count": TARGET_COUNT,
            "research_candle_count": RESEARCH_COUNT,
            "holdout_candle_count": TARGET_COUNT - RESEARCH_COUNT,
            "manifest_fingerprint": manifest.get("manifest_fingerprint"),
            "manifest_run_id": manifest.get(
                "provenance",
                {},
            ).get("run_id"),
        },
        "methodology": {
            "assets": list(ASSETS),
            "strategies": list(STRATEGIES),
            "scenarios": [name for name, _ in SCENARIOS],
            "stress_multiplier": STRESS_MULTIPLIER,
            "optimization_used": False,
            "selection_profile_used": False,
            "holdout_is_blind_to_selection": True,
            "execution": (
                "decision_at_close_t_then_next_session_open_to_following_open"
            ),
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

    print("COST_STRESS_STATUS:", report["status"])
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])
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
                "TOTAL_TURNOVER=",
                result["total_turnover"],
            )


if __name__ == "__main__":
    main()
