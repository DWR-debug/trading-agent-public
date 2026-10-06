from pathlib import Path
from automation import top4_candidate_capacity as worker

ROOT = Path(__file__).parents[1]

def test_top4_capacity_has_formal_lane_plus_four_frontier_candidates_and_no_authority():
    assert list(worker.LANES) == ["Q104:I19", "Q218", "Q219", "Q220", "Q221"]
    for candidate, commands in worker.LANES.items():
        assert commands
        flattened=" ".join(" ".join(str(x) for x in cmd) for cmd in commands)
        assert "performance_authorization" not in flattened
        assert "holdout_selection" not in flattened
        assert "ranking" not in flattened
        assert "tuning" not in flattened
        assert "live_execution" not in flattened

def test_top4_workpacks_are_mechanistically_separate():
    q104=" ".join(" ".join(map(str,c)) for c in worker.LANES["Q104:I19"])
    q218=" ".join(" ".join(map(str,c)) for c in worker.LANES["Q218"])
    q219=" ".join(" ".join(map(str,c)) for c in worker.LANES["Q219"])
    q220=" ".join(" ".join(map(str,c)) for c in worker.LANES["Q220"])
    q221=" ".join(" ".join(map(str,c)) for c in worker.LANES["Q221"])
    assert "q104_i19_xbrl_pit_compiler" in q104
    assert "q104_i19_13f_historical_identity_census" in q104
    assert "q104_i19_xbrl_concept_freeze" in q104
    assert "q218_sec_multichannel_source_gate" in q218
    assert "q219_options_source_breadth_gate" in q219
    assert "test_q219_options_source_breadth_gate.py" in q219
    assert "q104_xbrl_concept_freeze_audit.py" in q220
    assert "q220_as_filed_xbrl_population_gate" in q220
    assert "q220_fsn_schema_gate" not in q220
    assert "q221_usaspending_public_clock_gate" in q221
    assert "q104_i19_xbrl_pit_compiler.py" in q220
    assert "top_candidate_source_preflight" in q221

def test_top4_workflow_uses_three_windows_and_hosted_x64_arm64():
    text=(ROOT/".github/workflows/top4-candidate-research-capacity.yml").read_text(encoding="utf-8")
    assert "max-parallel: 3" in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "runs-on: ubuntu-24.04" in text
    assert "runs-on: ubuntu-24.04-arm" in text
    assert "candidate: [Q218,Q219,Q220]" in text
    assert "candidate: [Q104:I19" not in text
    assert 'cron: "*/15 * * * *"' in text

def test_legacy_research_loops_are_manual_only():
    for path in (
        ".github/workflows/permanent-pc-research-loop.yml",
        ".github/workflows/hosted-deterministic-frontier.yml",
        ".github/workflows/windows-runner-c-long-research.yml",
    ):
        text=(ROOT/path).read_text(encoding="utf-8")
        assert "workflow_dispatch:" in text
        assert "\n  schedule:" not in text
        assert "\n  push:" not in text


def test_top4_balances_hosted_capacity_slots():
    text=(ROOT/".github/workflows/top4-candidate-research-capacity.yml").read_text(encoding="utf-8")
    assert 'candidate: [Q218,Q220,Q221]' in text
    assert text.count('candidate: [Q221]') == 1
    assert text.count('candidate: [Q220]') == 1
    hosted = text.split("  hosted_x64:", 1)[1]
    assert "Q219" not in hosted
    assert "trading-agent-research-hosted-ubuntu-24.04" in hosted
    assert "trading-agent-research-hosted-ubuntu-24.04-arm" in hosted



def test_top4_has_no_global_wave_lock():
    text=(ROOT/".github/workflows/top4-candidate-research-capacity.yml").read_text(encoding="utf-8")
    assert "\nconcurrency:\n  group: trading-agent-top4-capacity" not in text
    assert "trading-agent-research-hosted-ubuntu-24.04" in text
    assert "trading-agent-research-hosted-ubuntu-24.04-arm" in text


def test_hosted_slots_are_explicitly_leased():
    text=(ROOT/".github/workflows/top4-candidate-research-capacity.yml").read_text(encoding="utf-8")
    q104=(ROOT/".github/workflows/q104-i19-13f-historical-identity-census.yml").read_text(encoding="utf-8")
    assert "trading-agent-research-hosted-ubuntu-24.04-slot-2" in text
    assert "trading-agent-research-hosted-ubuntu-24.04-arm-slot-2" in text
    assert "trading-agent-research-hosted-${{ matrix.runner }}-slot-${{ matrix.slot }}" in q104
    assert 'slot: "1"' in q104


def test_top4_workflow_triggers_on_q219_gate_changes():
    workflow = (ROOT / ".github/workflows/top4-candidate-research-capacity.yml").read_text(encoding="utf-8")
    assert '"automation/q219_options_source_breadth_gate.py"' in workflow
    assert '"tests/test_q219_options_source_breadth_gate.py"' in workflow
