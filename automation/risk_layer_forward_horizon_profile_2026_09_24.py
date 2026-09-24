"""Research-only forward-horizon profile after the existing 63-session de-risk state.

This extends the immediately-next-period diagnosis without changing the candidate.
For each Research time t, the unscaled cumulative net return from t+1 through
t+h is compared after scale(t)<1 versus scale(t)==1.

Fixed horizons: 1, 5, 20, 60 Research periods.
Holdout is never entered. No parameter search, strategy mutation, or orders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from automation import candidate_validation_50_50_vol_budget as base
from automation.risk_layer_drawdown_onset_2026_09_23 import CASES, _load_rows
from config import settings

RESEARCH_COUNT = base.RESEARCH_COUNT
HORIZONS = (1, 5, 20, 60)


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


def _compound(rows: tuple[dict[str, Any], ...], start: int, horizon: int) -> float | None:
    end = start + horizon
    if end > RESEARCH_COUNT:
        return None
    equity = 1.0
    cost_rate = base.FEE_RATE + base.SLIPPAGE_RATE
    for row in rows[start:end]:
        value = row["gross_open"] - cost_rate * row["turnover"]
        equity *= 1.0 + value
    return equity - 1.0


def _state_horizon_stats(
    rows: tuple[dict[str, Any], ...],
    simulated: list[dict[str, Any]],
    horizon: int,
) -> dict[str, Any]:
    derisk: list[float] = []
    full: list[float] = []

    for t in range(RESEARCH_COUNT - horizon):
        forward = _compound(rows, t + 1, horizon)
        if forward is None:
            continue
        if simulated[t]["scale"] < 1.0:
            derisk.append(forward)
        else:
            full.append(forward)

    def mean(values: list[float]) -> float | None:
        return sum(values) / len(values) if values else None

    def median(values: list[float]) -> float | None:
        if not values:
            return None
        ordered = sorted(values)
        return ordered[len(ordered) // 2]

    def positive_rate(values: list[float]) -> float | None:
        return (
            sum(value > 0.0 for value in values) / len(values)
            if values
            else None
        )

    mean_derisk = mean(derisk)
    mean_full = mean(full)
    median_derisk = median(derisk)
    median_full = median(full)
    positive_derisk = positive_rate(derisk)
    positive_full = positive_rate(full)

    return {
        "horizon": horizon,
        "eligible_state_observations": RESEARCH_COUNT - horizon,
        "de_risk_observations": len(derisk),
        "full_risk_observations": len(full),
        "de_risk_fraction": (
            len(derisk) / (len(derisk) + len(full))
            if derisk or full
            else 0.0
        ),
        "mean_forward_cumulative_return_after_de_risk": mean_derisk,
        "mean_forward_cumulative_return_after_full_risk": mean_full,
        "mean_difference_de_risk_minus_full": (
            mean_derisk - mean_full
            if mean_derisk is not None and mean_full is not None
            else None
        ),
        "median_forward_cumulative_return_after_de_risk": median_derisk,
        "median_forward_cumulative_return_after_full_risk": median_full,
        "median_difference_de_risk_minus_full": (
            median_derisk - median_full
            if median_derisk is not None and median_full is not None
            else None
        ),
        "positive_rate_after_de_risk": positive_derisk,
        "positive_rate_after_full_risk": positive_full,
        "positive_rate_difference_de_risk_minus_full": (
            positive_derisk - positive_full
            if positive_derisk is not None and positive_full is not None
            else None
        ),
        "mean_relationship": (
            "favorable"
            if mean_derisk is not None
            and mean_full is not None
            and mean_derisk <= mean_full
            else "adverse"
            if mean_derisk is not None
            and mean_full is not None
            else "inconclusive"
        ),
        "positive_rate_relationship": (
            "favorable"
            if positive_derisk is not None
            and positive_full is not None
            and positive_derisk <= positive_full
            else "adverse"
            if positive_derisk is not None
            and positive_full is not None
            else "inconclusive"
        ),
        "combined_relationship": (
            "favorable"
            if (
                mean_derisk is not None
                and mean_full is not None
                and positive_derisk is not None
                and positive_full is not None
                and mean_derisk <= mean_full
                and positive_derisk <= positive_full
            )
            else "adverse"
            if (
                mean_derisk is not None
                and mean_full is not None
                and positive_derisk is not None
                and positive_full is not None
                and mean_derisk > mean_full
                and positive_derisk > positive_full
            )
            else "mixed_or_inconclusive"
        ),
    }


def _aggregate_horizon_consensus(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    by_horizon: dict[str, Any] = {}
    for horizon in HORIZONS:
        results = [
            case["horizons"][str(horizon)]["combined_relationship"]
            for case in cases.values()
        ]
        by_horizon[str(horizon)] = {
            "favorable": results.count("favorable"),
            "adverse": results.count("adverse"),
            "mixed_or_inconclusive": results.count("mixed_or_inconclusive"),
        }

    return {
        "by_horizon": by_horizon,
        "interpretation_rule": {
            "short_horizon_adverse": (
                "At least 3/4 datasets are adverse at horizon 1."
            ),
            "medium_horizon_adverse": (
                "At least 3/4 datasets are adverse at horizon 20."
            ),
            "long_horizon_adverse": (
                "At least 3/4 datasets are adverse at horizon 60."
            ),
            "short_only_reversion": (
                "Horizon 1 is adverse in >=3/4 while horizon 20 or 60 is "
                "favorable in >=3/4."
            ),
        },
    }


def analyze(source_root: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    cases: dict[str, Any] = {}
    for case in CASES:
        rows = _load_rows(source_root, case)
        simulated = base._simulate(rows, 1.0, True, False)
        cases[case["name"]] = {
            "source": {
                "validation_run_id": case["run_id"],
                "artifact_id": case["artifact_id"],
            },
            "horizons": {
                str(horizon): _state_horizon_stats(rows, simulated, horizon)
                for horizon in HORIZONS
            },
            "research_only_assertion": (
                len(rows) == RESEARCH_COUNT + base.HOLDOUT_COUNT
                and len(simulated) == RESEARCH_COUNT + base.HOLDOUT_COUNT
            ),
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "risk_layer_forward_horizon_profile_2026_09_24",
        "status": "COMPLETED",
        "question": (
            "Is the adverse next-period relationship after the existing "
            "63-session de-risking state confined to short horizons or persistent "
            "over 5, 20 and 60 Research periods?"
        ),
        "scope": {
            "datasets": 4,
            "research_return_count_per_dataset": RESEARCH_COUNT,
            "horizons": list(HORIZONS),
            "holdout_used_for_decision": False,
            "holdout_metrics_reported": False,
            "parameter_search": False,
            "strategy_mutation": False,
            "asset_selection": False,
            "gate_changes": False,
            "production_mutation": False,
            "new_data_downloads": False,
        },
        "methodology": {
            "state_definition": "existing 63-session scale at time t: <1 de-risked, ==1 full risk",
            "forward_return": "cumulative unscaled net return from t+1 through t+h",
            "horizons_research_periods": list(HORIZONS),
            "same_candidate": True,
            "same_pit_semantics": True,
            "same_cost_model": True,
            "same_fixed_research_boundary": True,
            "descriptive_not_causal": True,
        },
        "cases": cases,
        "consensus": _aggregate_horizon_consensus(cases),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    result["diagnostic_fingerprint"] = _fp(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = analyze(Path(args.source_root))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )

    print("FORWARD_HORIZON_PROFILE_STATUS:", result["status"])
    print("CONSENSUS:", result["consensus"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
