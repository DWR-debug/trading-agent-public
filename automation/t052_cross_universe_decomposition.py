"""Q028 diagnostic-only cross-universe versus cross-sleeve decomposition for T052."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_TRIAL = "T-2026-09-27-052"
SLEEVES = ("trend_sma_50_200", "cs_momentum_12_1_top2")
UNIVERSES = ("T-2026-09-27-049", "T-2026-09-27-050")


def load_result(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("trial_id") != EXPECTED_TRIAL or data.get("status") != "COMPLETED":
        raise ValueError("unexpected or incomplete T052 result")
    gov = data.get("governance", {})
    if any(gov.get(k) is not False for k in (
        "selection_used",
        "parameter_search",
        "asset_search",
        "threshold_search",
        "horizon_search",
        "variant_search",
        "holdout_used_for_selection",
        "automatic_promotion",
    )):
        raise ValueError("T052 governance contract is not fixed")
    return data


def decompose(data: dict) -> dict:
    failure_sets = {}
    for universe_id in UNIVERSES:
        failure_sets[universe_id] = {}
        for sleeve in SLEEVES:
            failure_sets[universe_id][sleeve] = {
                k for k, v in data["universes"][universe_id][sleeve]["gates"].items() if not v
            }

    cross_sleeve = {}
    for universe_id in UNIVERSES:
        a = failure_sets[universe_id][SLEEVES[0]]
        b = failure_sets[universe_id][SLEEVES[1]]
        cross_sleeve[universe_id] = {
            "shared_between_sleeves": sorted(a & b),
            "trend_only": sorted(a - b),
            "cs_only": sorted(b - a),
        }

    cross_universe_shared = sorted(
        failure_sets[UNIVERSES[0]][SLEEVES[0]]
        & failure_sets[UNIVERSES[0]][SLEEVES[1]]
        & failure_sets[UNIVERSES[1]][SLEEVES[0]]
        & failure_sets[UNIVERSES[1]][SLEEVES[1]]
    )
    universe_specific = {
        "T049_only_shared_between_its_two_sleeves": sorted(
            (
                failure_sets["T-2026-09-27-049"][SLEEVES[0]]
                & failure_sets["T-2026-09-27-049"][SLEEVES[1]]
            )
            - set(cross_universe_shared)
        ),
        "T050_only_shared_between_its_two_sleeves": sorted(
            (failure_sets["T-2026-09-27-050"][SLEEVES[0]]
             & failure_sets["T-2026-09-27-050"][SLEEVES[1]])
            - set(cross_universe_shared)
        ),
    }
    return {
        "trial_id": EXPECTED_TRIAL,
        "source_result_fingerprint": data["report_fingerprint"],
        "cross_sleeve": cross_sleeve,
        "cross_universe_shared_failure_gates": cross_universe_shared,
        "universe_specific_shared_failures": universe_specific,
        "interpretation": {
            "diagnostic_only": True,
            "ranking_or_selection": False,
            "causal_claim": False,
            "statement": "Failure-pattern similarity within each fixed universe and differences between universes are descriptive only; they do not identify a causal driver."
        },
        "governance": {
            "selection_used": False,
            "ranking_used": False,
            "holdout_used_for_selection": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "variant_search": False,
            "promotion_decision": False,
        },
        "safety": data["safety"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    data = load_result(args.result)
    out = decompose(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "COMPLETED_DIAGNOSTIC_ONLY",
        "cross_universe_shared_count": len(out["cross_universe_shared_failure_gates"]),
        "cross_universe_shared_failure_gates": out["cross_universe_shared_failure_gates"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
