"""Family-level walk-forward control for the validated trend families.

This is a diagnostic research layer. It does not alter production strategy
selection or gates.

Selection is intentionally restricted to three already tested families:
- monthly TSM equal-weight
- SMA 50/200 inverse-volatility
- fixed 50/50 TSM/SMA inverse-volatility blend

For each research rolling window:
1. score families on training data by profit factor;
2. break ties by period return, then lower drawdown;
3. freeze the selected family for the following OOS test block.

The final family selected from the last research window is then frozen for the
blind holdout. Costs are selected under base costs only; 2x costs are a stress
evaluation of the same selected family.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from automation.cross_asset_trend_replication import (
    BASE_FEE,
    BASE_SLIPPAGE,
    COST_SCENARIOS,
    _daily_returns,
    _load_assets,
    _load_manifest,
    _rolling,
    _build_weight_path,
    _stats,
)

FAMILY_STRATEGIES = (
    "tsm_monthly_equal",
    "sma_50_200_inverse_vol",
    "blend_tsm_sma_inverse_vol",
)
REFERENCE_STRATEGY = "buy_and_hold_equal"

RESEARCH_SHARE = 0.80
TRAIN_SIZE = 1400
TEST_SIZE = 280
STEP_SIZE = 280


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


def _return_stats(
    returns: list[float],
    start_index: int,
    end_index: int,
) -> dict:
    first = max(0, start_index)
    last = min(end_index, len(returns))
    segment = returns[first:last]

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
                (1.0 - equity / peak),
            )

        if value > 0:
            gross_profit += value
            positive_days += 1
        elif value < 0:
            gross_loss -= value

    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    elif gross_profit > 0:
        profit_factor = "inf"
    else:
        profit_factor = 0.0

    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_drawdown * 100.0,
        "profit_factor": profit_factor,
        "positive_day_ratio": positive_days / len(segment),
        "day_count": len(segment),
    }


def _select_family(training_returns: dict[str, list[float]]) -> dict:
    scored = []

    for strategy, returns in training_returns.items():
        metrics = _return_stats(
            returns,
            0,
            len(returns),
        )
        pf = metrics["profit_factor"]
        pf_numeric = float("inf") if pf == "inf" else float(pf)
        scored.append(
            {
                "strategy": strategy,
                "profit_factor": pf_numeric,
                "period_return": metrics["period_return"],
                "max_drawdown_percent": metrics["max_drawdown_percent"],
            }
        )

    selected = sorted(
        scored,
        key=lambda item: (
            -item["profit_factor"],
            -item["period_return"],
            item["max_drawdown_percent"],
            item["strategy"],
        ),
    )[0]

    return {
        "selected_strategy": selected["strategy"],
        "candidates": scored,
        "selection_rule": (
            "highest_training_profit_factor; "
            "tie_break_period_return; "
            "tie_break_lower_max_drawdown; "
            "final_tie_lexicographic_strategy_name"
        ),
    }


def _rolling_windows(research_count: int) -> tuple[tuple[int, int, int, int], ...]:
    windows = []
    start = 0
    index = 1

    while start + TRAIN_SIZE + TEST_SIZE <= research_count:
        train_start = start
        train_end = start + TRAIN_SIZE
        test_end = train_end + TEST_SIZE
        windows.append(
            (index, train_start, train_end, test_end)
        )
        start += STEP_SIZE
        index += 1

    return tuple(windows)


def _dynamic_oos(
    base_streams: dict[str, list[float]],
    stress_streams: dict[str, list[float]],
    research_count: int,
    target_count: int,
) -> tuple[list[dict], str]:
    windows = _rolling_windows(research_count)
    rows = []

    for index, train_start, train_end, test_end in windows:
        training = {
            strategy: base_streams[strategy][train_start:train_end]
            for strategy in FAMILY_STRATEGIES
        }

        selection = _select_family(training)
        selected = selection["selected_strategy"]

        base_test = _return_stats(
            base_streams[selected],
            train_end,
            test_end,
        )
        stress_test = _return_stats(
            stress_streams[selected],
            train_end,
            test_end,
        )

        rows.append(
            {
                "window_index": index,
                "train_start": train_start,
                "train_end": train_end,
                "test_end": test_end,
                "selected_strategy": selected,
                "selection": selection,
                "base_test": base_test,
                "stress_test": stress_test,
            }
        )

    if not rows:
        raise ValueError("Keine Family-WFO-Fenster erzeugt.")

    final_selected = rows[-1]["selected_strategy"]

    holdout_base = _return_stats(
        base_streams[final_selected],
        research_count,
        target_count,
    )
    holdout_stress = _return_stats(
        stress_streams[final_selected],
        research_count,
        target_count,
    )

    holdout = {
        "frozen_strategy_from_last_research_window": final_selected,
        "base": holdout_base,
        "stress_2x_cost": holdout_stress,
    }

    return rows, holdout


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

    target_count = len(next(iter(assets.values())))
    research_count = int(target_count * RESEARCH_SHARE)
    holdout_count = target_count - research_count

    if target_count != 3500:
        raise ValueError(
            f"Family-WFO erwartet 3500 Candles, gefunden: {target_count}"
        )
    if research_count != 2800 or holdout_count != 700:
        raise ValueError("Unerwartete Research-/Holdout-Aufteilung.")

    base_streams = {}
    stress_streams = {}

    for strategy in (REFERENCE_STRATEGY, *FAMILY_STRATEGIES):
        weights = _build_weight_path(
            assets,
            strategy,
        )
        base_streams[strategy] = _daily_returns(
            assets,
            weights,
            1.0,
        )
        stress_streams[strategy] = _daily_returns(
            assets,
            weights,
            2.0,
        )

    windows, holdout = _dynamic_oos(
        base_streams,
        stress_streams,
        research_count,
        target_count,
    )

    selected_counts = {}
    for row in windows:
        selected = row["selected_strategy"]
        selected_counts[selected] = (
            selected_counts.get(selected, 0) + 1
        )

    fixed_family_summary = {}
    for strategy in FAMILY_STRATEGIES:
        fixed_family_summary[strategy] = {
            "base_research": _return_stats(
                base_streams[strategy],
                0,
                research_count,
            ),
            "base_holdout": _return_stats(
                base_streams[strategy],
                research_count,
                target_count,
            ),
            "stress_holdout": _return_stats(
                stress_streams[strategy],
                research_count,
                target_count,
            ),
        }

    reference = {
        "base": _return_stats(
            base_streams[REFERENCE_STRATEGY],
            research_count,
            target_count,
        ),
        "stress_2x_cost": _return_stats(
            stress_streams[REFERENCE_STRATEGY],
            research_count,
            target_count,
        ),
    }

    selected_base_returns = []
    selected_stress_returns = []
    for row in windows:
        selected_base_returns.append(
            row["base_test"]["period_return"]
        )
        selected_stress_returns.append(
            row["stress_test"]["period_return"]
        )

    report = {
        "diagnostic_type": "trend_family_walk_forward_control",
        "status": "COMPLETED",
        "source": {
            "universe": manifest["universe"],
            "symbols": list(assets),
            "target_count": target_count,
            "research_candle_count": research_count,
            "holdout_candle_count": holdout_count,
            "manifest_fingerprint": manifest["manifest_fingerprint"],
            "manifest_generated_at": manifest["generated_at"],
        },
        "methodology": {
            "candidate_families": list(FAMILY_STRATEGIES),
            "reference_strategy": REFERENCE_STRATEGY,
            "optimization_used": False,
            "parameter_optimization_used": False,
            "selection_profile_used": False,
            "selection_scope": "training_only",
            "selection_rule": windows[0]["selection"]["selection_rule"],
            "train_size": TRAIN_SIZE,
            "test_size": TEST_SIZE,
            "step_size": STEP_SIZE,
            "research_windows": len(windows),
            "holdout_is_blind_to_selection": True,
            "holdout_strategy_rule": (
                "freeze_family_selected_in_last_research_window"
            ),
            "base_fee": BASE_FEE,
            "base_slippage": BASE_SLIPPAGE,
            "stress_cost_multiplier": dict(COST_SCENARIOS)[
                "stress_2x_cost"
            ],
            "execution": (
                "close_t_decision_then_next_open_execution_and_following_open_return"
            ),
        },
        "selection": {
            "selected_family_per_window": windows,
            "selection_counts": selected_counts,
            "selected_base_test_return_sum": sum(
                selected_base_returns
            ),
            "selected_stress_test_return_sum": sum(
                selected_stress_returns
            ),
            "selected_base_positive_window_count": sum(
                value > 0
                for value in selected_base_returns
            ),
            "selected_stress_positive_window_count": sum(
                value > 0
                for value in selected_stress_returns
            ),
        },
        "fixed_family_summary": fixed_family_summary,
        "reference": reference,
        "holdout": holdout,
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
        "TREND_FAMILY_WFO_STATUS:",
        report["status"],
    )
    print(
        "REPORT_FINGERPRINT:",
        report["report_fingerprint"],
    )
    print(
        "SELECTION_COUNTS:",
        report["selection"]["selection_counts"],
    )
    print(
        "SELECTED_BASE_POSITIVE_WINDOWS:",
        report["selection"]["selected_base_positive_window_count"],
        "/",
        report["methodology"]["research_windows"],
    )
    print(
        "HOLDOUT_FROZEN_STRATEGY:",
        report["holdout"][
            "frozen_strategy_from_last_research_window"
        ],
    )
    print(
        "HOLDOUT_BASE_RETURN:",
        report["holdout"]["base"]["period_return"],
    )
    print(
        "HOLDOUT_BASE_PF:",
        report["holdout"]["base"]["profit_factor"],
    )
    print(
        "HOLDOUT_STRESS_RETURN:",
        report["holdout"]["stress_2x_cost"]["period_return"],
    )
    print(
        "HOLDOUT_STRESS_PF:",
        report["holdout"]["stress_2x_cost"]["profit_factor"],
    )


if __name__ == "__main__":
    main()
