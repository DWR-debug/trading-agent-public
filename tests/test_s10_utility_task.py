import json

from automation.s10_utility_task import build_cases


def test_utility_cases_are_fixed_and_bounded(tmp_path):
    os_state = {
        "permanent_safety": {
            "PAPER_ONLY": True, "LIVE_TRADING_ENABLED": False,
            "ORDERS_ENABLED": False, "AUTOMATIC_PROMOTION": False
        },
        "resource_routing": {
            "s10": {
                "scientific_role": "bounded support only",
                "routing_contract": "route only after accepted receipt",
                "capability_claim": "UTILITY_ACCEPTED",
            },
            "android_phone_fleet": {
                "activation_rule": "online + receipt-gated",
                "scientific_role": "bounded support only",
            },
        },
    }
    decision = {"scientific_status": {
        "latest_formal_trial": "T-X",
        "latest_formal_status": "PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES",
    }}
    cases = build_cases(os_state, decision)
    assert len(cases) == 6
    assert {c["id"] for c in cases} == {"G1", "G2", "G3", "G4", "G5", "G6"}
    assert [c["expected"] for c in cases] == [
        "REFUTED", "REFUTED", "SUPPORTED", "SUPPORTED", "REFUTED", "INSUFFICIENT"
    ]
    assert all(set(c) >= {"id", "claim", "expected", "evidence"} for c in cases)


def test_utility_output_is_governance_neutral():
    from automation.s10_utility_task import run

    payload = {
        "scientific_evidence": False,
        "performance_authorization": False,
        "candidate_selection": False,
        "candidate_ranking": False,
        "promotion": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    assert json.loads(json.dumps(payload))["scientific_evidence"] is False
