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


def test_future_quality_validator_requires_receipt_contract_for_authorized_entries(tmp_path):
    import automation.future_performance_quality_contract_check as checker

    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    root = tmp_path
    (root / "research/governance").mkdir(parents=True)
    (root / "research/preregistrations").mkdir(parents=True)
    (root / "research/evidence").mkdir(parents=True)
    (root / "research/governance/critical_research_quality_control.json").write_text(
        json.dumps(policy), encoding="utf-8"
    )

    trial_id = "T-2026-10-03-X01"
    prereg_path = root / "research/preregistrations/x01_performance.json"
    base = {
        "trial_id": trial_id,
        "governance": {"performance_trial_authorized": False},
        "robustness_contract": {
            "required_dimensions": policy["early_robustness"]["required_dimensions"],
            "research_only_before_formal_pass": True,
        },
        "independent_replication": {
            "trial_id": trial_id,
            "preregistration_path": "research/preregistrations/x01_replication.json",
            "trigger_path": "research/run_requests/x01_replication.trigger",
            "fresh_symbol_disjoint": True,
            "no_post_pass_optimization": True,
        },
    }
    prereg_path.write_text(json.dumps(base), encoding="utf-8")
    (root / "research/preregistrations/x01_replication.json").write_text(json.dumps(base), encoding="utf-8")
    (root / "research/governance/active_research_registry.json").write_text(
        json.dumps({
            "active_trials": [{
                "code": "X01",
                "trial_id": trial_id,
                "state": "PERFORMANCE_AUTHORIZED",
                "performance_authorization_allowed": True,
                "preregistration_path": "research/preregistrations/x01_performance.json",
            }]
        }),
        encoding="utf-8",
    )

    with __import__("pytest").raises(RuntimeError, match="pre_performance_robustness"):
        checker.validate(root)

def test_project_integrity_binds_future_quality_validator():
    text = (
        (ROOT / "automation" / "project_integrity_check.py")
        .read_text(encoding="utf-8")
    )
    assert "future_performance_quality_contract_check import validate" in text
    assert "future performance quality validator returned non-PASS" in text


def test_orthogonal_search_forbids_holdout_driven_scheduler_selection():
    p = json.loads(POLICY.read_text(encoding="utf-8"))
    forbidden = set(p["orthogonal_search"]["forbidden_scheduler_inputs"])
    assert {"holdout_return", "holdout_drawdown", "performance_rank"} <= forbidden


def test_future_quality_validator_rebuilds_candidate_gate_from_frozen_inventory(tmp_path):
    import automation.candidate_robustness_gate as gate
    import automation.future_performance_quality_contract_check as checker

    root = tmp_path
    (root / "research/governance").mkdir(parents=True)
    (root / "research/preregistrations").mkdir(parents=True)
    (root / "research/evidence").mkdir(parents=True)
    (root / "research/run_requests").mkdir(parents=True)

    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    (root / "research/governance/critical_research_quality_control.json").write_text(
        json.dumps(policy), encoding="utf-8"
    )

    inventory = {
        "status": "DESIGN_INVENTORY_ONLY",
        "candidates": [{
            "id": "X01-CANDIDATE",
            "name": "synthetic safe candidate",
            "hypothesis": "fixed deterministic test hypothesis",
            "construction": "frozen deterministic PIT construction",
            "sources": ["synthetic_public_source"],
            "next_gate": "source_feasibility",
        }],
    }
    inventory_path = root / "research/frontier/x01_inventory.json"
    inventory_path.parent.mkdir(parents=True)
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

    receipt = gate.compile_receipt(
        [inventory_path],
        "research/evidence/candidate_gate/X01.json",
        root=root,
    )
    item = receipt["candidates"][0]

    trial_id = "T-2026-10-03-X01"
    robustness_artifact_path = root / "research/evidence/x01_pre_performance.json"
    robustness_artifact_path.write_text(
        json.dumps({
            "trial_id": trial_id,
            "status": "PRE_PERFORMANCE_ROBUSTNESS_COMPLETED",
            "metrics": {
                name: True for name in policy["early_robustness"]["required_dimensions"]
            },
            "governance": {
                "holdout_selection": False,
                "parameter_search": False,
                "asset_search": False,
                "threshold_search": False,
                "horizon_search": False,
                "variant_search": False,
                "family_ranking": False,
                "promotion_decision": False,
                "performance_authorization": False,
            },
        }),
        encoding="utf-8",
    )

    prereg = {
        "trial_id": trial_id,
        "candidate_id": item["candidate_id"],
        "candidate_robustness_gate": {
            "receipt_path": "research/evidence/candidate_gate/X01.json",
            "candidate_inventory_path": "research/frontier/x01_inventory.json",
            "bundle_fingerprint": receipt["bundle_fingerprint"],
            "candidate_fingerprint": item["candidate_fingerprint"],
        },
        "robustness_contract": {
            "required_dimensions": policy["early_robustness"]["required_dimensions"],
            "research_only_before_formal_pass": True,
        },
        "pre_performance_robustness": {
            "trial_id": trial_id,
            "status": "PRE_PERFORMANCE_ROBUSTNESS_COMPLETED",
            "artifact_path": "research/evidence/x01_pre_performance.json",
            "artifact_sha256": __import__("hashlib").sha256(
                robustness_artifact_path.read_bytes()
            ).hexdigest(),
            "research_only": True,
            "screen_is_descriptive_only": True,
            "no_post_hoc_tuning": True,
        },
        "independent_replication": {
            "trial_id": trial_id,
            "preregistration_path": "research/preregistrations/x01_replication.json",
            "trigger_path": "research/run_requests/x01_replication.trigger",
            "fresh_symbol_disjoint": True,
            "no_post_pass_optimization": True,
        },
    }
    (root / "research/preregistrations/x01_performance.json").write_text(
        json.dumps(prereg), encoding="utf-8"
    )
    (root / "research/preregistrations/x01_replication.json").write_text(
        json.dumps(prereg), encoding="utf-8"
    )
    (root / "research/governance/active_research_registry.json").write_text(
        json.dumps({
            "active_trials": [{
                "code": "X01",
                "trial_id": trial_id,
                "state": "PERFORMANCE_AUTHORIZED",
                "performance_authorization_allowed": True,
                "preregistration_path": "research/preregistrations/x01_performance.json",
            }]
        }),
        encoding="utf-8",
    )

    assert not (root / "research/evidence/candidate_gate/X01.json").exists()
    result = checker.validate(root)
    assert result["status"] == "PASS"
    assert result["authorized_entries_checked"] == 1
