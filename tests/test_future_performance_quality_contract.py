from __future__ import annotations

from pathlib import Path

from automation.future_performance_quality_contract_check import validate

ROOT = Path(__file__).resolve().parents[1]
from automation.research_os_scheduler import build_plan


def test_future_performance_contract_is_currently_clean():
    result = validate()
    assert result["status"] == "PASS"


def test_future_formal_authorization_requires_universal_candidate_gate(tmp_path):
    import json
    import pytest
    from automation.future_performance_quality_contract_check import validate as validate_contract

    root = tmp_path
    (root / "research/governance").mkdir(parents=True)
    (root / "research/preregistrations").mkdir(parents=True)
    policy = json.loads((ROOT / "research/governance/critical_research_quality_control.json").read_text(encoding="utf-8"))
    (root / "research/governance/critical_research_quality_control.json").write_text(json.dumps(policy), encoding="utf-8")
    trial_id = "T-2026-10-03-GATE-TEST"
    prereg = {
        "trial_id": trial_id,
        "robustness_contract": {
            "required_dimensions": policy["early_robustness"]["required_dimensions"],
            "research_only_before_formal_pass": True,
        },
        "independent_replication": {
            "trial_id": trial_id,
            "preregistration_path": "research/preregistrations/gate_test_replication.json",
            "trigger_path": "research/run_requests/gate_test_replication.trigger",
            "fresh_symbol_disjoint": True,
            "no_post_pass_optimization": True,
        },
    }
    (root / "research/preregistrations/gate_test.json").write_text(json.dumps(prereg), encoding="utf-8")
    (root / "research/preregistrations/gate_test_replication.json").write_text(json.dumps(prereg), encoding="utf-8")
    (root / "research/governance/active_research_registry.json").write_text(
        json.dumps({
            "active_trials": [{
                "code": "GATE",
                "trial_id": trial_id,
                "state": "PERFORMANCE_AUTHORIZED",
                "performance_authorization_allowed": True,
                "preregistration_path": "research/preregistrations/gate_test.json",
            }]
        }),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="universal candidate robustness gate"):
        validate_contract(root)


def test_research_scheduler_selects_only_orthogonal_tracks():
    plan = build_plan(run_number=1)
    assert plan["quality_controls"]["orthogonal_only"] is True
    minimum = plan["quality_controls"]["minimum_scheduler_novelty_distance"]
    for assignment in plan["assignments"]:
        track = next(t for t in plan["tracks"] if t["id"] == assignment["track_id"])
        assert track["mechanism_novelty_distance"] >= minimum
    assert "holdout_return" in plan["forbidden_inputs"]
    assert "performance_rank" in plan["forbidden_inputs"]
    assert plan["resource_policy"]["performance_authorization"] is False
