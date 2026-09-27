"""Q027 diagnostic-only failure attribution for completed T052.

Reads the immutable T052 result and reports fixed-cell gate failures.
No cell selection, ranking, parameter search, holdout optimization, or
promotion decision is performed.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

EXPECTED_TRIAL = "T-2026-09-27-052"
EXPECTED_CELLS = {
    "T-2026-09-27-049:trend_sma_50_200",
    "T-2026-09-27-049:cs_momentum_12_1_top2",
    "T-2026-09-27-050:trend_sma_50_200",
    "T-2026-09-27-050:cs_momentum_12_1_top2",
}


def load_result(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("trial_id") != EXPECTED_TRIAL:
        raise ValueError("unexpected trial_id")
    if data.get("status") != "COMPLETED":
        raise ValueError("T052 result is not completed")
    if data.get("governance", {}).get("selection_used") is not False:
        raise ValueError("selection_used must be false")
    if data.get("governance", {}).get("holdout_used_for_selection") is not False:
        raise ValueError("holdout selection must be false")
    if data.get("governance", {}).get("parameter_search") is not False:
        raise ValueError("parameter search must be false")
    return data


def attribute(data: dict) -> dict:
    cells = {}
    counts: Counter[str] = Counter()
    for trial_id, universe in data["universes"].items():
        for sleeve in ("trend_sma_50_200", "cs_momentum_12_1_top2"):
            key = f"{trial_id}:{sleeve}"
            failed = sorted(name for name, passed in universe[sleeve]["gates"].items() if not passed)
            cells[key] = {
                "failed_gate_count": len(failed),
                "failed_gates": failed,
                "all_gates_passed": universe[sleeve]["all_gates_passed"],
            }
            counts.update(failed)
    if set(cells) != EXPECTED_CELLS:
        raise ValueError("T052 fixed-cell set changed")
    return {
        "trial_id": EXPECTED_TRIAL,
        "source_result_fingerprint": data["report_fingerprint"],
        "source_code_version": data["code_version"],
        "cell_count": len(cells),
        "cells": cells,
        "gate_failure_counts": dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))),
        "shared_failures_all_cells": sorted(name for name, count in counts.items() if count == len(cells)),
        "governance": {
            "diagnostic_only": True,
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
    result = load_result(args.result)
    output = attribute(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "COMPLETED_DIAGNOSTIC_ONLY",
        "cells": output["cell_count"],
        "shared_failures_all_cells": output["shared_failures_all_cells"],
        "source_result_fingerprint": output["source_result_fingerprint"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
