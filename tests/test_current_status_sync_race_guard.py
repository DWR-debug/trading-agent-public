from pathlib import Path


def test_status_sync_uses_file_level_updates_and_avoids_master_push_races():
    text = Path(".github/workflows/current-status-sync.yml").read_text(encoding="utf-8")
    assert "gh api --method PUT" in text
    assert "/contents/${path}" in text
    assert "git push origin HEAD:master" not in text
    assert "STATUS_SYNC_FILE_RACE" in text
    assert "CURRENT_STATUS_SYNC_PUBLISH_OK" in text
    assert "cancel-in-progress: true" in text
