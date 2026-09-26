"""Validation helpers for the observed agent-usage ledger.

The ledger is intentionally evidence-like: only verified external agent activity
may enter it. Planned or attempted dispatches are not counted as actual usage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STATUSES = {
    "PLANNED",
    "DISPATCHED",
    "UNAVAILABLE",
    "DISPATCH_FAILED",
    "PR_CREATED",
    "MERGED",
}
TERMINAL_STATUSES = {"UNAVAILABLE", "DISPATCH_FAILED", "MERGED"}
OBSERVED_STATUSES = {"PR_CREATED", "MERGED"}


class AgentUsageLedgerError(ValueError):
    """Raised when the observed agent-usage ledger violates its contract."""


def validate_ledger(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") not in {"1.1", "1.2", 1.1, 1.2}:
        raise AgentUsageLedgerError("Unsupported ledger schema_version.")
    policy = payload.get("policy")
    if not isinstance(policy, dict):
        raise AgentUsageLedgerError("policy is required.")
    if policy.get("paid_agent_budget_usd") != 0:
        raise AgentUsageLedgerError("paid_agent_budget_usd must remain 0.")
    if policy.get("no_overage") is not True:
        raise AgentUsageLedgerError("no_overage must remain true.")

    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise AgentUsageLedgerError("entries must be a list.")

    entry_ids: set[str] = set()
    active_tasks = 0
    for entry in entries:
        if not isinstance(entry, dict):
            raise AgentUsageLedgerError("Each entry must be an object.")
        entry_id = entry.get("entry_id")
        task_id = entry.get("task_id")
        status = entry.get("status")
        if not isinstance(entry_id, str) or not entry_id.strip():
            raise AgentUsageLedgerError("entry_id is required.")
        if entry_id in entry_ids:
            raise AgentUsageLedgerError(f"Duplicate entry_id: {entry_id}.")
        entry_ids.add(entry_id)
        if not isinstance(task_id, str) or not task_id.strip():
            raise AgentUsageLedgerError("task_id is required.")
        if status not in STATUSES:
            raise AgentUsageLedgerError(f"Unknown status: {status}.")
        if entry.get("paid_usage", False) is not False:
            raise AgentUsageLedgerError(f"Paid usage claimed by {entry_id}.")
        if entry.get("verified") not in {True, False}:
            raise AgentUsageLedgerError(f"verified must be boolean for {entry_id}.")

        credits = entry.get("ai_credits_used")
        if credits is not None and (not isinstance(credits, (int, float)) or credits < 0):
            raise AgentUsageLedgerError(f"Invalid ai_credits_used for {entry_id}.")
        cost = entry.get("observed_cost_usd")
        if cost is not None and (not isinstance(cost, (int, float)) or cost < 0):
            raise AgentUsageLedgerError(f"Invalid observed_cost_usd for {entry_id}.")
        if cost not in {None, 0, 0.0}:
            raise AgentUsageLedgerError(
                f"Paid observed_cost_usd is forbidden for {entry_id}."
            )

        if status in OBSERVED_STATUSES:
            if entry.get("verified") is not True:
                raise AgentUsageLedgerError(
                    f"Observed usage must be verified for {entry_id}."
                )
            if not entry.get("pull_request"):
                raise AgentUsageLedgerError(
                    f"Observed usage requires pull_request for {entry_id}."
                )
            if not entry.get("commit_sha"):
                raise AgentUsageLedgerError(
                    f"Observed usage requires commit_sha for {entry_id}."
                )

        if status == "DISPATCHED":
            active_tasks += 1
        if status == "PR_CREATED":
            active_tasks += 0
        if status == "MERGED":
            active_tasks += 0

        if status in TERMINAL_STATUSES and entry.get("active", False):
            raise AgentUsageLedgerError(
                f"Terminal entry cannot be marked active: {entry_id}."
            )

    if active_tasks > 2:
        raise AgentUsageLedgerError(
            f"Ledger reports {active_tasks} concurrent dispatched tasks; maximum is 2."
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.ledger.read_text(encoding="utf-8"))
    validate_ledger(payload)
    print("AGENT USAGE LEDGER OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
