from automation.rccsm_synthetic import synthetic_scenarios, synthetic_validation


def test_rccsm1_scenarios_are_frozen_and_unique() -> None:
    scenarios = synthetic_scenarios()
    ids = [item["state_id"] for item in scenarios]
    assert ids == [
        "RCCSM-SYN-TREND",
        "RCCSM-SYN-REVERSAL",
        "RCCSM-SYN-EVENT",
        "RCCSM-SYN-SILENT",
    ]
    assert len(ids) == len(set(ids))


def test_rccsm1_structural_expectations_pass() -> None:
    result = synthetic_validation()
    assert result["component"] == "RCCSM-1"
    assert result["performance_authorized"] is False
    assert result["uses_returns"] is False
    assert result["uses_holdout"] is False
    assert result["uses_optimizer"] is False
    assert result["scenario_count"] == 4
    assert result["all_structural_expectations_pass"] is True
    assert all(item["pass"] for item in result["results"])


def test_rccsm1_replay_is_deterministic() -> None:
    assert synthetic_validation() == synthetic_validation()
