import json
import platform
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

    assert worker.LANES["repo_qa"][0][0:2] == [worker.PYTHON, "-c"]
    assert "ast.parse" in worker.LANES["repo_qa"][0][2]
    assert worker.LANES["repo_qa"][1][0:3] == [worker.PYTHON, "-m", "pytest"]


def test_every_lane_writes_non_formal_run_manifest(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    monkeypatch.setenv("RUNNER_NAME", "self-hosted-test")

    for lane, commands in worker.LANES.items():
        output_dir = tmp_path / lane
        attempted = []

        def fake_run(command, out_dir, index):
            attempted.append(index)
            return {"index": index, "returncode": 0 if index == 1 else 7}

        monkeypatch.setattr(worker, "run", fake_run)
        monkeypatch.setattr(
            "sys.argv",
            [
                "self_hosted_research_worker",
                "--lane",
                lane,
                "--output-dir",
                str(output_dir),
            ],
        )

        expected_codes = [0] if len(commands) == 1 else [0, 7]
        assert worker.main() == (0 if len(commands) == 1 else 7)
        assert attempted == list(range(1, len(expected_codes) + 1))

        manifest = json.loads(
            (output_dir / "run_manifest.json").read_text(encoding="utf-8")
        )
        assert manifest == {
            "schema_version": 1,
            "lane": lane,
            "python_executable": worker.sys.executable,
            "python_version": platform.python_version(),
            "source_commit": "abc123",
            "runner_name": "self-hosted-test",
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "formal_research_evidence": False,
            "step_count": len(expected_codes),
            "step_return_codes": expected_codes,
        }


def test_run_manifest_allows_local_execution_without_github_metadata(monkeypatch, tmp_path):
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.delenv("RUNNER_NAME", raising=False)
    monkeypatch.setattr(worker, "run", lambda command, out_dir, index: {
        "index": index,
        "returncode": 0,
    })
    monkeypatch.setattr(
        "sys.argv",
        [
            "self_hosted_research_worker",
            "--lane",
            "data_qa",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert worker.main() == 0
    manifest = json.loads(
        (tmp_path / "run_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["source_commit"] is None
    assert manifest["runner_name"] is None
    assert manifest["formal_research_evidence"] is False


def test_copilot_cli_publication_has_nonfatal_pr_creation_fallback():
    text = (
        ROOT / ".github" / "workflows" / "copilot-cli-engineering-task.yml"
    ).read_text(encoding="utf-8")
    assert "PR_CREATE_UNAVAILABLE" in text
    assert "Automatic PR creation is unavailable" in text
    assert "tests/safety passed" in text



def test_continuous_qa_preserves_artifacts_and_runs_both_lanes():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-continuous-qa.yml"
    ).read_text(encoding="utf-8")
    assert "set \"FAIL=0\"" in text
    assert 'if errorlevel 1 set "FAIL=1"' in text
    assert "Publish continuous QA provenance" in text
    assert "actions/upload-artifact@v6" in text
    assert "continuous_repo_qa_${{ github.run_id }}" in text
    assert "continuous_data_qa_${{ github.run_id }}" in text

def test_self_hosted_continuous_qa_is_scheduled_and_non_formal():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-continuous-qa.yml"
    ).read_text(encoding="utf-8")
    assert 'cron: "*/30 * * * *"' in text
    assert "workflow_dispatch:" in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "concurrency:" in text
    assert "trading-agent-self-hosted-continuous-qa" in text
    assert "--lane repo_qa" in text
    assert "--lane data_qa" in text
    assert "--lane local_reproduction" in text
    assert "PAPER_ONLY" in text
    assert "LIVE_TRADING_ENABLED" in text
    assert "ORDERS_ENABLED" in text
    assert "AUTOMATIC_PROMOTION" not in text
    assert "research/evidence" not in text


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
