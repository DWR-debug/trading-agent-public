"""Research-only diagnosis of next-period returns after 63-session de-risking.

This is not an intervention. The fixed 63-session / 10% risk layer is simulated
unchanged on four immutable validation artifacts. For every Research period t,
the diagnosis conditions the unscaled next-period return at t+1 on whether the
risk layer was already de-risked at t.

The motivation is the volatility-timing mechanism documented by Moreira & Muir:
volatility management is economically useful when high-risk states are not
offset by proportionally high subsequent expected returns.

No parameter search, no new data, no holdout use, no strategy mutation, and no
orders.
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


def _forward_stats(
    simulated: list[dict[str, Any]],
    rows: tuple[dict, ...],
) -> dict[str, Any]:
    if len(simulated) != len(rows):
        raise ValueError("simulation/input length mismatch")
    research_rows = simulated[:RESEARCH_COUNT]
    available = RESEARCH_COUNT - 1
    cost_rate = base.FEE_RATE + base.SLIPPAGE_RATE

    forward_derisk_net: list[float] = []
    forward_full_net: list[float] = []
    forward_derisk_gross: list[float] = []
    forward_full_gross: list[float] = []

    for index in range(available):
        next_row = rows[index + 1]
        next_unscaled_net = (
            next_row["gross_open"] - cost_rate * next_row["turnover"]
        )
        if research_rows[index]["scale"] < 1.0:
            forward_derisk_net.append(next_unscaled_net)
            forward_derisk_gross.append(next_row["gross_open"])
        else:
            forward_full_net.append(next_unscaled_net)
            forward_full_gross.append(next_row["gross_open"])

    def mean(values: list[float]) -> float | None:
        return sum(values) / len(values) if values else None

    def positive_rate(values: list[float]) -> float | None:
        return (
            sum(value > 0.0 for value in values) / len(values)
            if values
            else None
        )

    mean_derisk = mean(forward_derisk_net)
    mean_full = mean(forward_full_net)
    pos_derisk = positive_rate(forward_derisk_net)
    pos_full = positive_rate(forward_full_net)

    return {
        "research_transition_count": available,
        "de_risk_observations": len(forward_derisk_net),
        "full_risk_observations": len(forward_full_net),
        "de_risk_fraction": (
            len(forward_derisk_net) / available if available else 0.0
        ),
        "mean_next_unscaled_net_return_after_de_risk": mean_derisk,
        "mean_next_unscaled_net_return_after_full_risk": mean_full,
        "mean_next_return_difference_de_risk_minus_full": (
            mean_derisk - mean_full
            if mean_derisk is not None and mean_full is not None
            else None
        ),
        "next_positive_rate_after_de_risk": pos_derisk,
        "next_positive_rate_after_full_risk": pos_full,
        "positive_rate_difference_de_risk_minus_full": (
            pos_derisk - pos_full
            if pos_derisk is not None and pos_full is not None
            else None
        ),
        "favorable_mean_relationship": (
            mean_derisk <= mean_full
            if mean_derisk is not None and mean_full is not None
            else False
        ),
        "favorable_positive_rate_relationship": (
            pos_derisk <= pos_full
            if pos_derisk is not None and pos_full is not None
            else False
        ),
        "next_return_range_de_risk": (
            [min(forward_derisk_gross), max(forward_derisk_gross)]
            if forward_derisk_gross
            else None
        ),
        "next_return_range_full": (
            [min(forward_full_gross), max(forward_full_gross)]
            if forward_full_gross
            else None
        ),
    }


def _classify(case_result: dict[str, Any]) -> str:
    stats = case_result["forward_stats"]
    mean_ok = stats["favorable_mean_relationship"]
    positive_ok = stats["favorable_positive_rate_relationship"]

    if mean_ok and positive_ok:
        return "favorable_de_risk_forward_relationship"
    if (not mean_ok) and (not positive_ok):
        return "adverse_de_risk_forward_relationship"
    return "mixed_de_risk_forward_relationship"


def _consensus(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    favorable = sum(
        case["classification"] == "favorable_de_risk_forward_relationship"
        for case in cases.values()
    )
    adverse = sum(
        case["classification"] == "adverse_de_risk_forward_relationship"
        for case in cases.values()
    )
    mixed = len(cases) - favorable - adverse

    if favorable >= 3:
        decision = (
            "supports_existing_volatility_timing_premise: de-risked states "
            "are followed by no-higher next-period returns on both predefined "
            "diagnostic measures in >=3/4 datasets."
        )
    elif adverse >= 3:
        decision = (
            "contradicts_existing_volatility_timing_premise: de-risked states "
            "are followed by higher next-period returns on both predefined "
            "diagnostic measures in >=3/4 datasets."
        )
    else:
        decision = (
            "forward_return_relationship_inconclusive: neither favorable nor "
            "adverse de-risking relationships reach the >=3/4 replication "
            "threshold."
        )

    return {
        "replication_counts": {
            "favorable": favorable,
            "adverse": adverse,
            "mixed": mixed,
        },
        "decision_rule": decision,
    }


def analyze(source_root: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    cases: dict[str, Any] = {}
    for case in CASES:
        rows = _load_rows(source_root, case)
        simulated = base._simulate(rows, 1.0, True, False)
        stats = _forward_stats(simulated, rows)
        cases[case["name"]] = {
            "source": {
                "validation_run_id": case["run_id"],
                "artifact_id": case["artifact_id"],
            },
            "forward_stats": stats,
            "classification": _classify({"forward_stats": stats}),
            "research_only_assertion": (
                len(rows) == RESEARCH_COUNT + base.HOLDOUT_COUNT
                and len(simulated) == RESEARCH_COUNT + base.HOLDOUT_COUNT
            ),
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "risk_layer_following_return_relationship_2026_09_24",
        "status": "COMPLETED",
        "question": (
            "Does the existing 63-session de-risking state align with lower "
            "subsequent unscaled portfolio returns, as a necessary empirical "
            "premise for volatility timing?"
        ),
        "scope": {
            "datasets": 4,
            "research_return_count_per_dataset": RESEARCH_COUNT,
            "research_transition_count_per_dataset": RESEARCH_COUNT - 1,
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
            "risk_layer": "existing 63-session / 10% volatility budget",
            "conditioning_state": "scale_at_t < 1 versus scale_at_t == 1",
            "forward_return": "next-period gross_open net of baseline fee+slippage costs, unscaled",
            "mean_relationship": "mean forward return after de-risk <= mean forward return after full risk",
            "positive_rate_relationship": "next-period positive-rate after de-risk <= positive-rate after full risk",
            "same_candidate": True,
            "same_pit_semantics": True,
            "same_cost_model": True,
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

    print("FOLLOWING_RETURN_DIAGNOSIS_STATUS:", result["status"])
    print("CONSENSUS:", result["consensus"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
