"""One-shot, fail-closed retirement of explicitly pinned stale Q220 queued runs.

Only queued/pending runs with exact run ID, workflow name, event, commit SHA, and
active job set may be cancelled. The current Q220 population/compiler/independent
receipt chain must still match the frozen pins. Running jobs are never cancelled.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Mapping

from automation.q220_receipt_chain import ROOT, evaluate_q220_receipt_chain

DEFAULT_REQUEST = ROOT / "research/run_requests/q220_stale_run_retirement_2026_10_12.json"
RUNNABLE_STATUSES = frozenset({"queued", "pending"})
ACTIVE_JOB_STATUSES = frozenset({"queued", "pending", "waiting", "in_progress"})


def retire_stale_runs(
    request: Mapping[str, Any],
    receipt_chain: Mapping[str, Any],
    *,
    get_json: Callable[[str], dict[str, Any]],
    cancel_run: Callable[[int], None],
) -> dict[str, Any]:
    """Cancel only allow-listed stale queue entries when the positive Q220 chain remains pinned."""
    if request.get("record_type") != "q220_stale_run_retirement_request":
        return {"status": "SKIPPED_INVALID_REQUEST", "actions": []}
    if request.get("candidate_id") != "Q220":
        return {"status": "SKIPPED_WRONG_CANDIDATE", "actions": []}
    if receipt_chain.get("independent_positive") is not True:
        return {"status": "SKIPPED_RECEIPT_CHAIN_NOT_POSITIVE", "actions": []}

    expected_receipts = request.get("required_receipt_fingerprints")
    if not isinstance(expected_receipts, dict) or any(
        receipt_chain.get(key) != value for key, value in expected_receipts.items()
    ):
        return {"status": "SKIPPED_RECEIPT_PINS_CHANGED", "actions": []}

    targets = request.get("targets")
    if not isinstance(targets, list) or not targets or len(targets) > 5:
        return {"status": "SKIPPED_INVALID_TARGET_LIST", "actions": []}

    actions: list[dict[str, Any]] = []
    errors = False
    for target in targets:
        if not isinstance(target, dict):
            actions.append({"status": "SKIPPED_INVALID_TARGET"})
            continue
        run_id = target.get("run_id")
        if isinstance(run_id, bool) or not isinstance(run_id, int) or run_id <= 0:
            actions.append({"status": "SKIPPED_INVALID_RUN_ID"})
            continue
        if not set(target.get("allowed_run_statuses", [])) or not set(
            target.get("allowed_run_statuses", [])
        ) <= RUNNABLE_STATUSES:
            actions.append({"run_id": run_id, "status": "SKIPPED_UNSAFE_STATUS_ALLOWLIST"})
            continue

        run_endpoint = f"repos/DWR-debug/trading-agent-public/actions/runs/{run_id}"
        jobs_endpoint = f"{run_endpoint}/jobs?per_page=100"
        try:
            run = get_json(run_endpoint)
            if (
                run.get("id") != run_id
                or run.get("name") != target.get("expected_workflow_name")
                or run.get("head_sha") != target.get("expected_head_sha")
                or run.get("event") != target.get("expected_event")
                or run.get("status") not in target.get("allowed_run_statuses", [])
            ):
                actions.append({"run_id": run_id, "status": "SKIPPED_RUN_STATE_MISMATCH"})
                continue

            payload = get_json(jobs_endpoint)
            jobs = payload.get("jobs")
            if not isinstance(jobs, list):
                actions.append({"run_id": run_id, "status": "SKIPPED_JOB_LIST_UNAVAILABLE"})
                continue
            active_names = sorted(
                str(job.get("name") or "")
                for job in jobs
                if isinstance(job, dict) and job.get("status") in ACTIVE_JOB_STATUSES
            )
            expected_names = sorted(str(name) for name in target.get("expected_active_job_names", []))
            if not expected_names or active_names != expected_names:
                actions.append({
                    "run_id": run_id,
                    "status": "SKIPPED_ACTIVE_JOB_SET_MISMATCH",
                    "observed_active_job_names": active_names,
                })
                continue

            cancel_run(run_id)
            actions.append({
                "run_id": run_id,
                "status": "CANCEL_REQUESTED",
                "reason": str(target.get("reason") or ""),
                "active_job_names": active_names,
            })
        except Exception as exc:  # fail closed on a GitHub API uncertainty
            errors = True
            actions.append({
                "run_id": run_id,
                "status": "API_OR_CANCELLATION_ERROR",
                "error_type": type(exc).__name__,
            })

    return {
        "status": "PARTIAL_ERROR" if errors else "COMPLETE",
        "actions": actions,
        "scientific_evidence": False,
        "performance_authorization": False,
        "live_execution": False,
    }


def gh_json(endpoint: str) -> dict[str, Any]:
    result = subprocess.run(
        ["gh", "api", endpoint],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise ValueError("GitHub API response is not an object")
    return payload


def gh_cancel(run_id: int) -> None:
    subprocess.run(
        [
            "gh", "api", "--method", "POST",
            f"repos/DWR-debug/trading-agent-public/actions/runs/{run_id}/cancel",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    args = parser.parse_args()
    request_path = args.request if args.request.is_absolute() else ROOT / args.request
    try:
        request = json.loads(request_path.read_text(encoding="utf-8"))
        chain = evaluate_q220_receipt_chain(ROOT)
        result = retire_stale_runs(
            request,
            chain,
            get_json=gh_json,
            cancel_run=gh_cancel,
        )
    except Exception as exc:
        print(json.dumps({
            "status": "FAILED_CLOSED",
            "error_type": type(exc).__name__,
            "scientific_evidence": False,
            "performance_authorization": False,
        }, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 1 if result.get("status") == "PARTIAL_ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
