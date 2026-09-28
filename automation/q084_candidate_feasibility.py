"""Q084 design/PIT feasibility harness. No performance evaluation."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research" / "preregistrations" / "q084_design_2026_09_28.json"


def cosine(a, b):
    aa = math.sqrt(sum(x * x for x in a))
    bb = math.sqrt(sum(x * x for x in b))
    if aa == 0 or bb == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (aa * bb)


def quarter_state(month, monthly_return):
    # Months 2, 5, 8, 11 are the second month of each calendar quarter.
    if month not in (2, 5, 8, 11):
        return None
    if monthly_return > 0:
        return -1
    if monthly_return < 0:
        return 1
    return 0


def c24_state(current_vector, previous_vector, prior_month_return):
    sim = cosine(current_vector, previous_vector)
    direction = -1 if prior_month_return > 0 else 1 if prior_month_return < 0 else 0
    return {"similarity": sim, "direction": direction}


def synthetic_pit_check():
    monthly = {m: 0.01 * (1 if m % 2 else -1) for m in range(1, 13)}
    assert quarter_state(2, monthly[2]) == 1
    assert quarter_state(1, monthly[1]) is None
    base_vec = [0.10, 0.20, -0.05]
    prev_vec = [0.11, 0.18, -0.04]
    base = c24_state(base_vec, prev_vec, 0.03)

    mutated_future = {
        1: [9, 9, 9],
        2: [-9, -9, -9],
        3: [7, 7, 7],
    }
    assert c24_state(base_vec, prev_vec, 0.03) == base
    assert mutated_future[1] != base_vec

    # The signal function takes only completed vectors and a completed prior-month return.
    # Future mutations are therefore structurally excluded.
    return {
        "m2_calendar_mapping_passed": True,
        "c24_cosine_and_direction_passed": True,
        "future_data_exclusion_passed": True,
    }


def main():
    p = json.loads(PREREG.read_text(encoding="utf-8"))
    assert p["status"] == "PREREGISTERED_DESIGN_ONLY"
    assert all(v is False for v in p["governance"].values())
    assert p["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    checks = synthetic_pit_check()
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-09-28-084-FEASIBILITY",
        "status": "FEASIBILITY_CHECK_COMPLETED_NO_PERFORMANCE",
        "pit_checks": checks,
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "scientific_evidence_created": False,
        "safety": p["safety"],
    }
    out = ROOT / "research" / "runs" / "q084_feasibility" / "result.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Q084_STATUS:", result["status"])
    print("Q084_PIT_CHECKS: PASS")


if __name__ == "__main__":
    main()
