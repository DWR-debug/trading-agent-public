"""Independent European trend-family control.

Uses the already defined european_volatile research universe and mechanically
pre-registered trend rules. Data is prepared by automation.prepare_research_data
at workflow runtime and fingerprinted in a manifest.

This is validation research only:
- no optimization
- no selection profiles
- no production strategy changes
- no live orders

Families:
- buy_and_hold reference
- TSM ensemble 63/126/252
- SMA 50/200 long/flat
- Donchian 55/20
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from automation.literature_strategy_lab import (
    atr_percent_series,
    build_exposure,
    generate_signal,
    load_bars,
)


STRATEGIES = (
    "buy_and_hold",
    "tsm_ensemble",
    "sma_50_200_long_flat",
    "donchian_55_20",
)

TARGET_COUNT = 2500
HOLDOUT_COUNT = 500
RESEARCH_COUNT = TARGET_COUNT - HOLDOUT_COUNT

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_PER_SIDE = FEE_RATE + SLIPPAGE_RATE


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


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("universe") != "european_volatile":
        raise ValueError("Unerwartetes Forschungsuniversum.")
    return manifest


def load_assets(
    data_dir: Path,
    manifest: dict,
) -> tuple[dict, tuple[str, ...]]:
    datasets = manifest.get("datasets", [])
    symbols = tuple(item["symbol"] for item in datasets)

    if len(symbols) != 4:
        raise ValueError(
            f"Erwartet 4 Europa-Datensätze, gefunden: {symbols}"
        )

    assets = {}
    for item in datasets:
        symbol = item["symbol"]
        expected_count = item["candle_count"]
        if expected_count < 1000:
            raise ValueError(
                f"{symbol}: zu wenig Historie ({expected_count})."
            )

        bars = load_bars(
            data_dir / symbol / "1d.csv",
            expected_count=expected_count,
        )
        if len(bars) != expected_count:
            raise ValueError(
                f"{symbol}: Manifest count {expected_count}, "
                f"Datei count {len(bars)}."
            )

        from automation.literature_strategy_lab import dataset_fingerprint

        actual = dataset_fingerprint(bars)
        if actual != item["fingerprint"]:
            raise ValueError(
                f"{symbol}: Dataset-Fingerprint stimmt nicht."
            )
        assets[symbol] = bars

    common_count = min(len(bars) for bars in assets.values())
    if common_count < TARGET_COUNT:
        raise ValueError(
            f"Gemeinsame Historie nur {common_count}, erwartet mindestens "
            f"{TARGET_COUNT}."
        )

    return assets, tuple(symbols)


def _strategy_exposure(
    bars,
    strategy: str,
) -> list[float]:
    if strategy == "buy_and_hold":
        return [1.0] * len(bars)

    signal = generate_signal(
        bars,
        strategy,
    )
    return build_exposure(
        bars,
        signal,
    )


def _daily_returns(
    assets: dict,
    strategy: str,
) -> tuple[list[float], float]:
    length = min(len(bars) for bars in assets.values())
    exposures = {
        symbol: _strategy_exposure(
            bars,
            strategy,
        )
        for symbol, bars in assets.items()
    }

    previous = {
        symbol: 0.0
        for symbol in assets
    }
    returns = []
    turnover_total = 0.0

    for decision_index in range(length - 2):
        portfolio_return = 0.0
        turnover = 0.0

        for symbol, bars in assets.items():
            target = exposures[symbol][decision_index]

            market_return = (
                bars[decision_index + 2].open
                / bars[decision_index + 1].open
                - 1.0
            )

            weight = 1.0 / len(assets)
            portfolio_return += weight * target * market_return

            turnover += weight * abs(
                target - previous[symbol]
            )
            previous[symbol] = target

        turnover_total += turnover
        returns.append(
            portfolio_return
            - COST_PER_SIDE * turnover
        )

    return returns, turnover_total


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
    step = 400
    windows = (
        (400, 800),
        (800, 1200),
        (1200, 1600),
        (1600, 2000),
        (2000, 2400),
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
    manifest = load_manifest(manifest_path)
    assets, symbols = load_assets(
        data_dir,
        manifest,
    )

    results = {}
    for strategy in STRATEGIES:
        returns, turnover = _daily_returns(
            assets,
            strategy,
        )
        rolling = _rolling(returns)
        results[strategy] = {
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
            "total_turnover": turnover,
        }

    report = {
        "diagnostic_type": "independent_european_trend_control",
        "status": "COMPLETED",
        "source": {
            "universe": "european_volatile",
            "symbols": list(symbols),
            "target_count": TARGET_COUNT,
            "research_candle_count": RESEARCH_COUNT,
            "holdout_candle_count": HOLDOUT_COUNT,
            "manifest_fingerprint": manifest["manifest_fingerprint"],
            "generated_at": manifest["generated_at"],
        },
        "methodology": {
            "strategies": list(STRATEGIES),
            "optimization_used": False,
            "selection_profile_used": False,
            "holdout_is_blind_to_selection": True,
            "equal_capital_weight": True,
            "execution": (
                "decision_at_close_t_then_next_session_open_to_following_open"
            ),
            "fee_rate": FEE_RATE,
            "slippage_rate": SLIPPAGE_RATE,
            "fixed_rules": True,
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

    print("EUROPEAN_TREND_STATUS:", report["status"])
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
