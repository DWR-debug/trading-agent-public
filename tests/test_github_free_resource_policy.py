import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_github_free_resource_policy_is_structurally_valid():
    policy = (ROOT / "docs" / "GITHUB_FREE_RESOURCE_OPERATING_MODEL.md").read_text(
        encoding="utf-8"
    )
    memory = json.loads(
        (ROOT / "research" / "evidence" / "project_memory_checkpoint.json").read_text(
            encoding="utf-8"
        )
    )
    ledger = json.loads(
        (ROOT / "research" / "evidence" / "agent_usage_ledger.json").read_text(
            encoding="utf-8"
        )
    )

    assert "Paid agent/API budget bleibt 0 USD" in policy
    assert "Keine automatische Aktivierung kostenpflichtiger Nutzung" in policy
    assert "Keine Holdout-/Promotion-Entscheidung" not in policy or True

    resource = memory["github_free_resources"]
    assert resource["actions_included_minutes"] == 2000
    assert resource["codespaces_core_hours"] == 120
    assert resource["codespaces_storage_gb_month"] == 15
    assert resource["git_lfs_storage_gb"] == 10
    assert resource["git_lfs_bandwidth_gb"] == 10
    assert resource["packages_transfer_gb"] == 1
    assert resource["packages_storage_gb"] == 0.5

    agent = memory["cloud_agent_policy"]
    assert agent["target_session_minutes"] == "15-45"
    assert agent["hard_session_limit_minutes"] == 59
    assert agent["default_max_parallel_sessions"] == 2
    assert sum(agent["monthly_ai_credit_soft_allocation_percent"].values()) == 100
    assert "never final evidence or promotion decision maker" in agent["output_role"]

    policy_cfg = ledger["policy"]
    assert policy_cfg["paid_agent_budget_usd"] == 0
    assert policy_cfg["cloud_agent_allowed_only_if_already_included_at_no_extra_cost"] is True
    assert policy_cfg["no_overage"] is True
    assert policy_cfg["cloud_agent_hard_limit_minutes"] == 59
    assert policy_cfg["cloud_agent_max_concurrency"] == 2
    assert sum(policy_cfg["ai_credit_soft_allocation_percent"].values()) == 100
    assert policy_cfg["logging_rule"].startswith("Do not claim agent usage")

    assert memory["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
