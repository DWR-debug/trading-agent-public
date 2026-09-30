import json
import platform
from pathlib import Path

from automation import self_hosted_research_worker as worker


ROOT = Path(__file__).parents[1]


def test_self_hosted_worker_has_only_bounded_lanes():
    assert set(worker.LANES) == {"repo_qa", "data_qa", "design_qa", "local_reproduction", "autonomous_frontier_qa"}
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

        summary = json.loads(
            (output_dir / "summary.json").read_text(encoding="utf-8")
        )
        assert summary["lane"] == lane
        assert summary["formal_evidence_allowed"] is False
        assert [result["index"] for result in summary["results"]] == list(
            range(1, len(expected_codes) + 1)
        )
        assert [result["returncode"] for result in summary["results"]] == expected_codes


def test_each_lane_fails_closed_and_preserves_failure_provenance(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    monkeypatch.setenv("RUNNER_NAME", "self-hosted-test")

    for lane in worker.LANES:
        output_dir = tmp_path / lane
        attempted = []

        def fail_first_step(command, out_dir, index):
            attempted.append(index)
            return {"index": index, "returncode": 17}

        monkeypatch.setattr(worker, "run", fail_first_step)
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

        assert worker.main() == 17
        assert attempted == [1]

        summary = json.loads(
            (output_dir / "summary.json").read_text(encoding="utf-8")
        )
        manifest = json.loads(
            (output_dir / "run_manifest.json").read_text(encoding="utf-8")
        )
        assert summary["lane"] == lane
        assert summary["results"][0]["returncode"] == 17
        assert summary["formal_evidence_allowed"] is False
        assert manifest["lane"] == lane
        assert manifest["source_commit"] == "abc123"
        assert manifest["step_return_codes"] == [17]


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



def test_continuous_qa_is_matrix_orchestrated_and_parallel_bounded():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-continuous-qa.yml"
    ).read_text(encoding="utf-8")
    assert "qa_lane:" in text
    assert "name: QA lane (${{ matrix.lane }})" in text
    assert "fail-fast: false" in text
    assert "max-parallel: 2" in text
    assert "cancel-in-progress: true" in text
    assert "lane: [repo_qa, data_qa, design_qa, local_reproduction, autonomous_frontier_qa]" in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "Aggregate QA gate" in text
    assert "needs: qa_lane" in text
    assert "if: always()" in text
    assert "MATRIX_RESULT: ${{ needs.qa_lane.result }}" in text
    assert 'if /I not "%MATRIX_RESULT%"=="success" exit /b 1' in text


def test_self_hosted_continuous_qa_is_scheduled_and_non_formal():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-continuous-qa.yml"
    ).read_text(encoding="utf-8")
    assert 'cron: "15 * * * *"' in text
    assert "workflow_dispatch:" in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "concurrency:" in text
    assert "trading-agent-self-hosted-continuous-qa" in text
    assert "PAPER_ONLY" in text
    assert "LIVE_TRADING_ENABLED" in text
    assert "ORDERS_ENABLED" in text
    assert "AUTOMATIC_PROMOTION" in text
    assert "formal_research_evidence" in text
    assert "research/evidence" not in text
    assert "pull_request:" not in text
    assert "codeload.github.com/DWR-debug/trading-agent-public/tar.gz/%GITHUB_SHA%" in text
    assert "python/3.13.15/python.3.13.15.nupkg" in text
    assert "if-no-files-found: error" in text
    assert "continuous_${{ matrix.lane }}" in text
    assert "runner_capacity_${{ matrix.lane }}" in text
    assert "self-hosted-continuous-qa-${{ matrix.lane }}-${{ github.run_id }}-${{ github.run_attempt }}" in text


def test_self_hosted_continuous_qa_is_run_isolated():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-continuous-qa.yml"
    ).read_text(encoding="utf-8")
    assert 'set "RUN_KEY=%GITHUB_RUN_ID%-%GITHUB_RUN_ATTEMPT%"' in text
    assert r'set "WORK=%RUNNER_TEMP%\trading-agent-continuous-%RUN_KEY%-%LANE%"' in text
    assert r'set "ARCHIVE=%RUNNER_TEMP%\trading-agent-continuous-%RUN_KEY%-' in text
    assert r'set "PY_ROOT=%RUNNER_TEMP%\python-3.13.15-nuget-%RUN_KEY%-' in text
    assert r'set "PY_PKG=%RUNNER_TEMP%\python.3.13.15-%RUN_KEY%-' in text
    assert r'set "SITE=%RUNNER_TEMP%\python-site-continuous-%RUN_KEY%-' in text


def test_continuous_qa_publishes_required_provenance_artifacts():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-continuous-qa.yml"
    ).read_text(encoding="utf-8")
    assert "if: always()" in text
    assert "if-no-files-found: error" in text
    assert "summary.json" in text
    assert "run_manifest.json" in text
    assert "RUNNER_CAPACITY_AND_PROVENANCE_OK" in text
    assert "exit /b 1" in text


def test_self_hosted_worker_v4_is_minimal_single_step_gateway():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-research-worker-v4.yml"
    ).read_text(encoding="utf-8")
    assert "name: Research Worker v4 (trusted self-hosted Windows)" in text
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


def test_q022_design_guard_is_bounded_and_non_executing():
    from automation import q022_design_guard

    payload = json.loads(
        (ROOT / "research" / "preregistrations" / "q022_treasury_failure_followup_design_2026_09_26.json").read_text(encoding="utf-8")
    )
    queue = json.loads((ROOT / "research" / "research_queue.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "research" / "evidence" / "trial_ledger.json").read_text(encoding="utf-8"))
    fingerprint = q022_design_guard.validate_q022_design(payload, queue, ledger)
    assert len(fingerprint) == 64
    assert payload["ranked"] is False
    assert payload["performance_trial_authorized"] is False
    assert payload["holdout_used_for_selection"] is False


def test_local_reproduction_targets_existing_governance_test():
    commands = worker.LANES["local_reproduction"]
    assert commands[1][0:4] == [worker.PYTHON, "-m", "pytest", "-q"]
    assert commands[1][4] == "tests/test_research_gates.py"
    assert (ROOT / commands[1][4]).is_file()

def test_continuous_qa_provenance_is_published_from_workspace():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-continuous-qa.yml"
    ).read_text(encoding="utf-8")
    assert r'set "PROV_ROOT=%GITHUB_WORKSPACE%\research\runs\self_hosted"' in text
    assert r'set "OUT=%PROV_ROOT%\continuous_%LANE%_%RUN_KEY%"' in text
    assert '${{ github.run_attempt }}' in text

def test_continuous_qa_fails_closed_on_missing_provenance_files():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-continuous-qa.yml"
    ).read_text(encoding="utf-8")
    assert "[7/8] Validate lane provenance" in text
    assert "[8/8] Lane result" in text
    assert "RUNNER_CAPACITY_AND_PROVENANCE_OK" in text
    assert "runner_capacity_%LANE%_%RUN_KEY%.json" in text
    assert "utf-8-sig" in text
    assert "c['lane']==r'%LANE%'" in text
    assert "c['source_commit']==r'%GITHUB_SHA%'" in text
    assert "logical_processors" in text
    assert "physical_memory_bytes" in text
    assert "RUNNER_ARCH" in text
    assert "if-no-files-found: error" in text


def test_self_hosted_runner_probe_targets_trusted_label_and_master_only():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-runner-probe.yml"
    ).read_text(encoding="utf-8")
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert "branches: [master]" in text
    assert "RUNNER_PROBE=SUCCESS" in text
    assert "pull_request:" not in text
