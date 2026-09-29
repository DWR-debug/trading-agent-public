import json
from pathlib import Path

from automation.q093_q091_cost_attribution_diagnosis import (
    COST_RATE,
    HOLDOUT,
    N,
    PARENT_TRIAL_ID,
    RESEARCH,
    RESULT_FP,
    TRIAL_ID,
)


def test_q093_contract_constants():
    assert TRIAL_ID == "T-2026-09-29-093"
    assert PARENT_TRIAL_ID == "T-2026-09-29-091"
    assert N == 3500
    assert RESEARCH == 2798
    assert HOLDOUT == 700
    assert COST_RATE == 0.0015
    assert len(RESULT_FP) == 64


def test_q093_preregistration_is_diagnostic_only():
    p=Path("research/preregistrations/q093_q091_cost_attribution_diagnosis_2026_09_29.json")
    d=json.loads(p.read_text(encoding="utf-8"))
    assert d["trial_id"] == TRIAL_ID
    assert d["status"] == "PREREGISTERED_DIAGNOSTIC_ONLY"
    assert d["parent_trial_id"] == "T-2026-09-29-091"
    assert d["governance"]["diagnostic_evaluation"] is True
    assert d["governance"]["new_performance_evaluation"] is False
    assert d["governance"]["selection"] is False
    assert d["governance"]["holdout_used_for_selection"] is False
    assert d["governance"]["family_ranking"] is False
    assert d["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
