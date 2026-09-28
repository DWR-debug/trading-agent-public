"""Synthetic RCCSM-1 structural scenarios.

These scenarios contain no market returns or performance labels. They test that
frozen routing rules produce the intended structural admissibility map.
"""

from __future__ import annotations

from typing import Any

SYNTHETIC_SCENARIOS: tuple[dict[str, Any], ...] = (
    {
        "state_id": "RCCSM-SYN-TREND",
        "state": {
            "trend_coherence": 0.90,
            "breadth": 0.80,
            "dispersion": 0.20,
            "event_density": 0.10,
        },
        "expected": {
            "cross_sectional_momentum": "ADMISSIBLE",
            "event_timing": "INADMISSIBLE",
            "reversal": "INADMISSIBLE",
            "trend_efficiency": "ADMISSIBLE",
        },
    },
    {
        "state_id": "RCCSM-SYN-REVERSAL",
        "state": {
            "trend_coherence": 0.20,
            "breadth": 0.30,
            "dispersion": 0.80,
            "event_density": 0.10,
        },
        "expected": {
            "cross_sectional_momentum": "INADMISSIBLE",
            "event_timing": "INADMISSIBLE",
            "reversal": "ADMISSIBLE",
            "trend_efficiency": "INADMISSIBLE",
        },
    },
    {
        "state_id": "RCCSM-SYN-EVENT",
        "state": {
            "trend_coherence": 0.20,
            "breadth": 0.30,
            "dispersion": 0.20,
            "event_density": 0.90,
        },
        "expected": {
            "cross_sectional_momentum": "INADMISSIBLE",
            "event_timing": "ADMISSIBLE",
            "reversal": "INADMISSIBLE",
            "trend_efficiency": "INADMISSIBLE",
        },
    },
    {
        "state_id": "RCCSM-SYN-SILENT",
        "state": {
            "trend_coherence": 0.10,
            "breadth": 0.10,
            "dispersion": 0.10,
            "event_density": 0.10,
        },
        "expected": {
            "cross_sectional_momentum": "INADMISSIBLE",
            "event_timing": "INADMISSIBLE",
            "reversal": "INADMISSIBLE",
            "trend_efficiency": "INADMISSIBLE",
        },
    },
)


def synthetic_scenarios() -> tuple[dict[str, Any], ...]:
    return SYNTHETIC_SCENARIOS


def synthetic_validation() -> dict[str, Any]:
    from automation.rccsm_feasibility import route_mesh

    results: list[dict[str, Any]] = []
    for scenario in SYNTHETIC_SCENARIOS:
        actual = {
            item["mechanism_id"]: item["admissibility"]
            for item in route_mesh(scenario["state_id"], scenario["state"])
        }
        results.append(
            {
                "state_id": scenario["state_id"],
                "expected": scenario["expected"],
                "actual": actual,
                "pass": actual == scenario["expected"],
            }
        )
    return {
        "component": "RCCSM-1",
        "performance_authorized": False,
        "uses_returns": False,
        "uses_holdout": False,
        "uses_optimizer": False,
        "scenario_count": len(results),
        "all_structural_expectations_pass": all(item["pass"] for item in results),
        "results": results,
    }
