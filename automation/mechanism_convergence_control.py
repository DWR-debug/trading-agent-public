"""Fixed convergence control for two independently replicated mechanisms.

Mechanisms:
1) cross-asset SMA 50/200 inverse-volatility trend sleeve
2) 12-1 cross-sectional momentum top-2 long-only sleeve

The only new portfolio hypothesis is an equal 50/50 capital combination of
these two already independently replicated mechanisms.

No optimization, selection profiles, gate changes or production integration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean
from math import sqrt

from automation.cross_asset_trend_replication import (
    _build_weight_path,
    _daily_returns as trend_daily_returns,
    _load_assets as load_trend_assets,
    _load_manifest as load_trend_manifest,
)
from automation.cross_sectional_momentum_replication import (
    daily_returns as cs_daily_returns,
    load_assets as load_cs_assets,
)


RESEARCH_SHARE = 0.80
STRESS_MULTIPLIER = 2.0

TREND_STRATEGY = "sma_50_200_inverse_vol"
CS_STRATEGY = "cs_momentum_252_long_only_top2"

STRATEGIES = (
    "trend_sma_50_200",
    "cs_momentum_12_1",
    "equal_50_50_convergence",
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


def _returns_by_timestamp(
    bars: tuple,
    returns: list[float],
) -> dict:
    if len(returns) != len(bars) - 2:
        raise ValueError(
            f"Return-/Bar-Länge passt nicht: {len(returns)} vs {len(bars)}"
        )

    return {
        bars[index + 2].timestamp: value
        for index, value in enumerate(returns)
    }


def _align(
    trend_bars: tuple,
    trend_returns: list[float],
    cs_bars: tuple,
    cs_returns: list[float],
) -> tuple[tuple, list[float], list[float]]:
    trend_map = _returns_by_timestamp(
        trend_bars,
        trend_returns,
    )
    cs_map = _returns_by_timestamp(
        cs_bars,
        cs_returns,
    )

    common = tuple(
        sorted(
            set(trend_map).intersection(cs_map)
        )
    )

    if len(common) < 500:
        raise ValueError(
            f"Zu wenig gemeinsamer Return-Zeitraum: {len(common)}"
        )

    return (
        common,
        [trend_map[timestamp] for timestamp in common],
        [cs_map[timestamp] for timestamp in common],
    )


def _stats(
    returns: list[float],
) -> dict:
    if not returns:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "positive_day_ratio": 0.0,
            "day_count": 0,
            "mean_daily_return": 0.0,
        }

    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    positive = 0

    for value in returns:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_drawdown = max(
            max_drawdown,
            1.0 - equity / peak,
        )

        if value > 0:
            gross_profit += value
            positive += 1
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
        "positive_day_ratio": positive / len(returns),
        "day_count": len(returns),
        "mean_daily_return": mean(returns),
    }


def _rolling(
    returns: list[float],
    research_count: int,
) -> list[dict]:
    width = research_count // 5
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
            **_stats(
                returns[start:end]
            ),
        }
        for index, (start, end) in enumerate(
            windows,
            start=1,
        )
    ]


def _correlation(
    left: list[float],
    right: list[float],
) -> float:
    if len(left) != len(right) or len(left) < 2:
        return 0.0

    left_mean = mean(left)
    right_mean = mean(right)
    numerator = sum(
        (a - left_mean) * (b - right_mean)
        for a, b in zip(left, right)
    )
    left_var = sum(
        (a - left_mean) ** 2
        for a in left
    )
    right_var = sum(
        (b - right_mean) ** 2
        for b in right
    )

    denominator = sqrt(
        left_var * right_var
    )
    return (
        numerator / denominator
        if denominator > 0
        else 0.0
    )


def _stats_bundle(
    trend_returns: list[float],
    cs_returns: list[float],
) -> dict:
    combined = [
        0.5 * trend + 0.5 * cross_sectional
        for trend, cross_sectional
        in zip(trend_returns, cs_returns)
    ]

    length = len(combined)
    research_count = int(
        length * RESEARCH_SHARE
    )

    result = {}
    for name, values in (
        ("trend_sma_50_200", trend_returns),
        ("cs_momentum_12_1", cs_returns),
        ("equal_50_50_convergence", combined),
    ):
        research = values[:research_count]
        holdout = values[research_count:]

        result[name] = {
            "research": _stats(research),
            "holdout": _stats(holdout),
            "rolling": _rolling(
                research,
                len(research),
            ),
        }

    return {
        "strategies": result,
        "research_correlation": _correlation(
            trend_returns[:research_count],
            cs_returns[:research_count],
        ),
        "holdout_correlation": _correlation(
            trend_returns[research_count:],
            cs_returns[research_count:],
        ),
        "common_return_count": length,
        "research_return_count": research_count,
        "holdout_return_count": length - research_count,
    }


def run_control(
    trend_data_dir: Path,
    trend_manifest_path: Path,
    cs_data_dir: Path,
    cs_manifest_path: Path,
    output_path: Path,
) -> dict:
    trend_manifest = load_trend_manifest(
        trend_manifest_path,
    )
    trend_assets = load_trend_assets(
        trend_data_dir,
        trend_manifest,
    )
    cs_assets, cs_manifest = load_cs_assets(
        cs_data_dir,
        cs_manifest_path,
    )

    trend_anchor = next(iter(trend_assets.values()))
    cs_anchor = next(iter(cs_assets.values()))

    by_scenario = {}

    for scenario, multiplier in (
        ("base", 1.0),
        ("stress_2x_cost", STRESS_MULTIPLIER),
    ):
        trend_weights = _build_weight_path(
            trend_assets,
            TREND_STRATEGY,
        )
        trend_returns = trend_daily_returns(
            trend_assets,
            trend_weights,
            multiplier,
        )
        cs_returns = cs_daily_returns(
            cs_assets,
            CS_STRATEGY,
            multiplier,
        )

        timestamps, aligned_trend, aligned_cs = _align(
            trend_anchor,
            trend_returns,
            cs_anchor,
            cs_returns,
        )

        by_scenario[scenario] = {
            **_stats_bundle(
                aligned_trend,
                aligned_cs,
            ),
            "common_start": timestamps[0].isoformat(),
            "common_end": timestamps[-1].isoformat(),
        }

    report = {
        "diagnostic_type": "mechanism_convergence_control",
        "status": "COMPLETED",
        "source": {
            "trend_universe": trend_manifest["universe"],
            "trend_manifest_fingerprint": trend_manifest["manifest_fingerprint"],
            "trend_source_run_id": trend_manifest.get(
                "provenance",
                {},
            ).get("run_id"),
            "cs_universe": cs_manifest["universe"],
            "cs_manifest_fingerprint": cs_manifest["manifest_fingerprint"],
            "cs_source_run_id": cs_manifest.get(
                "provenance",
                {},
            ).get("run_id"),
        },
        "methodology": {
            "hypothesis": (
                "equal 50/50 capital combination of two independently "
                "replicated mechanisms"
            ),
            "trend_mechanism": TREND_STRATEGY,
            "cross_sectional_mechanism": CS_STRATEGY,
            "portfolio_weighting": "fixed 50/50 sleeve weighting",
            "optimization_used": False,
            "selection_profile_used": False,
            "execution_semantics": (
                "each sleeve uses decision_at_close_t_then_next_open_to_following_open"
            ),
            "base_cost_model": "each sleeve carries its own fixed costs",
            "cost_stress_multiplier": STRESS_MULTIPLIER,
            "research_share": RESEARCH_SHARE,
            "holdout_is_blind_to_selection": True,
            "no_new_signal_tuning": True,
        },
        "scenarios": by_scenario,
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
    parser.add_argument("--trend-data-dir", required=True)
    parser.add_argument("--trend-manifest", required=True)
    parser.add_argument("--cs-data-dir", required=True)
    parser.add_argument("--cs-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_control(
        Path(args.trend_data_dir),
        Path(args.trend_manifest),
        Path(args.cs_data_dir),
        Path(args.cs_manifest),
        Path(args.output),
    )

    print(
        "MECHANISM_CONVERGENCE_STATUS:",
        report["status"],
    )
    print(
        "REPORT_FINGERPRINT:",
        report["report_fingerprint"],
    )

    for scenario, bundle in report["scenarios"].items():
        print(
            scenario,
            "RESEARCH_CORR=",
            bundle["research_correlation"],
            "HOLDOUT_CORR=",
            bundle["holdout_correlation"],
        )
        for strategy, values in bundle["strategies"].items():
            print(
                strategy,
                "HOLDOUT_RETURN=",
                values["holdout"]["period_return"],
                "HOLDOUT_DD=",
                values["holdout"]["max_drawdown_percent"],
                "HOLDOUT_PF=",
                values["holdout"]["profit_factor"],
                "ROLLING_POSITIVE_RATIO=",
                mean(
                    item["period_return"] > 0
                    for item in values["rolling"]
                ),
            )


if __name__ == "__main__":
    main()
