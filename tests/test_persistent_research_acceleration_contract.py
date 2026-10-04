import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_persistent_acceleration_contract_is_active_and_safe():
    payload = json.loads(
        (ROOT / "research" / "governance" / "persistent_research_acceleration_contract.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["status"] == "ACTIVE"
    assert payload["trigger"] == "trading agent"
    assert payload["parallelism_policy"]["self_hosted_windows"]["parallel_lanes"] == 2
    assert payload["parallelism_policy"]["self_hosted_windows"]["autonomous_frontier_default_workers"] == 3
    assert set(payload["parallelism_policy"]["self_hosted_windows"]["lane_roles"]) == {
        "lane_a_formal_readiness", "lane_b_frontier_discovery"
    }
    assert payload["parallelism_policy"]["lane_isolation"]["required"] is True
    assert payload["parallelism_policy"]["self_hosted_windows"]["hard_worker_cap"] == 4
    assert payload["phone_capacity_policy"]["decision"].startswith("Do not add another physical phone")
    assert payload["non_negotiable_safety"] == {
        "PAPER_ONLY": True,
        "LIVE_TRADING_ENABLED": False,
        "ORDERS_ENABLED": False,
        "AUTOMATIC_PROMOTION": False,
        "paid_resources_allowed": False,
    }


def test_new_chat_entrypoint_binds_acceleration_contract():
    text = (ROOT / "docs" / "TRADING_AGENT_CHAT_ENTRYPOINT.md").read_text(encoding="utf-8")
    assert "persistent_research_acceleration_contract.json" in text
    assert "Dauerhafte Beschleunigungslogik" in text
    assert "Ein zusätzliches Mobiltelefon ist derzeit keine Voraussetzung" in text
    assert "Lane A" in text
    assert "Lane B" in text


def test_os_state_binds_acceleration_contract_and_s10_event_review():
    payload = json.loads(
        (ROOT / "ops" / "trading_agent_os_state.json").read_text(encoding="utf-8")
    )
    assert payload["orchestration_policy"]["persistent_acceleration_contract"] == (
        "research/governance/persistent_research_acceleration_contract.json"
    )
    assert payload["autonomous_lanes"]["permanent_self_hosted_research"]["parallel_lanes"] == 2
    assert payload["autonomous_lanes"]["permanent_self_hosted_research"]["purpose"] == [
        "lane_a_formal_readiness", "lane_b_frontier_discovery"
    ]
    assert payload["two_lane_research_mode"]["status"] == "ACTIVE"
    assert payload["resource_routing"]["s10"]["event_driven_review"] == (
        "meaningful research-runner or critical-governance change plus regular two-hour mechanical-QA cadence; semantic review remains explicit"
    )
    assert payload["chatless_night_policy"]["s10"]["event_driven_review"] is True

def test_s10_defaults_to_mechanical_qa_in_phone_workflow():
    text = (ROOT / ".github" / "workflows" / "s10-phone-worker.yml").read_text(encoding="utf-8")
    assert 'cron: "0 */2 * * *"' in text
    assert 'default: "mechanical_qa"' in text
    assert "S10_TASK:" in text
    assert "mechanical_qa" in text
    assert "automation.s10_mechanical_research_qa" in text
