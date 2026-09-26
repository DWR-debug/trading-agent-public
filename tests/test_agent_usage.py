import pytest

from automation.agent_usage import AgentUsageLedgerError, validate_ledger


def base_ledger():
    return {
        "schema_version": 1.2,
        "policy": {"paid_agent_budget_usd": 0, "no_overage": True},
        "entries": [],
    }


def test_empty_observed_ledger_is_valid():
    validate_ledger(base_ledger())


def test_observed_pr_requires_verification_and_provenance():
    payload = base_ledger()
    payload["entries"] = [{
        "entry_id": "AGENT-001",
        "task_id": "AGENT-TEST-001",
        "status": "PR_CREATED",
        "verified": True,
        "paid_usage": False,
        "pull_request": 999,
        "commit_sha": "a" * 40,
        "observed_cost_usd": 0,
    }]
    validate_ledger(payload)


def test_unverified_pr_is_rejected():
    payload = base_ledger()
    payload["entries"] = [{
        "entry_id": "AGENT-001",
        "task_id": "AGENT-TEST-001",
        "status": "PR_CREATED",
        "verified": False,
        "paid_usage": False,
        "pull_request": 999,
        "commit_sha": "a" * 40,
    }]
    with pytest.raises(AgentUsageLedgerError, match="verified"):
        validate_ledger(payload)


def test_paid_usage_is_rejected():
    payload = base_ledger()
    payload["entries"] = [{
        "entry_id": "AGENT-001",
        "task_id": "AGENT-TEST-001",
        "status": "MERGED",
        "verified": True,
        "paid_usage": True,
        "pull_request": 999,
        "commit_sha": "a" * 40,
    }]
    with pytest.raises(AgentUsageLedgerError, match="Paid usage"):
        validate_ledger(payload)


def test_duplicate_entry_is_rejected():
    payload = base_ledger()
    entry = {
        "entry_id": "AGENT-001",
        "task_id": "AGENT-TEST-001",
        "status": "DISPATCHED",
        "verified": False,
        "paid_usage": False,
        "active": True,
    }
    payload["entries"] = [entry, dict(entry)]
    with pytest.raises(AgentUsageLedgerError, match="Duplicate"):
        validate_ledger(payload)
