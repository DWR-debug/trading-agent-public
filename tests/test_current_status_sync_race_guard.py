from pathlib import Path


def test_status_sync_uses_atomic_publisher_and_avoids_master_push_races():
    text = Path(".github/workflows/current-status-sync.yml").read_text(encoding="utf-8")
    assert "python -m automation.github_contents_publish" in text
    assert '--file "docs/CURRENT_STATUS.md=docs/CURRENT_STATUS.md"' in text
    assert '--file "research/evidence/current_operational_state.json=research/evidence/current_operational_state.json"' in text
    assert "PUBLISH_MESSAGE='OPS: synchronize current operational status'" in text
    assert "gh api --method PUT" not in text
    assert "git push origin HEAD:master" not in text
    assert "STATUS_SYNC_ABORT_STALE_SOURCE" in text
    assert "cancel-in-progress: true" in text
    assert "paths-ignore:" in text
    assert "- docs/CURRENT_STATUS.md" in text
    assert "- research/evidence/current_operational_state.json" in text
