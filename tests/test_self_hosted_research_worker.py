import json
import platform
from pathlib import Path

from automation import self_hosted_research_worker as worker


ROOT = Path(__file__).parents[1]


def test_frontier_workpacks_rotate_and_keep_q100_dependency_safe():
    name1, steps1 = worker.select_workpack("autonomous_frontier_qa", len(worker.LANES["autonomous_frontier_qa"]), 0)
    name2, steps2 = worker.select_workpack("autonomous_frontier_qa", len(worker.LANES["autonomous_frontier_qa"]), 1)
    name3, steps3 = worker.select_workpack("autonomous_frontier_qa", len(worker.LANES["autonomous_frontier_qa"]), 2)
    assert [name1, name2, name3] == ["frontier_pack_1", "frontier_pack_2", "frontier_pack_3"]
    assert set(steps1).isdisjoint(steps2)
    assert set(steps2).isdisjoint(steps3)
    assert set(steps1).isdisjoint(steps3)
    all_frontier_steps = set().union(steps1, steps2, steps3)
    assert all_frontier_steps == set(range(1, len(worker.LANES["autonomous_frontier_qa"]) + 1))
    assert [len(steps1), len(steps2), len(steps3)] == [10, 10, 10]
    groups = worker.execution_groups("autonomous_frontier_qa", len(worker.LANES["autonomous_frontier_qa"]), 0)
    assert groups[0][-1] != 8
    assert 5 in groups[0]
    assert 6 in groups[0]
    assert groups[-1] == [8]
    assert worker.execution_groups("local_reproduction", len(worker.LANES["local_reproduction"])) == [[1, 2, 3]]


def test_frontier_lane_has_bounded_parallelism_and_reproduction_stays_serial():
    assert worker.default_max_workers("autonomous_frontier_qa") == 3
    assert worker.default_max_workers("local_reproduction") == 1
    assert worker.default_max_workers("repo_qa") == 1


def test_worker_rejects_unbounded_concurrency(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "sys.argv",
        [
            "self_hosted_research_worker",
            "--lane",
            "data_qa",
            "--output-dir",
            str(tmp_path),
            "--max-workers",
            "5",
        ],
    )
    try:
        worker.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected argparse failure for unbounded concurrency")


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
    monkeypatch.delenv("GITHUB_RUN_NUMBER", raising=False)
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
                "--max-workers",
                "1",
            ],
        )

        selected = worker.select_workpack(lane, len(commands), 0)[1]
        expected_order = [x for x in selected if x != 8] + ([8] if 8 in selected else [])
        expected_codes = [0] if len(expected_order) == 1 else [0] + [7] * (len(expected_order) - 1)
        assert worker.main() == (0 if len(expected_order) == 1 else 7)
        assert attempted == expected_order

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
            "max_workers": 1,
            "rotation_index": 0,
            "workpack": worker.select_workpack(lane, len(commands), 0)[0],
            "selected_steps": selected,
            "step_count": len(expected_codes),
            "step_return_codes": expected_codes,
            "failed_steps": [] if len(expected_order) == 1 else [x for x in expected_order if x != 1],
            "all_bounded_steps_attempted": len(expected_order) == len(commands),
            "all_selected_bounded_steps_attempted": True,
        }

        summary = json.loads(
            (output_dir / "summary.json").read_text(encoding="utf-8")
        )
        assert summary["lane"] == lane
        assert summary["formal_evidence_allowed"] is False
        assert [result["index"] for result in summary["results"]] == sorted(expected_order)
        assert [result["returncode"] for result in summary["results"]] == expected_codes


def test_each_lane_fails_closed_and_preserves_failure_provenance(
    monkeypatch, tmp_path
):
    monkeypatch.delenv("GITHUB_RUN_NUMBER", raising=False)
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
                "--max-workers",
                "1",
            ],
        )

        assert worker.main() == 17
        selected = worker.select_workpack(lane, len(worker.LANES[lane]), 0)[1]
        expected_order = [x for x in selected if x != 8] + ([8] if 8 in selected else [])
        assert attempted == expected_order

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
        assert manifest["step_return_codes"] == [17] * len(expected_order)
        expected_failed_steps = expected_order
        assert manifest["failed_steps"] == expected_failed_steps
        assert manifest["all_bounded_steps_attempted"] is (len(expected_order) == len(worker.LANES[lane]))
        assert manifest["all_selected_bounded_steps_attempted"] is True
        assert summary["failed_steps"] == expected_failed_steps
        assert summary["all_selected_bounded_steps_attempted"] is True


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



def test_permanent_loop_uses_short_local_capacity_pulse():
    text = (
        ROOT / ".github" / "workflows" / "permanent-pc-research-loop.yml"
    ).read_text(encoding="utf-8")
    assert 'cron: "*/30 * * * *"' in text
    assert 'max-parallel: 1' in text
    assert "lane: [local_reproduction]" in text
    assert "runs-on: [self-hosted, trading-agent-research]" in text
    assert '--rotation-index "%GITHUB_RUN_NUMBER%"' in text


def test_hosted_frontier_loop_owns_deterministic_three_pack_rotation():
    text = (
        ROOT / ".github" / "workflows" / "hosted-deterministic-frontier.yml"
    ).read_text(encoding="utf-8")
    assert 'cron: "*/10 * * * *"' in text
    assert "runs-on: ubuntu-24.04" in text
    assert "--lane autonomous_frontier_qa" in text
    assert '--rotation-index "${GITHUB_RUN_NUMBER}"' in text
    assert "HOSTED_FRONTIER_OK" in text
    assert "retention-days: 30" in text



def test_continuous_qa_is_matrix_orchestrated_and_parallel_bounded():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-continuous-qa.yml"
    ).read_text(encoding="utf-8")
    assert "qa_lane:" in text
    assert "name: QA lane (${{ matrix.lane }})" in text
    assert "fail-fast: false" in text
    assert "max-parallel: 1" in text
    assert "cancel-in-progress: true" in text
    assert "lane: [repo_qa]" in text
    assert "runs-on: windows-latest" in text
    assert "Aggregate QA gate" in text
    assert "needs: qa_lane" in text
    assert "if: always()" in text
    # The aggregate gate must validate the actual lane artifacts rather than
    # trusting the matrix aggregate result alone.
    assert "expected = {" in text
    assert '"repo_qa"' in text
    assert "summaries = sorted(Path(" in text
    assert 'summary.get("failed_steps") != []' in text
    assert "step_return_codes" in text
    assert 'print("AGGREGATE_QA=SUCCESS")' in text


def test_s10_diagnostics_do_not_compete_for_parallel_phone_capacity():
    throughput = (
        ROOT / ".github" / "workflows" / "s10-throughput-probe.yml"
    ).read_text(encoding="utf-8")
    runtime = (
        ROOT / ".github" / "workflows" / "s10-runtime-probe.yml"
    ).read_text(encoding="utf-8")
    assert 'workflow_dispatch: {}' in throughput
    assert 'cron: "30 2 * * *"' not in throughput
    assert 'cron: "45 3 * * *"' not in runtime
    assert "workflow_dispatch:" in runtime
    assert 'max-parallel: 1' in runtime
    assert "slot: [a]" in runtime
    # Runtime diagnostics are manual-only by design.
    assert 'cron: "45 3 * * *"' not in runtime


def test_self_hosted_continuous_qa_is_scheduled_and_non_formal():
    text = (
        ROOT / ".github" / "workflows" / "self-hosted-continuous-qa.yml"
    ).read_text(encoding="utf-8")
    assert 'cron: "15 */6 * * *"' in text
    assert "workflow_dispatch:" in text
    assert "runs-on: windows-latest" in text
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


def test_autonomous_frontier_lane_includes_h06_p2_readiness():
    commands = worker.LANES["autonomous_frontier_qa"]
    flattened = [" ".join(command) for command in commands]
    assert any("automation.h06_p2_readiness" in command for command in flattened)
    assert any("h06_p2_readiness" in command for command in flattened)


def test_autonomous_frontier_lane_includes_rccsm_observational_pit_check():
    commands = worker.LANES["autonomous_frontier_qa"]
    flattened = [" ".join(command) for command in commands]
    assert any("tests/test_rccsm_observational_feasibility.py" in command for command in flattened)
    assert any("automation.rccsm_observational_feasibility" in command for command in flattened)
    assert any("q089_rccsm_observational_feasibility.json" in command for command in flattened)


def test_hosted_frontier_loop_publishes_complete_bounded_outputs():
    text = (
        ROOT / ".github" / "workflows" / "hosted-deterministic-frontier.yml"
    ).read_text(encoding="utf-8")
    assert "if: always()" in text
    assert "HOSTED_FRONTIER_OK" in text
    assert "provenance" in text
    assert "retention-days: 30" in text






def test_permanent_windows_loop_uses_two_bounded_lanes():
    workflow = (ROOT / ".github/workflows/permanent-pc-research-loop.yml").read_text(encoding="utf-8")
    assert "max-parallel: 2" in workflow
    assert "lane: [local_reproduction, data_qa]" in workflow
