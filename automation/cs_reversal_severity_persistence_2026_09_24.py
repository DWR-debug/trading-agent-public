"""Research-only diagnosis of the replicated CS winner-reversal mechanism.

Consumes the same four immutable validation artifacts as the prior diagnosis.
It measures continuous reversal severity, consecutive reversal runs and the
fixed 21-session CS rebalance phase. It never mutates strategy or gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from automation import signal_reversal_rebound_diagnosis_2026_09_24 as base
from config import settings

RESEARCH_COUNT = base.RESEARCH_COUNT
CS_REBALANCE_SESSIONS = 21
WORST_DAY_BUCKET_PERCENT = 5

CASES = (
    {
        "name": "validation_1",
        "artifact_id": 10751817990,
        "run_id": 35865847394,
        "root": "research/candidate_validation",
        "trend_universe": "validation_trend",
        "cs_universe": "validation_cs",
    },
    {
        "name": "validation_2",
        "artifact_id": 10740188093,
        "run_id": 35839443616,
        "root": "research/independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_trend",
        "cs_universe": "validation_2026_09_23_cs",
    },
    {
        "name": "validation_3",
        "artifact_id": 10745697729,
        "run_id": 35851876264,
        "root": "research/third_independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_third_trend",
        "cs_universe": "validation_2026_09_23_third_cs",
    },
    {
        "name": "validation_4",
        "artifact_id": 10753545703,
        "run_id": 35867637587,
        "root": "research/fourth_independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_fourth_trend",
        "cs_universe": "validation_2026_09_23_fourth_cs",
    },
)


def _canon(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _state_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    research = rows[:RESEARCH_COUNT]
    state = [
        row for row in research
        if row["cs_winner_reversal"]
        and row["cs_winner_loser_spread"] is not None
    ]
    non_state = [
        row for row in research
        if not row["cs_winner_reversal"]
        and row["cs_winner_loser_spread"] is not None
    ]
    if not state or not non_state:
        raise ValueError("Both reversal and non-reversal populations are required.")

    state_spreads = [row["cs_winner_loser_spread"] for row in state]
    non_spreads = [row["cs_winner_loser_spread"] for row in non_state]

    worst_count = max(
        1,
        (len(research) * WORST_DAY_BUCKET_PERCENT + 99) // 100,
    )
    worst = sorted(
        research,
        key=lambda row: row["portfolio_net_return"],
    )[:worst_count]

    total_negative_mass = sum(
        max(-row["portfolio_net_return"], 0.0) for row in research
    )
    reversal_negative_mass = sum(
        max(-row["portfolio_net_return"], 0.0) for row in state
    )

    mean_state = statistics.mean(state_spreads)
    mean_non = statistics.mean(non_spreads)

    return {
        "reversal_observations": len(state),
        "reversal_fraction": len(state) / len(research),
        "mean_winner_loser_spread": mean_state,
        "median_winner_loser_spread": statistics.median(state_spreads),
        "minimum_winner_loser_spread": min(state_spreads),
        "non_reversal_observations": len(non_state),
        "mean_non_reversal_winner_loser_spread": mean_non,
        "mean_spread_difference_reversal_minus_non_reversal": mean_state - mean_non,
        "worst_5pct_reversal_observations": sum(
            row["cs_winner_reversal"] for row in worst
        ),
        "worst_5pct_reversal_fraction": sum(
            row["cs_winner_reversal"] for row in worst
        ) / len(worst),
        "worst_5pct_enrichment_ratio": (
            (sum(row["cs_winner_reversal"] for row in worst) / len(worst))
            / (len(state) / len(research))
        ),
        "negative_portfolio_return_mass_share": (
            reversal_negative_mass / total_negative_mass
            if total_negative_mass > 0.0
            else None
        ),
        "reversal_days_with_negative_portfolio_return": sum(
            row["portfolio_net_return"] < 0.0 for row in state
        ),
    }


def _runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    research = rows[:RESEARCH_COUNT]
    result: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []

    def flush() -> None:
        if not current:
            return
        spreads = [row["cs_winner_loser_spread"] for row in current]
        result.append(
            {
                "length_sessions": len(current),
                "start_index": current[0]["index"],
                "end_index_inclusive": current[-1]["index"],
                "start_timestamp": current[0]["timestamp"].isoformat(),
                "end_timestamp": current[-1]["timestamp"].isoformat(),
                "cumulative_winner_loser_spread": sum(spreads),
                "mean_winner_loser_spread": statistics.mean(spreads),
                "minimum_winner_loser_spread": min(spreads),
                "cumulative_portfolio_return": sum(
                    row["portfolio_net_return"] for row in current
                ),
            }
        )
        current.clear()

    for index, row in enumerate(research):
        if row["cs_winner_reversal"]:
            enriched = dict(row)
            enriched["index"] = index
            current.append(enriched)
        else:
            flush()
    flush()
    return result


def _run_summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not runs:
        return {
            "run_count": 0,
            "mean_length_sessions": None,
            "median_length_sessions": None,
            "maximum_length_sessions": 0,
            "length_distribution": {},
            "mean_cumulative_winner_loser_spread": None,
            "median_cumulative_winner_loser_spread": None,
            "most_negative_cumulative_winner_loser_spread": None,
        }

    lengths = [int(run["length_sessions"]) for run in runs]
    cumulative = [
        float(run["cumulative_winner_loser_spread"]) for run in runs
    ]
    return {
        "run_count": len(runs),
        "mean_length_sessions": statistics.mean(lengths),
        "median_length_sessions": statistics.median(lengths),
        "maximum_length_sessions": max(lengths),
        "length_distribution": dict(sorted(Counter(lengths).items())),
        "mean_cumulative_winner_loser_spread": statistics.mean(cumulative),
        "median_cumulative_winner_loser_spread": statistics.median(cumulative),
        "most_negative_cumulative_winner_loser_spread": min(cumulative),
    }


def _phase(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    research = rows[:RESEARCH_COUNT]
    counts = Counter()
    reversal_counts = Counter()
    negative_counts = Counter()
    spreads: dict[int, list[float]] = {
        phase: [] for phase in range(CS_REBALANCE_SESSIONS)
    }

    for index, row in enumerate(research):
        phase = index % CS_REBALANCE_SESSIONS
        counts[phase] += 1
        reversal_counts[phase] += int(row["cs_winner_reversal"])
        negative_counts[phase] += int(row["portfolio_net_return"] < 0.0)
        if row["cs_winner_loser_spread"] is not None:
            spreads[phase].append(row["cs_winner_loser_spread"])

    return [
        {
            "phase_session": phase,
            "observation_count": counts[phase],
            "reversal_observation_count": reversal_counts[phase],
            "reversal_rate": reversal_counts[phase] / counts[phase],
            "negative_portfolio_day_rate": negative_counts[phase] / counts[phase],
            "mean_winner_loser_spread": statistics.mean(spreads[phase]),
        }
        for phase in range(CS_REBALANCE_SESSIONS)
    ]


def _case_analysis(
    trend: dict[str, tuple],
    cs: dict[str, tuple],
) -> dict[str, Any]:
    rows = base._case_rows(trend, cs)
    runs = _runs(rows)
    return {
        "summary": _state_summary(rows),
        "runs": _run_summary(runs),
        "run_details": runs,
        "rebalance_phase": _phase(rows),
    }


def _consensus(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    severity_direction = sum(
        case["analysis"]["summary"][
            "mean_spread_difference_reversal_minus_non_reversal"
        ] < 0.0
        for case in cases.values()
    )
    worst_enriched = sum(
        case["analysis"]["summary"]["worst_5pct_enrichment_ratio"] > 1.0
        for case in cases.values()
    )
    return {
        "replication_counts": {
            "negative_reversal_spread_difference": severity_direction,
            "worst_5pct_reversal_enriched": worst_enriched,
        },
        "diagnostic_rule": (
            "Counts only reproduce fixed descriptive directions across the "
            "four validations. Persistence and 21-session phase are reported "
            "without selecting a favored run length or phase."
        ),
        "interpretation": (
            "severity_direction_replicated"
            if severity_direction >= 3
            else "severity_direction_not_replicated"
        ),
        "persistence_reporting_only": True,
        "phase_reporting_only": True,
    }


def analyze(source_root: Path) -> dict[str, Any]:
    if (
        settings.PAPER_ONLY is not True
        or settings.LIVE_TRADING_ENABLED is not False
    ):
        raise RuntimeError("Paper-only safety contract violated.")

    cases: dict[str, Any] = {}
    for case in CASES:
        trend, cs = base._load_case(source_root, case)
        cases[case["name"]] = {
            "source": {
                "artifact_id": case["artifact_id"],
                "run_id": case["run_id"],
            },
            "analysis": _case_analysis(trend, cs),
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "cs_reversal_severity_persistence_2026_09_24",
        "status": "COMPLETED",
        "question": (
            "Ist der replizierte Cross-Sectional-Winner-Reversal-Befund "
            "durch festen Reversal-Schweregrad, Persistenz und/oder "
            "eine bestimmte 21-Session-Rebalance-Phase charakterisiert?"
        ),
        "scope": {
            "datasets": 4,
            "research_return_count_per_dataset": RESEARCH_COUNT,
            "holdout_used_for_decision": False,
            "holdout_metrics_reported": False,
            "new_data_downloads": False,
            "parameter_search": False,
            "asset_selection": False,
            "strategy_mutation": False,
            "gate_changes": False,
            "production_mutation": False,
        },
        "methodology": {
            "candidate_architecture_fixed": True,
            "cs_lookback_sessions": base.base.CS_LOOKBACK,
            "cs_skip_sessions": base.base.CS_SKIP,
            "cs_rebalance_sessions": CS_REBALANCE_SESSIONS,
            "cs_top_n": base.base.CS_TOP_N,
            "reversal_state": (
                "fixed top-2 CS winners minus equal-weighted non-selected "
                "CS assets, current open-to-open return < 0"
            ),
            "severity": "continuous winner-to-nonwinner spread; no threshold search",
            "persistence": "consecutive Research rows with the fixed reversal flag form one run",
            "phase": "Research-row index modulo the fixed 21-session CS cycle; descriptive only",
            "worst_bucket_percent": WORST_DAY_BUCKET_PERCENT,
            "replication_threshold": ">=3/4 validations",
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
    # Fingerprint the exact JSON-representable form that will be persisted.
    # This keeps verification stable across dict-key/type normalization.
    result = json.loads(
        json.dumps(
            result,
            ensure_ascii=False,
            allow_nan=False,
        )
    )
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
    print("CS_REVERSAL_SEVERITY_PERSISTENCE_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    print("CONSENSUS:", result["consensus"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
