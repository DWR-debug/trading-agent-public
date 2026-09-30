from __future__ import annotations

import json
from pathlib import Path


def test_c29_performance_preregistration_is_fixed_and_nonselective() -> None:
    spec = json.loads(
        Path("research/preregistrations/c29_performance_2026_09_30.json")
        .read_text(encoding="utf-8")
    )
    assert spec["trial_id"] == "T-2026-09-30-C29-PERFORMANCE-01"
    assert spec["status"] in {"PREREGISTERED_DESIGN_ONLY", "PREREGISTERED_PERFORMANCE"}
    assert spec["symbols"] == ["PPG", "GWW", "PGR", "TT", "ICE", "KLAC", "SNA", "SWK"]
    assert spec["data_contract"]["evaluation_periods"] == 3478
    assert spec["data_contract"]["research_periods"] == 2778
    assert spec["data_contract"]["holdout_periods"] == 700
    assert spec["mechanism_contract"]["lookback_sessions"] == 21
    assert spec["arms"]["C29_HIGH_GAP_LONG_TOP4"]["selection"] == "four highest C29 scores each decision session"
    assert spec["arms"]["C29_LOW_GAP_LONG_BOTTOM4"]["selection"] == "four lowest C29 scores each decision session"
    assert spec["execution_contract"]["turnover"] == "sum absolute target-weight changes across the eight symbols; initial target is zero"
    assert spec["governance"]["selection"] is False
    assert spec["governance"]["holdout_used_for_selection"] is False
    if spec["status"] == "PREREGISTERED_DESIGN_ONLY":
        assert spec["governance"]["performance_trial_authorized"] is False
    else:
        assert spec["governance"]["performance_trial_authorized"] is True
        assert spec["authorization"]["current_status"] == "AUTHORIZED_ONE_SHOT"
        assert spec["authorization"]["performance_trial_authorized"] is True
        assert spec["authorization"]["authorization_id"] == "AUTH-C29-2026-09-30-01"
    assert spec["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def test_c29_performance_source_has_no_unused_authority_placeholder() -> None:
    source = Path("automation/c29_performance.py").read_text(encoding="utf-8")
    assert "scenario-aware gate computation required" not in source
    assert 'TRIAL_ID = "T-2026-09-30-C29-PERFORMANCE-01"' in source
    assert 'ARMS = ("C29_HIGH_GAP_LONG_TOP4", "C29_LOW_GAP_LONG_BOTTOM4")' in source
    assert 'previous_weights = {symbol: 0.0 for symbol in SYMBOLS}' in source
    assert 'turnover = sum(abs(weights[symbol] - previous_weights[symbol])' in source


def test_c29_active_registry_matches_authorization_state() -> None:
    reg = json.loads(
        Path("research/governance/active_research_registry.json").read_text(
            encoding="utf-8"
        )
    )
    entry = next(x for x in reg["active_trials"] if x.get("code") == "C29P1")
    assert entry["trial_id"] == "T-2026-09-30-C29-PERFORMANCE-01"
    assert entry["state"] in {
        "PERFORMANCE_READY_FOR_AUTHORIZATION",
        "PERFORMANCE_AUTHORIZED",
    }
    if entry["state"] == "PERFORMANCE_READY_FOR_AUTHORIZATION":
        assert entry["performance_authorization_allowed"] is False
    else:
        assert entry["performance_authorization_allowed"] is True
        assert entry["authorization_id"] == "AUTH-C29-2026-09-30-01"
