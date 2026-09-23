from automation.risk_layer_drawdown_onset_2026_09_23 import (
    CASES,
    RESEARCH_COUNT,
    _classify,
)


def test_source_contract_is_fixed_to_four_prior_validations():
    assert RESEARCH_COUNT == 2798
    assert [case["artifact_id"] for case in CASES] == [
        10751817990,
        10740188093,
        10745697729,
        10753545703,
    ]


def test_delayed_classification_requires_three_of_four():
    cases = {
        "validation_1": {
            "activation_lag_drawdown_days": 0,
            "onset_day_de_risk": True,
            "first_two_drawdown_days_both_de_risk": True,
        },
        "validation_2": {
            "activation_lag_drawdown_days": 2,
            "onset_day_de_risk": False,
            "first_two_drawdown_days_both_de_risk": False,
        },
        "validation_3": {
            "activation_lag_drawdown_days": None,
            "onset_day_de_risk": False,
            "first_two_drawdown_days_both_de_risk": False,
        },
        "validation_4": {
            "activation_lag_drawdown_days": 1,
            "onset_day_de_risk": True,
            "first_two_drawdown_days_both_de_risk": True,
        },
    }
    result = _classify(cases)
    assert result["replication_counts"]["delayed_or_never"] == 2
    assert result["replication_counts"]["onset_day_already_de_risked"] == 2
    assert result["decision_rule"].startswith("mixed_risk_layer_onset:")


def test_proactive_classification_requires_three_of_four():
    cases = {
        f"validation_{i}": {
            "activation_lag_drawdown_days": 0,
            "onset_day_de_risk": True,
            "first_two_drawdown_days_both_de_risk": True,
        }
        for i in range(1, 5)
    }
    result = _classify(cases)
    assert result["replication_counts"]["onset_day_already_de_risked"] == 4
    assert result["decision_rule"].startswith("replicated_proactive_risk_layer_onset:")
