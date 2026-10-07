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


def test_completion_wakeup_covers_research_workflow_globs_and_six_dispatches():
    workflow = (ROOT / ".github/workflows/planned-capacity-fast-dispatch.yml").read_text(encoding="utf-8")
    assert 'workflow_run:' in workflow
    assert 'types: [completed]' in workflow
    for pattern in ['"Q*"', '"Top-4*"', '"*Research*"', '"*PIT*"', '"*Source*"', '"*Census*"', '"*Frontier*"', '"*Identity*"', '"*Capacity*"', '"*Reproduction*"']:
        assert pattern in workflow
    assert '--max-dispatches 6' in workflow
    assert 'github.event.workflow_run.head_branch == github.event.repository.default_branch' in workflow


def test_completion_wakeup_excludes_control_plane_loops_before_runner_use():
    workflow = (ROOT / ".github/workflows/planned-capacity-fast-dispatch.yml").read_text(encoding="utf-8")
    for name in ['CI', 'Full Suite Verification', 'T052 Exact Master CI Gate', 'Workflow Lint', 'Current Operational Status Synchronizer', 'Resource Dashboard Update', 'Planned Capacity Fast Dispatch']:
        assert name in workflow


def test_fast_dispatch_default_ceiling_is_six():
    planner = (ROOT / "automation/planned_capacity_fast_dispatch.py").read_text(encoding="utf-8")
    assert '--max-dispatches", type=int, default=6' in planner
