"""Point-in-time volatility-budget control for the fixed 50/50 convergence sleeve.

Only one new hypothesis is tested:
- keep the already replicated 50/50 Trend + Cross-Sectional Momentum sleeve
- add a fixed 10% annualized realized-volatility cap
- scale down only (never lever up)
- use the prior 63 common daily returns for the estimate
- leave signals, sleeve weights, costs and execution unchanged

Diagnostic only. No production strategy, gate or selection rule changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from automation.cross_asset_trend_replication import (
    _build_weight_path,
    _load_assets as load_trend_assets,
    _load_manifest as load_trend_manifest,
)
from automation.cross_sectional_momentum_replication import (
    load_assets as load_cs_assets,
    target_weights as cs_target_weights,
)


TREND_STRATEGY = "sma_50_200_inverse_vol"
CS_STRATEGY = "cs_momentum_252_long_only_top2"

TARGET_VOL = 0.10
VOL_WINDOW = 63
MAX_SCALE = 1.0

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005

RESEARCH_SHARE = 0.80

SCENARIOS = (
    ("base", 1.0),
    ("stress_2x_cost", 2.0),
)

RESULTS = (
    "unscaled_baseline",
    "vol_budget_10pct",
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


def _build_cs_weight_path(
    assets: dict[str, tuple],
) -> tuple[dict[str, float], ...]:
    length = min(
        len(bars)
        for bars in assets.values()
    )

    current = {
        symbol: 0.0
        for symbol in assets
    }
    weights = []

    for decision_index in range(length):
        if decision_index % 21 == 0:
            current = cs_target_weights(
                assets,
                CS_STRATEGY,
                decision_index,
            )

        weights.append(dict(current))

    return tuple(weights)


def _returns_for_weight_path(
    assets: dict[str, tuple],
    weights: tuple[dict[str, float], ...],
) -> tuple[dict, ...]:
    length = min(
        len(bars)
        for bars in assets.values()
    )

    previous = {
        symbol: 0.0
        for symbol in assets
    }

    rows = []

    for decision_index in range(length - 2):
        gross_return = 0.0
        turnover = 0.0
        current = weights[decision_index]

        for symbol, asset_bars in assets.items():
            target = current.get(symbol, 0.0)
            market_return = (
                asset_bars[decision_index + 2].open
                / asset_bars[decision_index + 1].open
                - 1.0
            )
            gross_return += target * market_return
            turnover += abs(
                target - previous[symbol]
            )
            previous[symbol] = target

        rows.append(
            {
                "timestamp": next(
                    asset_bars[decision_index + 2].timestamp
                    for asset_bars in assets.values()
                ),
                "gross_return": gross_return,
                "turnover": turnover,
            }
        )

    return tuple(rows)


def _align_rows(
    trend_assets: dict[str, tuple],
    trend_weights: tuple[dict[str, float], ...],
    cs_assets: dict[str, tuple],
    cs_weights: tuple[dict[str, float], ...],
) -> tuple[dict, ...]:
    trend_rows = _returns_for_weight_path(
        trend_assets,
        trend_weights,
    )
    cs_rows = _returns_for_weight_path(
        cs_assets,
        cs_weights,
    )

    trend_map = {
        row["timestamp"]: row
        for row in trend_rows
    }
    cs_map = {
        row["timestamp"]: row
        for row in cs_rows
    }

    common = sorted(
        set(trend_map).intersection(cs_map)
    )

    if len(common) < 500:
        raise ValueError(
            f"Zu wenig gemeinsamer Zeitraum: {len(common)}"
        )

    rows = []
    for timestamp in common:
        trend = trend_map[timestamp]
        cs = cs_map[timestamp]

        rows.append(
            {
                "timestamp": timestamp,
                "trend_gross": 0.5 * trend["gross_return"],
                "trend_turnover": 0.5 * trend["turnover"],
                "cs_gross": 0.5 * cs["gross_return"],
                "cs_turnover": 0.5 * cs["turnover"],
            }
        )

    return tuple(rows)


def _rolling_vol(
    previous_returns: list[float],
) -> float | None:
    if len(previous_returns) < VOL_WINDOW:
        return None

    mean = sum(previous_returns[-VOL_WINDOW:]) / VOL_WINDOW
    variance = sum(
        (value - mean) ** 2
        for value in previous_returns[-VOL_WINDOW:]
    ) / VOL_WINDOW

    return math.sqrt(variance) * math.sqrt(252.0)


def _simulate(
    rows: tuple[dict, ...],
    cost_multiplier: float,
    use_vol_budget: bool,
) -> list[dict]:
    previous_combined_weight = {}
    previous_scale = 0.0
    unscaled_history: list[float] = []
    output = []

    for index, row in enumerate(rows):
        if use_vol_budget:
            realized_vol = _rolling_vol(
                unscaled_history
            )
            if realized_vol and realized_vol > TARGET_VOL:
                scale = min(
                    MAX_SCALE,
                    TARGET_VOL / realized_vol,
                )
            else:
                scale = MAX_SCALE
        else:
            scale = MAX_SCALE

        base_gross = (
            row["trend_gross"]
            + row["cs_gross"]
        )
        base_turnover = (
            row["trend_turnover"]
            + row["cs_turnover"]
        )

        gross_return = scale * base_gross

        # Scale both sleeves globally. The additional scale change is itself
        # a real portfolio turnover event; include it conservatively.
        turnover = (
            scale * base_turnover
            + abs(scale - previous_scale)
        )

        cost = (
            FEE_RATE + SLIPPAGE_RATE
        ) * cost_multiplier * turnover

        net_return = gross_return - cost

        output.append(
            {
                "timestamp": row["timestamp"],
                "scale": scale,
                "gross_return": gross_return,
                "turnover": turnover,
                "net_return": net_return,
                "realized_vol_estimate": _rolling_vol(
                    unscaled_history
                ),
            }
        )

        previous_scale = scale
        unscaled_history.append(
            base_gross
            - (
                FEE_RATE + SLIPPAGE_RATE
            ) * base_turnover
        )

    return output


def _stats(
    returns: list[dict],
    start: int,
    end: int,
) -> dict:
    segment = returns[start:end]
    values = [
        row["net_return"]
        for row in segment
    ]

    if not values:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "positive_day_ratio": 0.0,
            "day_count": 0,
            "realized_vol_annualized": 0.0,
            "median_scale": 0.0,
            "minimum_scale": 0.0,
        }

    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    positive = 0.0
    scales = []

    for row in segment:
        value = row["net_return"]
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

        scales.append(row["scale"])

    mean_value = sum(values) / len(values)
    variance = sum(
        (value - mean_value) ** 2
        for value in values
    ) / len(values)

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0
        else "inf"
        if gross_profit > 0
        else 0.0
    )

    ordered_scales = sorted(scales)

    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_drawdown * 100.0,
        "profit_factor": profit_factor,
        "positive_day_ratio": positive / len(values),
        "day_count": len(values),
        "realized_vol_annualized": math.sqrt(variance) * math.sqrt(252.0),
        "median_scale": ordered_scales[len(ordered_scales) // 2],
        "minimum_scale": min(scales),
    }


def _rolling(
    returns: list[dict],
    research_end: int,
) -> list[dict]:
    width = research_end // 5
    windows = (
        (0, width),
        (width, width * 2),
        (width * 2, width * 3),
        (width * 3, width * 4),
        (width * 4, research_end),
    )

    return [
        {
            "window_index": index,
            "start_index": start,
            "end_index": end,
            **_stats(
                returns,
                start,
                end,
            ),
        }
        for index, (start, end) in enumerate(
            windows,
            start=1,
        )
    ]


def run_control(
    trend_data_dir: Path,
    trend_manifest_path: Path,
    cs_data_dir: Path,
    cs_manifest_path: Path,
    output_path: Path,
) -> dict:
    trend_manifest = load_trend_manifest(
        trend_manifest_path
    )
    trend_assets = load_trend_assets(
        trend_data_dir,
        trend_manifest,
    )

    cs_assets, cs_manifest = load_cs_assets(
        cs_data_dir,
        cs_manifest_path,
    )

    trend_weights = _build_weight_path(
        trend_assets,
        TREND_STRATEGY,
    )
    cs_weights = _build_cs_weight_path(
        cs_assets,
    )

    rows = _align_rows(
        trend_assets,
        trend_weights,
        cs_assets,
        cs_weights,
    )

    research_end = int(
        len(rows) * RESEARCH_SHARE
    )

    scenarios = {}

    for scenario, multiplier in SCENARIOS:
        simulated = {
            name: _simulate(
                rows,
                multiplier,
                name == "vol_budget_10pct",
            )
            for name in RESULTS
        }

        scenarios[scenario] = {
            name: {
                "research": _stats(
                    simulated[name],
                    0,
                    research_end,
                ),
                "holdout": _stats(
                    simulated[name],
                    research_end,
                    len(rows),
                ),
                "rolling": _rolling(
                    simulated[name],
                    research_end,
                ),
            }
            for name in RESULTS
        }

    report = {
        "diagnostic_type": (
            "convergence_volatility_budget_control"
        ),
        "status": "COMPLETED",
        "source": {
            "trend_universe": trend_manifest["universe"],
            "trend_manifest_fingerprint": trend_manifest[
                "manifest_fingerprint"
            ],
            "trend_source_run_id": trend_manifest.get(
                "provenance",
                {},
            ).get("run_id"),
            "cs_universe": cs_manifest["universe"],
            "cs_manifest_fingerprint": cs_manifest[
                "manifest_fingerprint"
            ],
            "cs_source_run_id": cs_manifest.get(
                "provenance",
                {},
            ).get("run_id"),
            "common_return_count": len(rows),
        },
        "methodology": {
            "baseline_sleeve_architecture": "fixed 50/50 trend + 12-1 CS momentum",
            "new_hypothesis": (
                "fixed 10% annualized realized-volatility target, "
                "de-risk only"
            ),
            "target_vol_annualized": TARGET_VOL,
            "volatility_window_sessions": VOL_WINDOW,
            "scale_cap": MAX_SCALE,
            "optimization_used": False,
            "selection_profile_used": False,
            "signals_unchanged": True,
            "sleeve_weights_unchanged": True,
            "execution_unchanged": True,
            "holdout_is_blind_to_selection": True,
            "cost_scenarios": [name for name, _ in SCENARIOS],
        },
        "scenarios": scenarios,
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
        "CONVERGENCE_VOL_BUDGET_STATUS:",
        report["status"],
    )
    print(
        "REPORT_FINGERPRINT:",
        report["report_fingerprint"],
    )

    for scenario, values in report["scenarios"].items():
        for name, result in values.items():
            print(
                scenario,
                name,
                "HOLDOUT_RETURN=",
                result["holdout"]["period_return"],
                "HOLDOUT_DD=",
                result["holdout"]["max_drawdown_percent"],
                "HOLDOUT_PF=",
                result["holdout"]["profit_factor"],
                "HOLDOUT_VOL=",
                result["holdout"]["realized_vol_annualized"],
                "MEDIAN_SCALE=",
                result["holdout"]["median_scale"],
                "MIN_SCALE=",
                result["holdout"]["minimum_scale"],
            )


if __name__ == "__main__":
    main()
