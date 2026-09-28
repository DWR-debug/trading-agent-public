from pathlib import Path


def test_status_sync_fails_closed_on_master_drift_before_generation_and_commit():
    text = Path(".github/workflows/current-status-sync.yml").read_text(encoding="utf-8")
    assert text.count("git ls-remote origin refs/heads/master") == 2
    assert "STATUS_SYNC_MASTER_MOVED_BEFORE_GENERATION" in text
    assert "STATUS_SYNC_REMOTE_MOVED_BEFORE_PUSH" in text
    assert "git pull --rebase origin master" not in text
    assert "git push origin HEAD:master" in text
