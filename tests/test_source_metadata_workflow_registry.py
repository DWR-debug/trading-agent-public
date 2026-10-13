from automation.project_integrity_check import ACTIVE_WORKFLOWS


def test_q127_q130_r2_source_only_workflows_are_registered():
    assert "q127r2-finra-wayback-metadata.yml" in ACTIVE_WORKFLOWS
    assert "q130r2-wikimedia-wayback-metadata.yml" in ACTIVE_WORKFLOWS
