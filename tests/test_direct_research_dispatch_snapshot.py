from __future__ import annotations

import json
import subprocess

import pytest

from automation import build_direct_dispatch_snapshot as direct
from automation import generate_resource_dashboard as dashboard


WINDOWS_POLICY = "ASSUMED_ALWAYS_AVAILABLE_BY_OPERATOR"
SAFETY = {
    "PAPER_ONLY": True,
    "LIVE_TRADING_ENABLED": False,
    "ORDERS_ENABLED": False,
    "AUTOMATIC_PROMOTION": False,
}


def _os_state():
    return {
        "permanent_safety": dict(SAFETY),
        "self_hosted_windows_availability": WINDOWS_POLICY,
    }


def _active_job(run_id=101, runner="LHT-N133732-2", status="in_progress", labels=None):
    return {
        "id": 501,
        "run_id": run_id,
        "name": "bounded Q220 gate",
        "status": status,
        "runner_name": runner,
        "labels": labels or ["self-hosted", "windows", "x64", "trading-agent-research"],
        "workflow_name": "Top-4 Candidate Slot Research",
        "workflow_path": ".github/workflows/top4-candidate-slot-research.yml",
        "run_url": f"https://github.com/DWR-debug/trading-agent-public/actions/runs/{run_id}",
        "event": "schedule",
    }


def test_work_from_active_jobs_counts_only_jobs_actually_in_progress():
    runs = [
        {
            "id": 101,
            "name": "Top-4 Candidate Slot Research",
            "status": "in_progress",
            "event": "schedule",
            "html_url": "https://github.com/DWR-debug/trading-agent-public/actions/runs/101",
        },
        {
            "id": 102,
            "name": "Top-4 Candidate Slot Research",
            "status": "queued",
            "event": "schedule",
        },
    ]
    jobs = [
        _active_job(run_id=101, runner="LHT-N133732-2", status="in_progress"),
        _active_job(run_id=101, runner="LHT-N133732-3", status="queued"),
        _active_job(run_id=102, runner="LHT-N133732", status="waiting"),
    ]

    work = direct.work_from_active_jobs(runs, jobs)

    assert len(work) == 1
    assert work[0]["resource"] == "Windows self-hosted B"
    assert work[0]["runner_name"] == "LHT-N133732-2"
    assert work[0]["status"] == "in_progress"
    assert work[0]["job_status"] == "in_progress"


def test_all_three_windows_slots_are_routable_when_no_actual_job_is_running():
    resources = dashboard.enrich_resources(direct.configured_resources(_os_state()), [], [])
    windows = {row["name"]: row for row in resources if row["name"].startswith("Windows self-hosted ")}

    assert set(windows) == {
        "Windows self-hosted A",
        "Windows self-hosted B",
        "Windows self-hosted C",
    }
    for row in windows.values():
        assert row["capacity_state"] == "assumed_available"
        assert row["research_slots_free"] == 1
        assert row["runner_busy"] is None
        assert row["live_status"] == "assumed available (operator policy; not live-verified)"


def test_one_running_windows_job_occupies_only_its_exact_runner_slot():
    runs = [{
        "id": 101,
        "name": "Top-4 Candidate Slot Research",
        "status": "in_progress",
        "event": "schedule",
        "html_url": "https://github.com/DWR-debug/trading-agent-public/actions/runs/101",
    }]
    work = direct.work_from_active_jobs(runs, [_active_job(runner="LHT-N133732-2")])
    resources = dashboard.enrich_resources(direct.configured_resources(_os_state()), [], work)
    windows = {row["name"]: row for row in resources if row["name"].startswith("Windows self-hosted ")}

    assert windows["Windows self-hosted A"]["capacity_state"] == "assumed_available"
    assert windows["Windows self-hosted A"]["research_slots_free"] == 1
    assert windows["Windows self-hosted B"]["capacity_state"] == "operating"
    assert windows["Windows self-hosted B"]["research_slots_free"] == 0
    assert windows["Windows self-hosted B"]["runner_busy"] is True
    assert windows["Windows self-hosted C"]["capacity_state"] == "assumed_available"
    assert windows["Windows self-hosted C"]["research_slots_free"] == 1


def test_direct_snapshot_uses_canonical_state_and_not_dashboard_file(monkeypatch):
    monkeypatch.setattr(dashboard, "research_board", lambda evidence, os_state: [])
    monkeypatch.setattr(dashboard, "expanded_candidate_board", lambda evidence, os_state, base: [
        {"code": "Q104:I19", "lane": "FORMAL READINESS", "next_gate": "bounded source lineage"},
        {"code": "Q220", "lane": "FRONTIER DISCOVERY", "next_gate": "fixed-key source header verification"},
        {"code": "Q221", "lane": "FRONTIER DISCOVERY", "next_gate": "transaction-level public clock"},
    ])
    monkeypatch.setattr(dashboard, "planned_capacity_plan", lambda resources, work, top4, benchmarks, os_state, recent_runs=None: [])
    snapshot = direct.compile_direct_snapshot(
        runs=[],
        active_jobs=[],
        evidence={"active_research_registry": []},
        os_state=_os_state(),
        master_sha="fixed-test-master",
    )

    assert snapshot["status"] == "DIRECT_SNAPSHOT_READY"
    assert snapshot["master_sha"] == "fixed-test-master"
    assert snapshot["dashboard_is_display_only"] is True
    assert snapshot["dashboard_artifact_used_as_input"] is False
    assert snapshot["focus_candidates"] == ["Q104:I19", "Q220", "Q221"]
    assert len(snapshot["windows_slot_occupancy"]) == 3
    assert all(not row["occupied"] for row in snapshot["windows_slot_occupancy"].values())
    assert snapshot["safety"]["paper_only"] is True
    assert snapshot["safety"]["live_execution"] is False


def test_direct_snapshot_refuses_changed_paper_only_safety():
    invalid = _os_state()
    invalid["permanent_safety"]["LIVE_TRADING_ENABLED"] = True
    with pytest.raises(RuntimeError, match="PERMANENT_SAFETY_BOUNDARY_MISSING_OR_CHANGED"):
        direct.compile_direct_snapshot([], [], evidence={}, os_state=invalid, master_sha="test")


def test_active_run_jobs_are_queried_directly_from_github_not_dashboard(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        payload = {
            "total_count": 2,
            "jobs": [
                _active_job(run_id=101, runner="LHT-N133732", status="in_progress"),
                _active_job(run_id=101, runner="LHT-N133732-2", status="queued"),
            ],
        }
        return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")

    monkeypatch.setattr(direct.subprocess, "run", fake_run)
    jobs = direct.fetch_active_jobs("DWR-debug/trading-agent-public", [{
        "id": 101,
        "name": "Top-4 Candidate Slot Research",
        "status": "in_progress",
        "html_url": "https://github.com/DWR-debug/trading-agent-public/actions/runs/101",
    }])

    assert len(calls) == 1
    assert "/actions/runs/101/jobs?per_page=100" in calls[0][2]
    assert len(jobs) == 1
    assert jobs[0]["runner_name"] == "LHT-N133732"
    assert jobs[0]["status"] == "in_progress"


def test_unidentified_active_job_on_windows_label_fails_closed(monkeypatch):
    payload = {
        "total_count": 1,
        "jobs": [{
            **_active_job(runner="mystery-windows-runner", status="in_progress"),
            "labels": ["self-hosted", "windows", "trading-agent-research"],
        }],
    }

    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")

    monkeypatch.setattr(direct.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="ACTIVE_WINDOWS_JOB_RUNNER_IDENTITY_UNRESOLVED"):
        direct.fetch_active_jobs("DWR-debug/trading-agent-public", [{
            "id": 101, "name": "Some Windows Workflow", "status": "in_progress",
        }])
