from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research" / "governance" / "research_os_source_registry_2026_09_30.json"


def test_research_os_registry_is_machine_readable_and_safe() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"
    assert payload["research_os_version"] == "ROS-0.1"
    assert payload["safety"]["paper_only"] is True
    assert payload["safety"]["live_trading_enabled"] is False
    assert payload["safety"]["orders_enabled"] is False
    assert payload["safety"]["automatic_promotion"] is False
    assert payload["safety"]["paid_resources_allowed"] is False
    assert payload["source_lattice"]
    assert payload["agent_runtime_lattice"]


def test_no_registered_source_is_silently_marked_as_authoritative() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for source in payload["source_lattice"]:
        assert source["pit_fit"]
        assert source["source_url"].startswith("https://")


def test_agent_runtime_is_not_scientific_authority() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for item in payload["agent_runtime_lattice"]:
        assert "adoption_mode" in item
