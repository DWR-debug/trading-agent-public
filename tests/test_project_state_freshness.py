import json
import subprocess
from types import SimpleNamespace

import pytest

from automation.project_state_freshness_check import (
    _verified_master_revision,
    freshness_errors,
)


def test_consistent_state_and_checkpoint_are_green():
    revision = "a" * 40
    state = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit": revision,
        "engineering_notes": {
            "q016_execution_status": "COMPLETED",
            "q016_scientific_status": "DATA_INSUFFICIENT",
        },
    }
    checkpoint = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit_at_checkpoint_creation": revision,
        "generated_at_utc": "2026-09-25T18:25:10Z",
        "q016": {
            "workflow_conclusion": "success",
            "aggregate_status": "DATA_INSUFFICIENT",
            "workflow_run_id": 36172112861,
            "result_fingerprint": "fingerprint",
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }

    assert freshness_errors(
        state,
        checkpoint,
        verified_master_revision=revision,
        verified_master_source="test master ref",
    ) == []


def test_stale_running_q016_is_rejected():
    state = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit": "abc",
        "engineering_notes": {
            "q016_execution_status": "RUNNING",
            "q016_scientific_status": "NO_RESULT_YET",
        },
    }
    checkpoint = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit_at_checkpoint_creation": "abc",
        "generated_at_utc": "2026-09-25T18:25:10Z",
        "q016": {
            "workflow_conclusion": "success",
            "aggregate_status": "DATA_INSUFFICIENT",
            "workflow_run_id": 36172112861,
            "result_fingerprint": "fingerprint",
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }

    errors = freshness_errors(state, checkpoint)

    assert any("execution status is stale" in error for error in errors)
    assert any("scientific status is stale" in error for error in errors)
    assert any("36172112861" in error for error in errors)
    assert any("fingerprint" in error for error in errors)


def test_provenance_drift_is_rejected():
    state = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit": "b" * 40,
        "engineering_notes": {},
    }
    checkpoint = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit_at_checkpoint_creation": "c" * 40,
        "generated_at_utc": "2026-09-25T18:25:10Z",
        "q016": {},
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }

    errors = freshness_errors(state, checkpoint)

    assert any("master provenance drift" in error for error in errors)


def test_checkpoint_behind_verified_master_reports_revision_and_source():
    stale_revision = "d" * 40
    verified_revision = "e" * 40
    state = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit": stale_revision,
        "engineering_notes": {},
    }
    checkpoint = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit_at_checkpoint_creation": stale_revision,
        "generated_at_utc": "2026-09-25T18:25:10Z",
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }

    errors = freshness_errors(
        state,
        checkpoint,
        verified_master_revision=verified_revision,
        verified_master_source="pull_request.base.sha",
    )

    assert len(errors) == 1
    assert "checkpoint repository revision is stale" in errors[0]
    assert "pull_request.base.sha" in errors[0]
    assert "current_project_checkpoint.json" in errors[0]
    assert stale_revision in errors[0]
    assert verified_revision in errors[0]


def test_stale_q020_checkpoint_workflow_provenance_is_reported():
    revision = "f" * 40
    state = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit": revision,
        "q020_performance": {
            "status": "NO_PROMOTION_EVIDENCE",
            "workflow_run_id": 101,
            "artifact_id": 201,
            "result_fingerprint": "old-fingerprint",
        },
    }
    checkpoint = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit_at_checkpoint_creation": revision,
        "generated_at_utc": "2026-09-25T18:25:10Z",
        "q020_performance": {
            "status": "NO_PROMOTION_EVIDENCE",
            "workflow_run_id": 102,
            "artifact_id": 202,
            "result_fingerprint": "new-fingerprint",
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }

    errors = freshness_errors(state, checkpoint)

    assert any("workflow_run_id is stale" in error and "102" in error for error in errors)
    assert any("artifact_id is stale" in error and "202" in error for error in errors)
    assert any(
        "result_fingerprint is stale" in error and "new-fingerprint" in error
        for error in errors
    )


def test_pull_request_revision_comes_from_base_sha(tmp_path, monkeypatch):
    revision = "a" * 40
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps({"pull_request": {"base": {"sha": revision}}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.delenv("GITHUB_REF", raising=False)
    monkeypatch.delenv("GITHUB_SHA", raising=False)

    assert _verified_master_revision() == (revision, "pull_request.base.sha")


def test_master_push_revision_comes_from_github_sha(monkeypatch):
    revision = "b" * 40
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/master")
    monkeypatch.setenv("GITHUB_SHA", revision)

    assert _verified_master_revision() == (revision, "GITHUB_SHA (master push)")


def test_master_revision_uses_remote_ref_when_local_master_is_unavailable(monkeypatch):
    revision = "c" * 40
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/research/qa")
    monkeypatch.delenv("GITHUB_SHA", raising=False)

    def run(command, **_kwargs):
        if command[1] == "rev-parse":
            raise subprocess.CalledProcessError(128, command)
        return SimpleNamespace(stdout=f"{revision}\trefs/heads/master\n")

    monkeypatch.setattr(
        "automation.project_state_freshness_check.subprocess.run",
        run,
    )

    assert _verified_master_revision() == (revision, "origin/refs/heads/master")


def test_malformed_pull_request_event_fails_closed(tmp_path, monkeypatch):
    event_path = tmp_path / "event.json"
    event_path.write_text("[]", encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))

    with pytest.raises(SystemExit, match="not a JSON object"):
        _verified_master_revision()
