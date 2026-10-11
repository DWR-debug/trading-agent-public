from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS_WORKFLOW = ROOT / ".github/workflows/q104-i19-13f-historical-identity-census.yml"
RECOVERY_WORKFLOW = ROOT / ".github/workflows/q104-i19-missing-shard-recovery.yml"


def test_q104_does_not_rerun_its_own_workflow_before_terminal_state():
    census = CENSUS_WORKFLOW.read_text(encoding="utf-8")
    # A workflow cannot re-run its own current run while that run is still
    # executing. Terminal recovery is orchestrated by the separate workflow_run
    # consumer below, which receives the source run only after completion.
    assert "gh run rerun \"$GITHUB_RUN_ID\" --failed" not in census
    assert "  retry_failed:" not in census
    assert "  completion_relay:" in census


def test_q104_terminal_recovery_is_triggered_only_from_a_completed_census():
    recovery = RECOVERY_WORKFLOW.read_text(encoding="utf-8")
    trigger = recovery.split("on:", 1)[1].split("permissions:", 1)[0]
    assert 'workflows: ["Q104 I19 Historical 13F Identity Census"]' in trigger
    assert "types: [completed]" in trigger
    assert "branches: [master]" in trigger
    assert '.status == "completed"' in recovery
    assert "targeted_header_repair:" in recovery
    assert "q104-i19-targeted-acceptance-repair.yml" in recovery
    assert "github.event.workflow_run.conclusion != 'success'" in recovery


def test_q104_push_events_require_changed_explicit_recovery_trigger():
    census = CENSUS_WORKFLOW.read_text(encoding="utf-8")

    assert "Q104_CENSUS_PUSH_SUPPRESSED=RECOVERY_TRIGGER_UNCHANGED" in census
    assert 'git diff --name-only "$before_sha" "$GITHUB_SHA" -- "$trigger_path"' in census
    assert "research/run_requests/q104_i19_census_recovery.trigger" in census
    assert 'RUN_Q104_I19_CENSUS_RECOVERY=true' in census
    for flag in (
        "SOURCE_RECEIPT_REUSE=false",
        "PERFORMANCE=false",
        "HOLDOUT_SELECTION=false",
        "RANKING=false",
        "TUNING=false",
        "PROMOTION=false",
        "LIVE_EXECUTION=false",
    ):
        assert flag in census
    assert "fetch-depth: 2" in census


