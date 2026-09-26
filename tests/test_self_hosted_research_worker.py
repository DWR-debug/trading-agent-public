from pathlib import Path

from automation import self_hosted_research_worker as worker


ROOT = Path(__file__).parents[1]


def test_self_hosted_worker_has_only_bounded_lanes():
    assert set(worker.LANES) == {"repo_qa", "data_qa", "local_reproduction"}
    for commands in worker.LANES.values():
        assert commands

    assert worker.LANES["repo_qa"][0][0:3] == [worker.PYTHON, "-m", "compileall"]
    assert worker.LANES["repo_qa"][1][0:3] == [worker.PYTHON, "-m", "pytest"]
        for command in commands:
            assert command
            assert command[0] == worker.PYTHON
            assert "live" not in " ".join(command).lower()
            assert "promotion" not in " ".join(command).lower()



def test_self_hosted_worker_v4_is_minimal_single_step_gateway():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-research-worker-v4.yml"
    ).read_text(encoding="utf-8")
    assert "name: Self-hosted Research Worker v4" in text
    assert "workflow_dispatch:" not in text
    assert '  push:' in text
    assert "- master" in text
    assert 'research/run_requests/self_hosted_repo_qa.trigger' in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "steps:" in text
    assert "Self-hosted repo_qa single-step worker" in text
    assert "uses:" not in text
    assert "shell: cmd" in text
    assert "shell: powershell" not in text
    assert "codeload.github.com/DWR-debug/trading-agent-public/tar.gz/" in text
    assert "python.3.13.15.nupkg" in text
    assert "v3-flatcontainer/python/3.13.15" in text
    assert "python-3.13.15-nuget" in text
    assert "python.exe" in text
    assert "--lane repo_qa" in text
    assert "PAPER_ONLY" in text
    assert "LIVE_TRADING_ENABLED" in text
    assert "ORDERS_ENABLED" in text
