import json
from pathlib import Path

from portfolio.q094_monthly_rebalance import (
    MONTHLY_E1_ID,
    MONTHLY_E2_ID,
    VARIANTS,
    is_first_trading_session_of_month,
)


def test_q094_variant_contract():
    assert VARIANTS == (MONTHLY_E1_ID, MONTHLY_E2_ID)
    assert MONTHLY_E1_ID == "M1_MONTHLY_REBALANCED_Q091_E1"
    assert MONTHLY_E2_ID == "M2_MONTHLY_REBALANCED_Q091_E2"


def test_q094_preregistration_is_fixed_and_non_performance():
    p=Path("research/preregistrations/q094_monthly_rebalance_q091_low_turnover_2026_09_29.json")
    d=json.loads(p.read_text(encoding="utf-8"))
    assert d["trial_id"]=="T-2026-09-29-094"
    assert d["status"]=="PREREGISTERED_DESIGN_ONLY"
    assert d["rebalance_contract"]["schedule"]=="first_available_trading_session_of_each_calendar_month"
    assert d["rebalance_contract"]["cadence_parameter_search"] is False
    assert d["governance"]["performance_trial_authorized"] is False
    assert d["governance"]["selection"] is False
    assert d["governance"]["holdout_used_for_selection"] is False
    assert d["safety"]=={
        "paper_only":True,
        "live_trading_enabled":False,
        "orders_enabled":False,
        "automatic_promotion":False,
    }


def test_q094_month_boundary_detection():
    class Bar:
        def __init__(self, y, m, d):
            from datetime import datetime, timezone
            self.timestamp=datetime(y,m,d,tzinfo=timezone.utc)
    bars=[Bar(2020,1,31),Bar(2020,2,3),Bar(2020,2,4)]
    assets={"X":bars,"Y":[Bar(2020,1,31),Bar(2020,2,3),Bar(2020,2,4)]}
    assert is_first_trading_session_of_month(assets,0,["X","Y"]) is True
    assert is_first_trading_session_of_month(assets,1,["X","Y"]) is True
    assert is_first_trading_session_of_month(assets,2,["X","Y"]) is False
