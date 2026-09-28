import base64
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

    def fake_api(method, url):
        if "/git/ref/heads/master" in url:
            return {"object": {"sha": next(current_shas)}}
        raise RuntimeError("GitHub API GET contents failed: 404: not found")

    monkeypatch.setattr(publisher.github_contents_publish, "api", fake_api)

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


def test_local_ai_state_publisher_is_idempotent(monkeypatch, tmp_path):
    import automation.publish_ai_worker_state as publisher

    output = tmp_path / "worker.json"
    payload = '{"schema_version":1,"task_id":"T","provider":"gemini_cli","status":"SKIPPED"}\n'
    output.write_text(payload, encoding="utf-8")
    state = tmp_path / "ops" / "state.json"

    for key, value in {
        "AI_WORKER_STATE_PATH": str(state),
        "AI_WORKER_OUTPUT_PATH": str(output),
        "AI_WORKER_TASK_ID": "T",
        "AI_WORKER_PROVIDER": "gemini_cli",
        "GITHUB_REPOSITORY": "DWR-debug/trading-agent-public",
        "GH_TOKEN": "test-token",
    }.items():
        monkeypatch.setenv(key, value)

    def fake_api(method, url):
        if "/git/ref/heads/master" in url:
            return {"object": {"sha": "base-1"}}
        return {"content": base64.b64encode(payload.encode("utf-8")).decode("ascii")}

    publish_calls = []
    monkeypatch.setattr(publisher.github_contents_publish, "api", fake_api)
    monkeypatch.setattr(publisher.github_contents_publish, "publish", lambda *args, **kwargs: publish_calls.append(args))

    assert publisher.main() == 0
    assert publish_calls == []
