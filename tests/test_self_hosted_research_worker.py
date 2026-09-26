from pathlib import Path

from automation import self_hosted_research_worker as worker


ROOT = Path(__file__).parents[1]


def test_self_hosted_worker_has_only_bounded_lanes():
    assert set(worker.LANES) == {"repo_qa", "data_qa", "local_reproduction"}
    for commands in worker.LANES.values():
        assert commands
        for command in commands:
            assert command
            assert command[0] == worker.PYTHON
            assert "live" not in " ".join(command).lower()
            assert "promotion" not in " ".join(command).lower()


def test_self_hosted_worker_v3_uses_proven_master_push_shape():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-research-worker-v3.yml"
    ).read_text(encoding="utf-8")
    assert "name: Self-hosted Research Worker v3" in text
    assert "on:" in text
    assert "branches:" in text
    assert "- master" in text
    assert "workflow_dispatch:" not in text
    assert "research/run_requests/self_hosted_repo_qa.trigger" in text
    assert "RUN_SELF_HOSTED_REPO_QA:" in text
    assert "github.actor == github.repository_owner" not in text
    assert "GITHUB_ACTOR" in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "Registration probe" in text
    assert "actions/checkout@v5" in text
    assert "ref: ${{ github.sha }}" in text
    assert "shell: cmd" in text
    assert "shell: powershell" not in text
    assert "python.3.13.15.nupkg" in text
    assert "v3-flatcontainer/python/3.13.15" in text
    assert "python-3.13.15-nuget" in text
    assert "python.exe" in text
    assert "--lane repo_qa" in text
    assert "PAPER_ONLY" in text
    assert "LIVE_TRADING_ENABLED" in text
    assert "ORDERS_ENABLED" in text
