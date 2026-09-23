"""Single-hypothesis Research ablation: risk-layer window 31 vs 63 sessions.

The fixed candidate, 10% annualized target, signals, PIT semantics and asset
universes remain unchanged. Only the realized-volatility estimation window of
the risk layer changes from 63 to 31 sessions.

No intermediate windows are tested. The four existing holdouts are not used.
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
WINDOW_A = 31
WINDOW_B = 63


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


def _vol(history: list[float], window: int) -> float | None:
    if len(history) < window:
        return None
    sample = history[-window:]
    mean = sum(sample) / len(sample)
    variance = sum((x - mean) ** 2 for x in sample) / len(sample)
    return math.sqrt(variance) * math.sqrt(252.0)


def _simulate_with_window(
    rows: tuple[dict, ...],
    window: int,
) -> list[dict]:
    if window <= 0:
        raise ValueError("window must be positive")
    history: list[float] = []
    previous_scale = 1.0
    output = []
    cost_rate = base.FEE_RATE + base.SLIPPAGE_RATE

    for row in rows:
        realized_vol = _vol(history, window)
        scale = 1.0
        if realized_vol is not None and realized_vol > base.TARGET_VOL:
            scale = min(1.0, base.TARGET_VOL / realized_vol)

        gross = row["gross_open"]
        turnover = scale * row["turnover"] + abs(scale - previous_scale)
        net = scale * gross - cost_rate * turnover

        output.append(
            {
                "timestamp": row["timestamp"],
                "scale": scale,
                "net_return": net,
                "gross_return": scale * gross,
                "realized_vol_estimate": realized_vol,
            }
        )
        previous_scale = scale
        history.append(
            row["gross_open"]
            - (base.FEE_RATE + base.SLIPPAGE_RATE) * row["turnover"]
        )
    return output


def _research_metrics(simulated: list[dict]) -> dict[str, Any]:
    research = base._stats(simulated, 0, RESEARCH_COUNT)
    rolling = base._rolling(simulated, RESEARCH_COUNT)
    summary = base._summary(simulated[:RESEARCH_COUNT], rolling)
    return {
        "research_return": research["period_return"],
        "research_drawdown_percent": research["max_drawdown_percent"],
        "research_profit_factor": research["profit_factor"],
        "rolling_profit_factor": summary["overall_profit_factor"],
        "rolling_average_drawdown_percent": summary["average_drawdown_percent"],
        "profitable_rolling_windows": summary["profitable_windows"],
        "profitable_window_ratio": summary["profitable_window_ratio"],
        "research_median_scale": sorted(
            row["scale"] for row in simulated[:RESEARCH_COUNT]
        )[RESEARCH_COUNT // 2],
        "research_minimum_scale": min(
            row["scale"] for row in simulated[:RESEARCH_COUNT]
        ),
        "research_de_risk_fraction": sum(
            row["scale"] < 1.0 for row in simulated[:RESEARCH_COUNT]
        ) / RESEARCH_COUNT,
    }


def _timing_metrics(simulated: list[dict]) -> dict[str, Any]:
    windows = [
        _analyze_window(simulated, start, end)
        for start, end in _window_bounds()
    ]
    rapid = _summarize(windows, "rapid")
    slow = _summarize(windows, "slow")
    return {
        "windows": windows,
        "rapid": rapid,
        "slow": slow,
    }


def _compare(
    result_31: dict[str, Any],
    result_63: dict[str, Any],
) -> dict[str, Any]:
    rapid31 = result_31["timing"]["rapid"]
    rapid63 = result_63["timing"]["rapid"]
    return {
        "rapid_delayed_rate_31": rapid31["delayed_or_never_rate"],
        "rapid_delayed_rate_63": rapid63["delayed_or_never_rate"],
        "rapid_delayed_rate_improved": (
            rapid31["delayed_or_never_rate"]
            < rapid63["delayed_or_never_rate"]
        ),
        "rapid_onset_active_rate_31": (
            rapid31["onset_day_already_de_risked_rate"]
        ),
        "rapid_onset_active_rate_63": (
            rapid63["onset_day_already_de_risked_rate"]
        ),
        "rapid_onset_active_rate_improved": (
            rapid31["onset_day_already_de_risked_rate"]
            > rapid63["onset_day_already_de_risked_rate"]
        ),
        "research_drawdown_31": result_31["research"]["research_drawdown_percent"],
        "research_drawdown_63": result_63["research"]["research_drawdown_percent"],
        "research_drawdown_non_deteriorated": (
            result_31["research"]["research_drawdown_percent"]
            <= result_63["research"]["research_drawdown_percent"]
        ),
        "rolling_pf_31": result_31["research"]["rolling_profit_factor"],
        "rolling_pf_63": result_63["research"]["rolling_profit_factor"],
        "rolling_pf_non_deteriorated": (
            float(result_31["research"]["rolling_profit_factor"])
            >= float(result_63["research"]["rolling_profit_factor"])
        ),
        "research_return_31": result_31["research"]["research_return"],
        "research_return_63": result_63["research"]["research_return"],
        "rolling_average_dd_31": (
            result_31["research"]["rolling_average_drawdown_percent"]
        ),
        "rolling_average_dd_63": (
            result_63["research"]["rolling_average_drawdown_percent"]
        ),
    }


def _consensus(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    timing_delay = sum(
        case["comparison"]["rapid_delayed_rate_improved"]
        for case in cases.values()
    )
    timing_onset = sum(
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

    if timing_delay >= 3 and timing_onset >= 3 and dd_ok >= 3 and pf_ok >= 3:
        decision = (
            "supports_31_session_risk_window_for_fifth_validation: "
            "rapid-drawdown timing improves in >=3/4 datasets on both "
            "pre-registered timing measures and Research DD/PF do not "
            "deteriorate in >=3/4."
        )
    elif timing_delay >= 3 or timing_onset >= 3:
        decision = (
            "timing_improvement_with_research_tradeoff: "
            "the 31-session window improves at least one rapid-drawdown "
            "timing measure in >=3/4 datasets, but the full non-deterioration "
            "criteria are not met."
        )
    else:
        decision = (
            "risk_window_hypothesis_not_supported: "
            "the 31-session window does not improve the pre-registered "
            "rapid-drawdown timing measures in >=3/4 datasets."
        )

    return {
        "replication_counts": {
            "rapid_delayed_rate_improved": timing_delay,
            "rapid_onset_active_rate_improved": timing_onset,
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
        sim63 = base._simulate(rows, 1.0, True, False)
        sim31 = _simulate_with_window(rows, WINDOW_A)

        # Exact parity test inside the production experiment: our 63-session
        # reproduction must equal the existing implementation row-for-row.
        parity63 = [
            (
                a["timestamp"],
                a["scale"],
                a["net_return"],
                a["realized_vol_estimate"],
            )
            for a in sim63
        ]
        parity63_reference = _simulate_with_window(rows, WINDOW_B)
        parity63_alt = [
            (
                a["timestamp"],
                a["scale"],
                a["net_return"],
                a["realized_vol_estimate"],
            )
            for a in parity63_reference
        ]
        if parity63 != parity63_alt:
            raise ValueError(f'{case["name"]}: 63-session parity mismatch')

        result31 = {
            "research": _research_metrics(sim31),
            "timing": _timing_metrics(sim31),
        }
        result63 = {
            "research": _research_metrics(sim63),
            "timing": _timing_metrics(sim63),
        }

        cases[case["name"]] = {
            "source": {
                "validation_run_id": case["run_id"],
                "artifact_id": case["artifact_id"],
            },
            "window_31": result31,
            "window_63": result63,
            "comparison": _compare(result31, result63),
            "research_only_assertion": (
                len(sim31) == RESEARCH_COUNT + base.HOLDOUT_COUNT
                and len(sim63) == RESEARCH_COUNT + base.HOLDOUT_COUNT
            ),
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "risk_layer_window_31_vs_63_2026_09_23",
        "status": "COMPLETED",
        "question": (
            "Does a fixed 31-session realized-volatility risk-layer window "
            "reduce rapid-drawdown onset lag versus the current 63-session "
            "window at the same 10% annualized target?"
        ),
        "scope": {
            "datasets": 4,
            "research_rolling_windows": 20,
            "research_return_count_per_dataset": RESEARCH_COUNT,
            "holdout_used_for_decision": False,
            "holdout_metrics_reported": False,
            "intermediate_windows_tested": False,
            "parameter_search": False,
            "asset_selection": False,
            "gate_changes": False,
            "production_mutation": False,
        },
        "methodology": {
            "window_a_sessions": WINDOW_A,
            "window_b_sessions": WINDOW_B,
            "target_annualized_volatility": base.TARGET_VOL,
            "same_candidate_signals": True,
            "same_pit_semantics": True,
            "same_cost_model": True,
            "same_de_risk_only_behavior": True,
            "same_asset_universes": True,
            "same_research_windows": True,
            "no_holdout_selection": True,
            "63_session_parity_checked": True,
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
    print("RISK_WINDOW_EXPERIMENT_STATUS:", result["status"])
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
