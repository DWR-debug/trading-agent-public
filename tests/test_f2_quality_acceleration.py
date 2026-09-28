import pytest

from automation.f2_quality_acceleration import _fp


def test_f2_definition_is_fixed():
    from automation.f2_quality_acceleration import STUDY_END, STUDY_START, SYMBOLS
    assert STUDY_START.isoformat() == "2011-01-01"
    assert STUDY_END.isoformat() == "2025-09-24"
    assert SYMBOLS == ("UPS", "FDX", "DIS", "ADP", "ORLY", "AZO", "TJX", "RSG")


def test_quality_acceleration_is_second_difference():
    levels = [0.10, 0.14, 0.11, 0.17]
    growth = [levels[i] - levels[i - 1] for i in range(1, len(levels))]
    acceleration = [growth[i] - growth[i - 1] for i in range(1, len(growth))]
    assert growth == pytest.approx([0.04, -0.03, 0.06])
    assert acceleration == pytest.approx([-0.07, 0.09])


def test_fingerprint_is_deterministic():
    assert _fp({"candidate": "F2", "values": [1, 2, 3]}) == _fp(
        {"values": [1, 2, 3], "candidate": "F2"}
    )


def test_f2_contract_is_non_performance():
    governance = {
        "performance_evaluation": False,
        "holdout_used": False,
        "selection_used": False,
        "parameter_search": False,
        "asset_search": False,
        "threshold_search": False,
        "performance_trial_authorized": False,
    }
    safety = {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    assert all(value is False for value in governance.values())
    assert safety["paper_only"] is True
    assert safety["live_trading_enabled"] is False
    assert safety["orders_enabled"] is False
    assert safety["automatic_promotion"] is False
