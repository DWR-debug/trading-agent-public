from pathlib import Path


def test_status_sync_uses_atomic_publisher_and_avoids_master_push_races():
    text = Path(".github/workflows/current-status-sync.yml").read_text(encoding="utf-8")
    assert "python -m automation.github_contents_publish" in text
    assert '--file "docs/CURRENT_STATUS.md=docs/CURRENT_STATUS.md"' in text
    assert '--file "research/evidence/current_operational_state.json=research/evidence/current_operational_state.json"' in text
    assert "PUBLISH_MESSAGE='OPS: synchronize current operational status'" in text
    assert "gh api --method PUT" not in text
    assert "git push origin HEAD:master" not in text

    # A concurrent master push must cause a bounded regeneration, not a stale
    # status publish or a one-time abort that leaves the canonical snapshot stale.
    assert "for attempt in 1 2 3 4 5; do" in text
    assert "STATUS_SYNC_RETRY_STALE_GENERATION" in text
    assert "STATUS_SYNC_RETRY_PUBLISH_RACE" in text
    assert "Master kept moving; status sync exhausted five bounded regeneration attempts." in text
    assert "STATUS_SYNC_ABORT_STALE_SOURCE" not in text

    assert "cancel-in-progress: true" in text
    assert "paths-ignore:" in text
    assert "- docs/CURRENT_STATUS.md" in text
    assert "- research/evidence/current_operational_state.json" in text
