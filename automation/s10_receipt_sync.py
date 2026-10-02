"""Validate and normalize the S10 phone-workflow artifact into a safe OS status record.

The resulting status is operational metadata only. It cannot create scientific
evidence, authorize performance, rank candidates or promote a model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SAFE_EXPECTED = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
    "scientific_evidence": False,
    "performance_authorization": False,
}


def _load(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_status(
    artifact_root: Path,
    *,
    workflow_run_id: str,
    workflow_conclusion: str,
    source_commit: str,
    artifact_id: str | None,
    artifact_digest: str | None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    provenance = _load(artifact_root / "provenance_receipt.json")
    acceptance = _load(artifact_root / "s10_acceptance_receipt.json")
    result = _load(artifact_root / "evidence_critic.json")

    base = {
        "schema_version": 1,
        "status_type": "s10_phone_operational_status",
        "source_workflow": "S10 Phone Research Worker",
        "workflow_run_id": workflow_run_id,
        "workflow_conclusion": workflow_conclusion,
        "source_commit": source_commit,
        "artifact_id": artifact_id,
        "artifact_digest": artifact_digest,
        "generated_at_utc": generated_at_utc or datetime.now(timezone.utc).isoformat(),
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

    if provenance is None:
        base.update({
            "status": "S10_ARTIFACT_INVALID",
            "eligible": False,
            "receipt_status": "PROVENANCE_MISSING",
        })
        return base

    provenance_ok = all(provenance.get(key) is expected for key, expected in SAFE_EXPECTED.items())
    if not provenance_ok:
        base.update({
            "status": "S10_ARTIFACT_POLICY_INVALID",
            "eligible": False,
            "receipt_status": "PROVENANCE_POLICY_VIOLATION",
        })
        return base

    acceptance_status = acceptance.get("status") if acceptance else None
    worker_status = result.get("status") if result else None
    eligible = acceptance_status == "S10_UTILITY_ACCEPTED"

    base.update({
        "status": "S10_UTILITY_ACCEPTED" if eligible else ("S10_RESULT_AVAILABLE" if result else "S10_ARTIFACT_INCOMPLETE"),
        "eligible": eligible,
        "receipt_status": acceptance_status or worker_status or "NOT_PRESENT",
        "acceptance_receipt_sha256": _sha256(artifact_root / "s10_acceptance_receipt.json") if acceptance else None,
        "worker_status": worker_status,
        "model": (acceptance or {}).get("model") or (result or {}).get("model"),
        "runner_name": provenance.get("runner_name"),
        "runner_arch": provenance.get("runner_arch"),
    })
    return base


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-root", type=Path, required=True)
    ap.add_argument("--workflow-run-id", required=True)
    ap.add_argument("--workflow-conclusion", required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--artifact-id")
    ap.add_argument("--artifact-digest")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    status = build_status(
        args.artifact_root,
        workflow_run_id=args.workflow_run_id,
        workflow_conclusion=args.workflow_conclusion,
        source_commit=args.source_commit,
        artifact_id=args.artifact_id,
        artifact_digest=args.artifact_digest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status["status"],
        "eligible": status["eligible"],
        "workflow_run_id": status["workflow_run_id"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
