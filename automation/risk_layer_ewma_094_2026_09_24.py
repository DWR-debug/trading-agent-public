"""Research-only EWMA(0.94) risk-layer ablation.

The current fixed candidate, 63-session realized-volatility control and 10%
annualized target remain the reference. Only the volatility estimator changes.

Intervention:
    EWMA variance recurrence with RiskMetrics daily decay lambda = 0.94,
    using zero-mean daily returns, annualized by sqrt(252).

The estimator warms up on the first 63 observed unscaled portfolio returns.
After the warm-up, the EWMA state is updated recursively as new returns arrive.

No lambda search, no alternative estimators, no asset selection, no gate changes,
no holdout use, no production mutation, and no orders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from automation import candidate_validation_50_50_vol_budget as base
from automation.risk_layer_drawdown_onset_2026_09_23 import CASES, _load_rows
from automation.risk_layer_drawdown_speed_2026_09_23 import (
    _analyze_window,
    _summarize,
    _window_bounds,
)
from config import settings

RESEARCH_COUNT = base.RESEARCH_COUNT
WARMUP_WINDOW = base.VOL_WINDOW
TARGET_VOL = base.TARGET_VOL
EWMA_LAMBDA = 0.94
ANNUALIZATION = math.sqrt(252.0)


def _canon(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode()).hexdigest()


def _simulate_ewma(rows: tuple[dict, ...]) -> list[dict[str, Any]]:
    history: list[float] = []
    ewma_variance: float | None = None
    previous_scale = 1.0
    output = []
    cost_rate = base.FEE_RATE + base.SLIPPAGE_RATE

    for row in rows:
        if ewma_variance is not None and len(history) >= WARMUP_WINDOW:
            realized_vol = math.sqrt(max(0.0, ewma_variance)) * ANNUALIZATION
        else:
            realized_vol = None

        scale = 1.0
        if realized_vol is not None and realized_vol > TARGET_VOL:
            scale = min(1.0, TARGET_VOL / realized_vol)

        gross = row["gross_open"]
        turnover = scale * row["turnover"] + abs(scale - previous_scale)
        net = scale * gross - cost_rate * turnover

        output.append(
            {
                "timestamp": row["timestamp"],
                "scale": scale,
                "net_return": net,
                "gross_return": scale * gross,
                "ewma_realized_vol_estimate": realized_vol,
                "ewma_variance": ewma_variance,
            }
        )

        previous_scale = scale
        observed = (
            row["gross_open"]
            - (base.FEE_RATE + base.SLIPPAGE_RATE) * row["turnover"]
        )
        history.append(observed)

        if ewma_variance is None:
            ewma_variance = observed * observed
        else:
            ewma_variance = (
                EWMA_LAMBDA * ewma_variance
                + (1.0 - EWMA_LAMBDA) * observed * observed
            )

    return output


def _research_metrics(simulated: list[dict[str, Any]]) -> dict[str, Any]:
    research_rows = simulated[:RESEARCH_COUNT]
    research = base._stats(simulated, 0, RESEARCH_COUNT)
    rolling = base._rolling(simulated, RESEARCH_COUNT)
    summary = base._summary(research_rows, rolling)
    return {
        "research_return": research["period_return"],
        "research_drawdown_percent": research["max_drawdown_percent"],
        "research_profit_factor": research["profit_factor"],
        "rolling_profit_factor": summary["overall_profit_factor"],
        "rolling_average_drawdown_percent": summary["average_drawdown_percent"],
        "profitable_rolling_windows": summary["profitable_windows"],
        "profitable_window_ratio": summary["profitable_window_ratio"],
        "research_median_scale": sorted(
            row["scale"] for row in research_rows
        )[RESEARCH_COUNT // 2],
        "research_minimum_scale": min(row["scale"] for row in research_rows),
        "research_de_risk_fraction": sum(
            row["scale"] < 1.0 for row in research_rows
        ) / RESEARCH_COUNT,
    }


def _timing_metrics(simulated: list[dict[str, Any]]) -> dict[str, Any]:
    windows = [
        _analyze_window(simulated, start, end)
        for start, end in _window_bounds()
    ]
    return {
        "windows": windows,
        "rapid": _summarize(windows, "rapid"),
        "slow": _summarize(windows, "slow"),
    }


def _compare(intervention: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    rapid_i = intervention["timing"]["rapid"]
    rapid_c = control["timing"]["rapid"]
    research_i = intervention["research"]
    research_c = control["research"]

    return {
        "rapid_delayed_rate_control": rapid_c["delayed_or_never_rate"],
        "rapid_delayed_rate_intervention": rapid_i["delayed_or_never_rate"],
        "rapid_delayed_rate_improved": (
            rapid_i["delayed_or_never_rate"]
            < rapid_c["delayed_or_never_rate"]
        ),
        "rapid_onset_active_rate_control": (
            rapid_c["onset_day_already_de_risked_rate"]
        ),
        "rapid_onset_active_rate_intervention": (
            rapid_i["onset_day_already_de_risked_rate"]
        ),
        "rapid_onset_active_rate_improved": (
            rapid_i["onset_day_already_de_risked_rate"]
            > rapid_c["onset_day_already_de_risked_rate"]
        ),
        "research_drawdown_control": research_c["research_drawdown_percent"],
        "research_drawdown_intervention": research_i["research_drawdown_percent"],
        "research_drawdown_non_deteriorated": (
            research_i["research_drawdown_percent"]
            <= research_c["research_drawdown_percent"]
        ),
        "rolling_pf_control": research_c["rolling_profit_factor"],
        "rolling_pf_intervention": research_i["rolling_profit_factor"],
        "rolling_pf_non_deteriorated": (
            float(research_i["rolling_profit_factor"])
            >= float(research_c["rolling_profit_factor"])
        ),
        "research_return_control": research_c["research_return"],
        "research_return_intervention": research_i["research_return"],
        "rolling_average_dd_control": (
            research_c["rolling_average_drawdown_percent"]
        ),
        "rolling_average_dd_intervention": (
            research_i["rolling_average_drawdown_percent"]
        ),
    }


def _consensus(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    delay = sum(
        case["comparison"]["rapid_delayed_rate_improved"]
        for case in cases.values()
    )
    onset = sum(
        case["comparison"]["rapid_onset_active_rate_improved"]
        for case in cases.values()
    )
    dd_ok = sum(
        case["comparison"]["research_drawdown_non_deteriorated"]
        for case in cases.values()
    )
    pf_ok = sum(
        case["comparison"]["rolling_pf_non_deteriorated"]
        for case in cases.values()
    )

    if delay >= 3 and onset >= 3 and dd_ok >= 3 and pf_ok >= 3:
        decision = (
            "supports_ewma_094_for_fifth_validation: both rapid-drawdown timing "
            "measures improve in >=3/4 datasets and Research DD/PF do not "
            "deteriorate in >=3/4."
        )
    elif delay >= 3 or onset >= 3:
        decision = (
            "ewma_094_timing_improvement_with_research_tradeoff: the EWMA(0.94) "
            "intervention improves at least one rapid-drawdown timing measure "
            "in >=3/4 datasets, but the full Research non-deterioration criteria "
            "are not met."
        )
    else:
        decision = (
            "ewma_094_not_supported: the fixed RiskMetrics-style EWMA does not "
            "improve the pre-registered rapid-drawdown timing measures in >=3/4 "
            "datasets."
        )

    return {
        "replication_counts": {
            "rapid_delayed_rate_improved": delay,
            "rapid_onset_active_rate_improved": onset,
            "research_drawdown_non_deteriorated": dd_ok,
            "rolling_pf_non_deteriorated": pf_ok,
        },
        "decision_rule": decision,
    }


def run_experiment(source_root: Path, output_path: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    cases: dict[str, Any] = {}
    for case in CASES:
        rows = _load_rows(source_root, case)
        control = base._simulate(rows, 1.0, True, False)
        intervention = _simulate_ewma(rows)

        control_research = _research_metrics(control)
        control_timing = _timing_metrics(control)
        intervention_research = _research_metrics(intervention)
        intervention_timing = _timing_metrics(intervention)

        cases[case["name"]] = {
            "source": {
                "validation_run_id": case["run_id"],
                "artifact_id": case["artifact_id"],
            },
            "control_63_session": {
                "research": control_research,
                "timing": control_timing,
            },
            "ewma_094": {
                "research": intervention_research,
                "timing": intervention_timing,
            },
            "comparison": _compare(
                {"research": intervention_research, "timing": intervention_timing},
                {"research": control_research, "timing": control_timing},
            ),
            "research_only_assertion": (
                len(control) == RESEARCH_COUNT + base.HOLDOUT_COUNT
                and len(intervention) == RESEARCH_COUNT + base.HOLDOUT_COUNT
            ),
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "risk_layer_ewma_094_2026_09_24",
        "status": "COMPLETED",
        "question": (
            "Can a fixed RiskMetrics-style EWMA(0.94) daily volatility estimator "
            "reduce the replicated rapid-drawdown onset lag while preserving "
            "Research DD and rolling PF relative to the fixed 63-session control?"
        ),
        "scope": {
            "datasets": 4,
            "research_rolling_windows": 20,
            "research_return_count_per_dataset": RESEARCH_COUNT,
            "holdout_used_for_decision": False,
            "holdout_metrics_reported": False,
            "lambda_search": False,
            "alternative_estimator_search": False,
            "asset_selection": False,
            "gate_changes": False,
            "production_mutation": False,
            "new_data_downloads": False,
        },
        "methodology": {
            "control_risk_estimator": "63-session sample volatility",
            "intervention_estimator": "RiskMetrics-style EWMA variance",
            "ewma_lambda": EWMA_LAMBDA,
            "warmup_sessions": WARMUP_WINDOW,
            "target_annualized_volatility": TARGET_VOL,
            "zero_mean_return_assumption": True,
            "same_candidate_signals": True,
            "same_pit_semantics": True,
            "same_cost_model": True,
            "same_asset_universes": True,
            "same_de_risk_only_behavior": True,
            "same_research_windows": True,
            "descriptive_research_ablation": True,
        },
        "cases": cases,
        "consensus": _consensus(cases),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }

    result["experiment_fingerprint"] = _fp(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )

    print("EWMA_094_STATUS:", result["status"])
    print("DECISION_RULE:", result["consensus"]["decision_rule"])
    print("REPLICATION_COUNTS:", result["consensus"]["replication_counts"])
    print("EXPERIMENT_FINGERPRINT:", result["experiment_fingerprint"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_experiment(Path(args.source_root), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
