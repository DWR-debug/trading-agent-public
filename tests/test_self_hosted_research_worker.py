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


def test_self_hosted_dispatch_uses_registered_orchestrator_gateway():
    text = (
        ROOT / ".github" / "workflows" / "research-orchestrator.yml"
    ).read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "- self_hosted_worker" in text
    assert "self_hosted_lane:" in text
    assert "self_hosted_ref:" in text
    assert "github.event_name == 'workflow_dispatch'" in text
    assert "inputs.mode == 'self_hosted_worker'" in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "PAPER_ONLY" in text
    assert "ORDERS_ENABLED" in text
    assert "shell: cmd" in text
    assert "shell: powershell" not in text
    assert "python.3.13.15.nupkg" in text
    assert "v3-flatcontainer/python/3.13.15" in text
    assert "python-3.13.15-nuget" in text
    assert "python.exe" in text

def test_ci_has_dedicated_self_hosted_gateway():
    text = (
        ROOT / ".github" / "workflows" / "ci.yml"
    ).read_text(encoding="utf-8")
    assert "research/run-self-hosted/repo_qa" in text
    assert "research/run-self-hosted/data_qa" in text
    assert "research/run-self-hosted/local_reproduction" in text
    assert "self_hosted_worker:" in text
    assert "needs: test" in text
    assert "github.event_name == 'push'" in text
    assert "github.actor == github.repository_owner" in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "ref: ${{ github.sha }}" in text
    assert "PAPER_ONLY" in text
    assert "LIVE_TRADING_ENABLED" in text
    assert "ORDERS_ENABLED" in text
    assert "shell: cmd" in text
    assert "shell: powershell" not in text
    assert "python.3.13.15.nupkg" in text
    assert "v3-flatcontainer/python/3.13.15" in text
    assert "python-3.13.15-nuget" in text
    assert "python.exe" in text
