from automation.risk_layer_following_return_diagnosis_2026_09_24 import (
    CASES,
    RESEARCH_COUNT,
    _classify,
    _consensus,
)


def test_fixed_diagnostic_contract():
    assert RESEARCH_COUNT == 2798
    assert len(CASES) == 4
    assert [case["artifact_id"] for case in CASES] == [
        10751817990,
        10740188093,
        10745697729,
        10753545703,
    ]


def test_classification_is_sign_based_and_predefined():
    favorable = {
        "forward_stats": {
            "favorable_mean_relationship": True,
            "favorable_positive_rate_relationship": True,
        }
    }
    adverse = {
        "forward_stats": {
            "favorable_mean_relationship": False,
            "favorable_positive_rate_relationship": False,
        }
    }
    mixed = {
        "forward_stats": {
            "favorable_mean_relationship": True,
            "favorable_positive_rate_relationship": False,
        }
    }
    assert _classify(favorable) == "favorable_de_risk_forward_relationship"
    assert _classify(adverse) == "adverse_de_risk_forward_relationship"
    assert _classify(mixed) == "mixed_de_risk_forward_relationship"


def test_consensus_requires_three_of_four():
    favorable = {
        f"validation_{i}": {"classification": "favorable_de_risk_forward_relationship"}
        for i in range(1, 4)
    }
    favorable["validation_4"] = {"classification": "mixed_de_risk_forward_relationship"}
    assert _consensus(favorable)["decision_rule"].startswith(
        "supports_existing_volatility_timing_premise:"
    )

    adverse = {
        f"validation_{i}": {"classification": "adverse_de_risk_forward_relationship"}
        for i in range(1, 4)
    }
    adverse["validation_4"] = {"classification": "mixed_de_risk_forward_relationship"}
    assert _consensus(adverse)["decision_rule"].startswith(
        "contradicts_existing_volatility_timing_premise:"
    )

    mixed = {
        "validation_1": {"classification": "favorable_de_risk_forward_relationship"},
        "validation_2": {"classification": "adverse_de_risk_forward_relationship"},
        "validation_3": {"classification": "mixed_de_risk_forward_relationship"},
        "validation_4": {"classification": "favorable_de_risk_forward_relationship"},
    }
    assert _consensus(mixed)["decision_rule"].startswith(
        "forward_return_relationship_inconclusive:"
    )
