"""Research-only comparison of fast versus slow maximum-drawdown onset.

The fixed candidate and fixed 63-session / 10% volatility risk layer are held
constant. For each of four immutable validation datasets, each of the five
pre-existing Research rolling windows contributes one maximum-drawdown episode.

Rapid episode:
    maximum-drawdown episode length <= floor(63 / 2) = 31 sessions.

Delayed onset:
    first de-risking occurs at least two drawdown days after episode onset,
    or no de-risking occurs before the episode trough.

Only Research windows are used. The Holdout is not reported or used for
classification.

No parameter search, no asset selection, no gate changes, no production
mutation, no orders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from automation.risk_layer_drawdown_onset_2026_09_23 import CASES, _load_rows
from automation import candidate_validation_50_50_vol_budget as base
from config import settings

RESEARCH_COUNT = base.RESEARCH_COUNT
ROLLING_WINDOWS = 5
RAPID_THRESHOLD_DAYS = base.VOL_WINDOW // 2


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


def _window_bounds() -> tuple[tuple[int, int], ...]:
    width = RESEARCH_COUNT // ROLLING_WINDOWS
    bounds = []
    start = 0
    for index in range(ROLLING_WINDOWS):
        end = RESEARCH_COUNT if index == ROLLING_WINDOWS - 1 else start + width
        bounds.append((start, end))
        start = end
    return tuple(bounds)


def _max_drawdown_interval(
    simulated: list[dict[str, Any]],
    start: int,
    end: int,
) -> tuple[int, int, float]:
    equity = peak_equity = 1.0
    peak_index = start
    best = (start, start, 0.0)

    for index in range(start, end):
        equity *= 1.0 + simulated[index]["net_return"]
        if equity > peak_equity:
            peak_equity = equity
            peak_index = index
        drawdown = 1.0 - equity / peak_equity
        if drawdown > best[2]:
            best = (peak_index, index, drawdown)
    return best


def _analyze_window(
    simulated: list[dict[str, Any]],
    start: int,
    end: int,
) -> dict[str, Any]:
    peak_index, trough_index, max_dd = _max_drawdown_interval(
        simulated,
        start,
        end,
    )
    episode_start = min(peak_index + 1, end)
    episode = simulated[episode_start : trough_index + 1]

    activation_index = None
    for index, row in enumerate(episode, start=episode_start):
        if row["scale"] < 1.0:
            activation_index = index
            break

    lag = (
        activation_index - episode_start
        if activation_index is not None
        else None
    )
    delayed = lag is None or lag >= 2

    return {
        "window_start_index": start,
        "window_end_index_exclusive": end,
        "peak_index": peak_index,
        "trough_index": trough_index,
        "peak_timestamp": simulated[peak_index]["timestamp"].isoformat(),
        "trough_timestamp": simulated[trough_index]["timestamp"].isoformat(),
        "max_drawdown_percent": max_dd * 100.0,
        "episode_length_days": len(episode),
        "rapid_episode": len(episode) <= RAPID_THRESHOLD_DAYS,
        "activation_index": activation_index,
        "activation_lag_drawdown_days": lag,
        "delayed_or_never": delayed,
        "onset_day_already_de_risked": bool(episode) and episode[0]["scale"] < 1.0,
        "minimum_episode_scale": min(
            (row["scale"] for row in episode),
            default=1.0,
        ),
    }


def _summarize(windows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    selected = [row for row in windows if row["rapid_episode"] == (label == "rapid")]
    delayed = sum(row["delayed_or_never"] for row in selected)
    onset = sum(row["onset_day_already_de_risked"] for row in selected)
    activations = [
        row["activation_lag_drawdown_days"]
        for row in selected
        if row["activation_lag_drawdown_days"] is not None
    ]
    return {
        "episode_count": len(selected),
        "delayed_or_never_count": delayed,
        "delayed_or_never_rate": delayed / len(selected) if selected else 0.0,
        "onset_day_already_de_risked_count": onset,
        "onset_day_already_de_risked_rate": onset / len(selected) if selected else 0.0,
        "mean_activation_lag_days": (
            sum(activations) / len(activations) if activations else None
        ),
        "median_activation_lag_days": (
            sorted(activations)[len(activations) // 2]
            if activations
            else None
        ),
    }


def analyze_case(rows: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    simulated = base._simulate(rows, 1.0, True, False)
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
        "rapid_minus_slow_delayed_rate": (
            rapid["delayed_or_never_rate"] - slow["delayed_or_never_rate"]
        ),
        "rapid_minus_slow_onset_active_rate": (
            rapid["onset_day_already_de_risked_rate"]
            - slow["onset_day_already_de_risked_rate"]
        ),
    }


def _consensus(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rapid_more_delayed = sum(
        case["rapid"]["delayed_or_never_rate"]
        > case["slow"]["delayed_or_never_rate"]
        for case in cases.values()
    )
    rapid_less_onset_active = sum(
        case["rapid"]["onset_day_already_de_risked_rate"]
        < case["slow"]["onset_day_already_de_risked_rate"]
        for case in cases.values()
    )

    if rapid_more_delayed >= 3:
        decision = (
            "replicated_rapid_drawdown_onset_lag: "
            "rapid maximum-drawdown episodes have a higher delayed-or-never "
            "rate than slow episodes in at least 3/4 validation datasets."
        )
    elif rapid_less_onset_active >= 3:
        decision = (
            "replicated_rapid_drawdown_onset_undercoverage: "
            "rapid maximum-drawdown episodes are less often already de-risked "
            "at onset than slow episodes in at least 3/4 validation datasets."
        )
    else:
        decision = (
            "no_replicated_rapid_drawdown_onset_contrast: "
            "neither pre-registered 3/4 rapid-versus-slow timing rule is met."
        )

    return {
        "replication_counts": {
            "rapid_more_delayed_than_slow": rapid_more_delayed,
            "rapid_less_onset_active_than_slow": rapid_less_onset_active,
        },
        "decision_rule": decision,
    }


def run_diagnosis(source_root: Path, output_path: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    cases = {}
    for case in CASES:
        rows = _load_rows(source_root, case)
        cases[case["name"]] = {
            "source": {
                "validation_run_id": case["run_id"],
                "artifact_id": case["artifact_id"],
            },
            **analyze_case(rows),
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "risk_layer_drawdown_speed_2026_09_23",
        "status": "COMPLETED",
        "question": (
            "Is the fixed risk-layer onset lag systematically worse for rapid "
            "maximum-drawdown episodes than for slow episodes?"
        ),
        "scope": {
            "datasets": 4,
            "research_rolling_windows": 20,
            "research_return_count_per_dataset": RESEARCH_COUNT,
            "holdout_used_for_decision": False,
            "holdout_metrics_reported": False,
            "new_data_downloads": False,
            "parameter_search": False,
            "selection": False,
            "gate_changes": False,
            "production_mutation": False,
        },
        "methodology": {
            "risk_layer_window_sessions": base.VOL_WINDOW,
            "risk_layer_target_annualized_volatility": base.TARGET_VOL,
            "rapid_episode_threshold_days": RAPID_THRESHOLD_DAYS,
            "rapid_definition": (
                f"maximum-drawdown episode length <= {RAPID_THRESHOLD_DAYS} sessions"
            ),
            "delayed_definition": (
                "first de-risking occurs >=2 drawdown days after episode onset, "
                "or no de-risking before trough"
            ),
            "fixed_rolling_window_count_per_dataset": ROLLING_WINDOWS,
            "same_candidate_and_cost_model": True,
            "same_pit_semantics": True,
            "descriptive_not_causal": True,
        },
        "cases": cases,
        "consensus": _consensus(cases),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    result["diagnostic_fingerprint"] = _fp(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    print("RISK_LAYER_DRAWDOWN_SPEED_STATUS:", result["status"])
    print("DECISION_RULE:", result["consensus"]["decision_rule"])
    print("REPLICATION_COUNTS:", result["consensus"]["replication_counts"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_diagnosis(Path(args.source_root), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
