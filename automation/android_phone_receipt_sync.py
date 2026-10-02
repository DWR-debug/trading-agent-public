"""Normalize Samsung Android phone receipts without revoking valid acceptance on utility runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ACCEPTANCE_STATUS = "ANDROID_PHONE_UTILITY_ACCEPTED"
CONTRACT = "2026-10-02-R3"


def _load(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def build_status(
    artifact_root: Path,
    *,
    resource_id: str,
    workflow_run_id: str,
    workflow_conclusion: str,
    source_commit: str,
    workflow_run_updated_at: str,
    existing: dict[str, Any] | None,
) -> dict[str, Any]:
    receipt = next(artifact_root.rglob("android_phone_acceptance_receipt.json"), None)
    utility = next(artifact_root.rglob("utility_task.json"), None)
    acceptance = _load(receipt) if receipt else None
    utility_data = _load(utility) if utility else None

    accepted_now = (
        workflow_conclusion == "success"
        and acceptance is not None
        and acceptance.get("status") == ACCEPTANCE_STATUS
        and acceptance.get("acceptance_contract_version") == CONTRACT
    )
    prior_accepted = (
        acceptance is None
        and existing is not None
        and existing.get("status") == ACCEPTANCE_STATUS
        and existing.get("eligible") is True
        and existing.get("acceptance_contract_version") == CONTRACT
    )

    if accepted_now:
        status = ACCEPTANCE_STATUS
        eligible = True
        runner_name = acceptance.get("runner_name")
        model = acceptance.get("model")
        endpoint = acceptance.get("endpoint")
        acceptance_contract_version = acceptance.get("acceptance_contract_version")
        acceptance_receipt_sha256 = acceptance.get("result_sha256")
    elif prior_accepted:
        status = ACCEPTANCE_STATUS
        eligible = True
        runner_name = existing.get("runner_name")
        model = existing.get("model")
        endpoint = existing.get("endpoint")
        acceptance_contract_version = existing.get("acceptance_contract_version")
        acceptance_receipt_sha256 = existing.get("acceptance_receipt_sha256")
    else:
        status = (
            str(acceptance.get("status"))
            if acceptance is not None
            else ("ANDROID_PHONE_UTILITY_NOT_ACCEPTED" if utility_data is None else str(utility_data.get("status", "ANDROID_PHONE_UTILITY_NOT_ACCEPTED")))
        )
        eligible = status == ACCEPTANCE_STATUS
        runner_name = (acceptance or {}).get("runner_name") or (utility_data or {}).get("runner_name")
        model = (acceptance or {}).get("model") or (utility_data or {}).get("model")
        endpoint = (acceptance or {}).get("endpoint") or (utility_data or {}).get("endpoint")
        acceptance_contract_version = (acceptance or {}).get("acceptance_contract_version")
        acceptance_receipt_sha256 = (acceptance or {}).get("result_sha256")

    return {
        "schema_version": 1,
        "status_type": "android_phone_operational_status",
        "resource_id": resource_id,
        "workflow_name": "Android Phone Fleet Worker",
        "workflow_run_id": workflow_run_id,
        "workflow_conclusion": workflow_conclusion,
        "source_commit": source_commit,
        "workflow_run_updated_at": workflow_run_updated_at,
        "status": status,
        "eligible": eligible,
        "runner_name": runner_name,
        "model": model,
        "endpoint": endpoint,
        "acceptance_contract_version": acceptance_contract_version,
        "acceptance_receipt_sha256": acceptance_receipt_sha256,
        "utility_task_status": (utility_data or {}).get("status"),
        "utility_task_id": (utility_data or {}).get("task_id"),
        "acceptance_preserved": prior_accepted,
        "scientific_evidence": False,
        "performance_authorization": False,
        "candidate_selection": False,
        "candidate_ranking": False,
        "promotion": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-root", type=Path, required=True)
    ap.add_argument("--existing-status", type=Path)
    ap.add_argument("--resource-id", required=True)
    ap.add_argument("--workflow-run-id", required=True)
    ap.add_argument("--workflow-conclusion", required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--workflow-updated-at", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    existing = _load(args.existing_status) if args.existing_status else None
    status = build_status(
        args.artifact_root,
        resource_id=args.resource_id,
        workflow_run_id=args.workflow_run_id,
        workflow_conclusion=args.workflow_conclusion,
        source_commit=args.source_commit,
        workflow_run_updated_at=args.workflow_updated_at,
        existing=existing,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"resource_id": args.resource_id, "status": status["status"], "eligible": status["eligible"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
