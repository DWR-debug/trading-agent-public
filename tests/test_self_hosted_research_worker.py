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


def test_self_hosted_workflow_is_manual_and_owner_gated():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-research-worker.yml"
    ).read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "github.actor == github.repository_owner" in text
    assert "pull_request:" not in text
    assert "PAPER_ONLY" in text
    assert "ORDERS_ENABLED" in text
    assert "shell: cmd" in text
    assert "shell: powershell" not in text
