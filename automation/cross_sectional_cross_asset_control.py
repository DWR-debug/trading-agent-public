"""Cross-sectional 12-1 momentum control on the same cross-asset universe as TSM.

Diagnostic only:
- universe: SPY, EFA, TLT, GLD, DBC, UUP, QQQ, IWM
- 12-1 formation (252 sessions), 21-session skip
- rebalance every 21 sessions
- long-only top-2 equal weight
- same point-in-time open-to-open execution used in prior controls
- base + 2x cost stress
- no optimization, no selection profile, no gate changes
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from automation.cross_asset_trend_replication import (
    _load_manifest,
    _load_assets,
)
from automation.cross_sectional_momentum_replication import (
    _stats,
)

UNIVERSE = "cross_asset_trend"
ASSETS = ("SPY", "EFA", "TLT", "GLD", "DBC", "UUP", "QQQ", "IWM")

TARGET_COUNT = 3500
RESEARCH_COUNT = 2800
HOLDOUT_COUNT = 700

LOOKBACK = 252
SKIP = 21
REBALANCE_DAYS = 21
TOP_N = 2

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005

STRATEGIES = (
    "cs_momentum_252_long_only_top2",
    "tsm_sma_reference",
    "equal_weight_buy_and_hold",
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


def _load_cross_asset_assets(
    data_dir: Path,
    manifest_path: Path,
) -> tuple[dict[str, tuple], dict]:
    manifest = _load_manifest(manifest_path)
    assets = _load_assets(
        data_dir,
        manifest,
    )

    if tuple(assets) != ASSETS:
        raise ValueError(
            f"Unerwartete Cross-Asset-Reihenfolge: {tuple(assets)}"
        )

    if len(next(iter(assets.values()))) != TARGET_COUNT:
        raise ValueError("Unerwartete gemeinsame Zielhistorie.")

    return assets, manifest


def _ranking(
    assets: dict[str, tuple],
    decision_index: int,
) -> list[str]:
    anchor = decision_index - SKIP
    origin = anchor - LOOKBACK

    if origin < 0:
        return []

    scores = {}
    for symbol, bars in assets.items():
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


def _weights(
    assets: dict[str, tuple],
    strategy: str,
    decision_index: int,
) -> dict[str, float]:
    if strategy == "equal_weight_buy_and_hold":
        return {
            symbol: 1.0 / len(ASSETS)
            for symbol in ASSETS
        }

    ranking = _ranking(
        assets,
        decision_index,
    )

    if not ranking:
        return {
            symbol: 0.0
            for symbol in ASSETS
        }

    if strategy == "cs_momentum_252_long_only_top2":
        winners = set(ranking[:TOP_N])
        return {
            symbol: (
                1.0 / TOP_N
                if symbol in winners
                else 0.0
            )
            for symbol in ASSETS
        }

    if strategy == "tsm_sma_reference":
        # Fixed 50/200 long/flat reference derived from the already tested
        # cross-asset trend family, without re-optimizing it here.
        weights = {}
        for symbol, bars in assets.items():
            if decision_index < 199:
                weights[symbol] = 0.0
                continue
            fast = sum(
                bars[index].close
                for index in range(
                    decision_index - 49,
                    decision_index + 1,
                )
            ) / 50.0
            slow = sum(
                bars[index].close
                for index in range(
                    decision_index - 199,
                    decision_index + 1,
                )
            ) / 200.0
            weights[symbol] = 1.0 / len(ASSETS) if fast > slow else 0.0
        return weights

    raise ValueError(f"Unbekannte Strategie: {strategy}")


def _daily_returns(
    assets: dict[str, tuple],
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
            current = _weights(
                assets,
                strategy,
                decision_index,
            )

            if strategy == "tsm_sma_reference":
                total = sum(
                    abs(value)
                    for value in current.values()
                )
                if total > 0:
                    current = {
                        symbol: value / total
                        for symbol, value in current.items()
                    }

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


def _rolling(
    returns: list[float],
) -> list[dict]:
    width = RESEARCH_COUNT // 5
    return [
        {
            "window_index": index,
            **_stats(
                returns,
                start,
                end,
            ),
        }
        for index, (start, end) in enumerate(
            (
                (0, width),
                (width, width * 2),
                (width * 2, width * 3),
                (width * 3, width * 4),
                (width * 4, RESEARCH_COUNT),
            ),
            start=1,
        )
    ]


def run_control(
    data_dir: Path,
    manifest_path: Path,
    output_path: Path,
) -> dict:
    assets, manifest = _load_cross_asset_assets(
        data_dir,
        manifest_path,
    )

    strategies = {}

    for strategy in STRATEGIES:
        strategies[strategy] = {}

        for scenario, multiplier in (
            ("base", 1.0),
            ("stress_2x_cost", 2.0),
        ):
            returns = _daily_returns(
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
            "cross_sectional_momentum_same_universe_control"
        ),
        "status": "COMPLETED",
        "source": {
            "universe": manifest["universe"],
            "symbols": list(ASSETS),
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
            "primary_rule": "12-1 cross-sectional momentum, top-2 long-only",
            "formation_sessions": LOOKBACK,
            "skip_sessions": SKIP,
            "rebalance_sessions": REBALANCE_DAYS,
            "top_n": TOP_N,
            "optimization_used": False,
            "selection_profile_used": False,
            "same_universe_as_time_series_trend": True,
            "execution": (
                "decision_at_close_t_then_next_session_open_to_following_open"
            ),
            "fee_rate": FEE_RATE,
            "slippage_rate": SLIPPAGE_RATE,
            "cost_stress_multiplier": 2.0,
            "holdout_is_blind_to_selection": True,
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
        "CS_CROSS_ASSET_STATUS:",
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
