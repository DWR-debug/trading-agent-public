from pathlib import Path


def test_local_ai_state_publisher_is_gitless_and_race_tolerant(monkeypatch, tmp_path):
    import automation.publish_ai_worker_state as publisher

    output = tmp_path / "worker.json"
    output.write_text(
        '{"schema_version":1,"task_id":"T","provider":"gemini_cli","status":"SKIPPED"}\n',
        encoding="utf-8",
    )
    state = tmp_path / "ops" / "state.json"

    monkeypatch.setenv("AI_WORKER_STATE_PATH", str(state))
    monkeypatch.setenv("AI_WORKER_OUTPUT_PATH", str(output))
    monkeypatch.setenv("AI_WORKER_TASK_ID", "T")
    monkeypatch.setenv("AI_WORKER_PROVIDER", "gemini_cli")
    monkeypatch.setenv("GITHUB_REPOSITORY", "DWR-debug/trading-agent-public")
    monkeypatch.setenv("GH_TOKEN", "test-token")

    current_shas = iter(("base-1", "base-2"))
    publish_calls = []

    monkeypatch.setattr(
        publisher.github_contents_publish,
        "api",
        lambda method, url: {"object": {"sha": next(current_shas)}},
    )

    def fake_publish(repository, branch, base_sha, files):
        publish_calls.append((repository, branch, base_sha, files))
        if len(publish_calls) == 1:
            raise RuntimeError("ref moved from base-1 to newer")
        return "commit-2"

    monkeypatch.setattr(
        publisher.github_contents_publish,
        "publish",
        fake_publish,
    )
    monkeypatch.setattr(publisher.time, "sleep", lambda _: None)

    assert publisher.main() == 0
    assert state.read_text(encoding="utf-8") == output.read_text(encoding="utf-8")
    assert [call[2] for call in publish_calls] == ["base-1", "base-2"]
    assert publish_calls[1][0:2] == (
        "DWR-debug/trading-agent-public",
        "master",
    )
