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
    assert payload["parallelism_policy"]["self_hosted_windows"]["autonomous_frontier_default_workers"] == 3
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


def test_os_state_binds_acceleration_contract_and_s10_event_review():
    payload = json.loads(
        (ROOT / "ops" / "trading_agent_os_state.json").read_text(encoding="utf-8")
    )
    assert payload["orchestration_policy"]["persistent_acceleration_contract"] == (
        "research/governance/persistent_research_acceleration_contract.json"
    )
    assert payload["autonomous_lanes"]["permanent_self_hosted_research"]["internal_frontier_workers"] == 3
    assert payload["resource_routing"]["s10"]["event_driven_review"] == (
        "meaningful research-runner or critical-governance change plus regular six-hour cadence"
    )
    assert payload["chatless_night_policy"]["s10"]["event_driven_review"] is True
