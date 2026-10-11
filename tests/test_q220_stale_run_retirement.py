from __future__ import annotations

import json
from pathlib import Path

from automation.q220_stale_run_retirement import retire_stale_runs

ROOT = Path(__file__).resolve().parents[1]
REQUEST_PATH = ROOT / "research/run_requests/q220_stale_run_retirement_2026_10_12.json"


def request():
    return json.loads(REQUEST_PATH.read_text(encoding="utf-8"))


def positive_chain():
    return {
        "independent_positive": True,
        "population_receipt_fingerprint": "158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543",
        "compiler_receipt_fingerprint": "dc0ba88133fec8a362cd2a135e452fb8ea24a45349bedf4398113c37bc0fed61",
        "independent_receipt_fingerprint": "4cdbcac030dced54d52a25235e7fd39426065fe1f5b50b1952314ae9a92d41d4",
    }


def fixture_runs():
    req = request()
    runs = {}
    jobs = {}
    for target in req["targets"]:
        run_id = target["run_id"]
        runs[f"repos/DWR-debug/trading-agent-public/actions/runs/{run_id}"] = {
            "id": run_id,
            "name": target["expected_workflow_name"],
            "head_sha": target["expected_head_sha"],
            "event": target["expected_event"],
            "status": target["allowed_run_statuses"][0],
        }
        jobs[f"repos/DWR-debug/trading-agent-public/actions/runs/{run_id}/jobs?per_page=100"] = {
            "jobs": [
                {"name": name, "status": target["allowed_run_statuses"][0]}
                for name in target["expected_active_job_names"]
            ]
        }
    return req, {**runs, **jobs}


def test_retirement_requests_cancel_for_only_the_two_exact_stale_queue_targets():
    req, responses = fixture_runs()
    cancelled = []
    calls = []
    result = retire_stale_runs(
        req,
        positive_chain(),
        get_json=lambda endpoint: calls.append(endpoint) or responses[endpoint],
        cancel_run=cancelled.append,
    )
    assert result["status"] == "COMPLETE"
    assert cancelled == [38179574127, 38178545899]
    assert all(action["status"] == "CANCEL_REQUESTED" for action in result["actions"])
    assert "workflow_dispatch" not in calls[0]
    assert result["scientific_evidence"] is False
    assert result["performance_authorization"] is False


def test_retirement_fails_closed_if_positive_receipt_chain_is_missing_or_stale():
    req, _ = fixture_runs()
    called = []
    chain = positive_chain()
    chain["independent_positive"] = False
    result = retire_stale_runs(req, chain, get_json=called.append, cancel_run=called.append)
    assert result["status"] == "SKIPPED_RECEIPT_CHAIN_NOT_POSITIVE"
    assert called == []


def test_retirement_fails_closed_if_any_receipt_fingerprint_pin_changes():
    req, _ = fixture_runs()
    chain = positive_chain()
    chain["compiler_receipt_fingerprint"] = "f" * 64
    called = []
    result = retire_stale_runs(req, chain, get_json=called.append, cancel_run=called.append)
    assert result["status"] == "SKIPPED_RECEIPT_PINS_CHANGED"
    assert called == []


def test_retirement_never_cancels_running_or_changed_work():
    req, responses = fixture_runs()
    target = req["targets"][0]
    run_endpoint = f"repos/DWR-debug/trading-agent-public/actions/runs/{target['run_id']}"
    responses[run_endpoint]["status"] = "in_progress"
    cancelled = []
    result = retire_stale_runs(
        req,
        positive_chain(),
        get_json=lambda endpoint: responses[endpoint],
        cancel_run=cancelled.append,
    )
    assert cancelled == [38178545899]
    assert result["actions"][0]["status"] == "SKIPPED_RUN_STATE_MISMATCH"
    assert result["actions"][1]["status"] == "CANCEL_REQUESTED"


def test_retirement_never_cancels_if_active_job_names_differ():
    req, responses = fixture_runs()
    target = req["targets"][1]
    jobs_endpoint = f"repos/DWR-debug/trading-agent-public/actions/runs/{target['run_id']}/jobs?per_page=100"
    responses[jobs_endpoint]["jobs"].append({"name":"new_unreviewed_job","status":"queued"})
    cancelled = []
    result = retire_stale_runs(
        req,
        positive_chain(),
        get_json=lambda endpoint: responses[endpoint],
        cancel_run=cancelled.append,
    )
    assert cancelled == [38179574127]
    assert result["actions"][1]["status"] == "SKIPPED_ACTIVE_JOB_SET_MISMATCH"


def test_retirement_script_has_a_one_shot_push_trigger_and_explicit_actions_write():
    workflow = (ROOT / ".github/workflows/q220-as-filed-xbrl-population.yml").read_text(encoding="utf-8")
    job = workflow.split("  retire_stale_queued_runs:", 1)[1].split("  population:", 1)[0]
    assert "github.event_name == 'push'" in job
    assert "needs.receipt_gate.outputs.run_population == 'false'" in job
    assert "actions: write" in job
    assert "GH_TOKEN: ${{ github.token }}" in job
