from pathlib import Path
import json

ROOT = Path(__file__).parents[1]


def test_permanent_contract_defines_slotwise_replenishment():
    data=json.loads((ROOT/"research/governance/persistent_research_acceleration_contract.json").read_text(encoding="utf-8"))
    rule=data["rolling_capacity_wave_control"]["slotwise_replenishment"]
    assert rule["status"]=="PERMANENT"
    assert rule["slot_scoped_workflow"]==".github/workflows/top4-candidate-slot-research.yml"
    assert "ubuntu_x64" in rule["supported_resources"]
    assert "ubuntu_arm64" in rule["supported_resources"]
    assert "windows" in rule["supported_resources"]
    assert rule["implementation"]["legacy_cohort_mode"]=="manual_only"


def test_slotwise_workflow_is_explicitly_non_authorizing():
    text=(ROOT/".github/workflows/top4-candidate-slot-research.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "candidate:" in text
    assert "resource:" in text
    assert "ubuntu-24.04" in text
    assert "ubuntu-24.04-arm" in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "SLOT_RESEARCH_BOUNDARY" in text
    assert "NO_PERFORMANCE" in text
    assert "NO_HOLDOUT" in text
    assert "NO_RANKING" in text
    assert "NO_TUNING" in text
    assert "NO_PROMOTION" in text
    assert "NO_LIVE_EXECUTION" in text


def test_legacy_bundled_top4_is_manual_fallback_only():
    text=(ROOT/".github/workflows/top4-candidate-research-capacity.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "\n  schedule:" not in text
    assert "\n  push:" not in text
