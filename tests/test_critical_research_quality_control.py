from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "research/governance/critical_research_quality_control.json"


def test_critical_research_policy_is_fail_closed():
    p = json.loads(POLICY.read_text(encoding="utf-8"))
    assert p["status"] == "ACTIVE"
    assert p["early_robustness"]["required_before_future_performance_authorization"] is True
    assert p["immediate_replication"]["required_for_any_future_full_formal_pass"] is True
    assert p["immediate_replication"]["failure_mode"].startswith(
        "If a replication contract is missing"
    )
    assert p["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "paid_resources_allowed": False,
    }


def test_robustness_dimensions_cover_failure_modes_seen_in_project():
    p = json.loads(POLICY.read_text(encoding="utf-8"))
    dims = set(p["early_robustness"]["required_dimensions"])
    required = {
        "research_and_holdout_return",
        "research_and_holdout_drawdown",
        "profit_factor",
        "rolling_profit_factor",
        "rolling_profitable_window_ratio",
        "rolling_average_drawdown",
        "oos_to_is_return_ratio",
        "cost_stress_1_5x",
        "cost_stress_2x",
        "total_return_sensitivity",
        "turnover",
        "concentration_hhi",
        "market_correlation",
        "underwater_fraction",
        "regime_decomposition",
    }
    assert required <= dims


def test_orthogonal_search_forbids_holdout_driven_scheduler_selection():
    p = json.loads(POLICY.read_text(encoding="utf-8"))
    forbidden = set(p["orthogonal_search"]["forbidden_scheduler_inputs"])
    assert {"holdout_return", "holdout_drawdown", "performance_rank"} <= forbidden
