from pathlib import Path
from automation import top4_candidate_capacity as worker

ROOT = Path(__file__).parents[1]

def test_top4_capacity_has_exact_four_candidates_and_no_authority():
    assert list(worker.LANES) == ["Q104:I19", "Q218", "Q220", "Q221"]
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
    assert "q104_xbrl_concept_freeze_audit.py" in q220
    assert "q220_fsn_schema_gate" in q220
    assert "q221_usaspending_public_clock_gate" in q221
    assert "q104_i19_xbrl_pit_compiler.py" in q220
    assert "top_candidate_source_preflight" in q221

def test_top4_workflow_uses_three_windows_and_hosted_x64_arm64():
    text=(ROOT/".github/workflows/top4-candidate-research-capacity.yml").read_text(encoding="utf-8")
    assert "max-parallel: 3" in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "runs-on: ubuntu-24.04" in text
    assert "runs-on: ubuntu-24.04-arm" in text
    assert "candidate: [Q104:I19,Q218,Q220,Q221]" in text
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
