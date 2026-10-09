from pathlib import Path


def test_q218_replication_bundle_verification_uses_local_frozen_receipts():
    workflow = Path(".github/workflows/q218-independent-replication-once.yml").read_text(encoding="utf-8")
    start = workflow.index("- name: Verify downloaded replication bundle")
    end = workflow.index("- name: Require explicit authorization for exact replication trial")
    verify_step = workflow[start:end]

    assert 'REP_ROOT: research/runs/q218_independent_replication/${{ github.run_id }}' in verify_step
    assert 'root/"input_bundle_manifest.json"' in verify_step
    assert 'root/"input_bundle_receipt.json"' in verify_step
    assert 'EXPECTED_ARTIFACT_ID: ${{ steps.bundle.outputs.artifact_id }}' in verify_step
    assert 'research/evidence/q218_independent_replication_input_bundle_latest.json' not in verify_step


def test_q218_missing_performance_result_does_not_create_secondary_artifact_failure():
    workflow = Path(".github/workflows/q218-independent-replication-once.yml").read_text(encoding="utf-8")
    anchor = "- name: Upload immutable replication result\n        if: always() && hashFiles('replication_bundle/q218_independent_replication_performance_result.json') != ''"
    assert anchor in workflow

def test_q218_replication_can_dispatch_dashboard_and_capacity_refresh():
    workflow = Path(".github/workflows/q218-independent-replication-once.yml").read_text(encoding="utf-8")
    assert "permissions:\n  contents: write\n  actions: write" in workflow
    assert 'gh workflow run resource-dashboard-update.yml --repo "$GITHUB_REPOSITORY" --ref master' in workflow
    assert 'gh workflow run planned-capacity-fast-dispatch.yml --repo "$GITHUB_REPOSITORY" --ref master' in workflow
