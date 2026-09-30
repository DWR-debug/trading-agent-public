"""Fail-closed consistency checks for durable project context and evidence metadata.

This checker is intentionally lightweight and read-only. It does not decide whether
a research hypothesis is scientifically correct; it detects repository-state
inconsistencies that can silently break project memory or trial accounting.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ACTIVE_WORKFLOWS = {
    "agent-dispatch.yml",
    "agent-request-queue.yml",
    "ai-worker-fabric.yml",
    "autonomous-control-plane.yml",
    "ci.yml",
    "c29-fresh-coverage-pit.yml",
    "copilot-cli-ci-repair.yml",
    "copilot-cli-engineering-task.yml",
    "copilot-setup-steps.yml",
    "coverage-candidate-discovery.yml",
    "coverage-candidate-search.yml",
    "current-status-sync.yml",
    "f1-profitability-feasibility.yml",
    "f2-quality-acceleration-cloud.yml",
    "f2-quality-acceleration-feasibility.yml",
    "f2-sec-cloud-source-probe.yml",
    "fixed-study-window-candidate-discovery.yml",
    "h06-mechanism-replication-run.yml",
    "h06-mechanism-replication.yml",
    "h06-mechanism.yml",
    "intraday-directional-discovery.yml",
    "intraday-discovery.yml",
    "paper-2000-candidate.yml",
    "paper-30-day-experiment-harness.yml",
    "paper-500-candidate.yml",
    "paper-forward-persistent-mtm-2000.yml",
    "paper-forward-persistent-mtm.yml",
    "paper-forward-self-hosted-validation.yml",
    "permanent-pc-research-loop.yml",
    "public-frontier-feasibility.yml",
    "q014-resilient.yml",
    "q015-mechanism-discrimination.yml",
    "q017-coverage-first-standalone.yml",
    "q018-source-feasibility.yml",
    "q019-treasury-auction-contract.yml",
    "q020-treasury-auction-performance.yml",
    "q020-treasury-coverage-repair.yml",
    "q022-design-guard.yml",
    "q022-h1-directional-inversion-coverage.yml",
    "q022-h1-directional-inversion-performance.yml",
    "q023-treasury-release-timestamp-pit-feasibility.yml",
    "q024-treasury-auction-result-timestamp-pit-feasibility.yml",
    "q024-treasury-result-timestamp-pit.yml",
    "q025-treasury-auction-date-pit-feasibility.yml",
    "q031-q030-risk-stability-coverage.yml",
    "q032-q031-fixed-core-pit.yml",
    "q034-q033-mechanism-pit.yml",
    "q036-t056-risk-mechanism-diagnostic.yml",
    "q039-price-only-alpha-pit.yml",
    "q040-official-event-source-feasibility.yml",
    "q042-additional-price-alpha-pit.yml",
    "q043-fresh-disjoint-alpha-replication-coverage.yml",
    "q044-fresh-alpha-pit.yml",
    "q066-alpha-failure-diagnosis.yml",
    "q067-coverage-pit.yml",
    "q067-evidence-reconcile.yml",
    "q068-coverage-pit.yml",
    "q068-evidence-reconcile.yml",
    "q068-snapshot-recovery-audit.yml",
    "q070-coverage-pit.yml",
    "q070-evidence-reconcile.yml",
    "q071-source-feasibility.yml",
    "q072-candidate-bank.yml",
    "q074-extended-source-feasibility.yml",
    "q075-information-channel-contract.yml",
    "q077-fresh-e1-e2-discovery.yml",
    "q077r1-fresh-e1-e2-discovery.yml",
    "q077r1-pit.yml",
    "q079-fresh-e1-e2-coverage-pit.yml",
    "q079-fresh-e1-e2-discovery.yml",
    "q079-persist-frozen-input-bundle.yml",
    "q081r1-preflight.yml",
    "q081r1-selfhosted-reproduction.yml",
    "q081r2-preflight.yml",
    "q081r3-authorization-once.yml",
    "q081r4-authorization-once.yml",
    "q081r4-performance-once.yml",
    "q081r3-performance-once.yml",
    "q081r2-authorization-once.yml",
    "q081r2-performance-once.yml",
    "q083-feasibility.yml",
    "q084-feasibility.yml",
    "q085-coverage-pit.yml",
    "q086-coverage-pit.yml",
    "q089-contract-audit.yml",
    "q089-performance-once.yml",
    "q089-coverage-cloud-crosscheck.yml",
    "q089-coverage-pit.yml",
    "q090-q089-failure-diagnosis.yml",
    "q091-portfolio-architecture-coverage.yml",
    "q091-contract-audit.yml",
    "q091-performance-once.yml",
    "q091-input-freeze.yml",
    "q091-persist-input-freeze-artifact.yml",
    "q091-persist-coverage.yml",
    "q092-q091-failure-diagnosis.yml",
    "q093-q091-cost-attribution-diagnosis.yml",
    "q094-coverage-pit-input-freeze.yml",
    "q094-performance-once.yml",
    "q095-coverage-pit-input-freeze.yml",
    "q095-contract-audit.yml",
    "q095-performance-once.yml",
    "q095-authorization-once.yml",
    "rccsm-feasibility-cloud.yml",
    "rccsm-feasibility.yml",
    "rccsm-observational-feasibility-cloud.yml",
    "rccsm-observational-feasibility.yml",
    "rccsm-transition-diagnostic.yml",
    "research-governance-audit.yml",
    "research-orchestrator.yml",
    "self-hosted-ai-worker-fabric.yml",
    "self-hosted-capacity-autostart.yml",
    "self-hosted-continuous-qa.yml",
    "self-hosted-research-worker-v4.yml",
    "self-hosted-runner-probe.yml",
    "simulation-capital-focused-qa.yml",
    "t049-fixed-candidate-batch-coverage.yml",
    "t050-fixed-candidate-batch-02-coverage.yml",
    "t051-fixed-core-strategy-pit.yml",
    "t052-evidence-reconcile-once.yml",
    "t052-exact-master-ci-gate.yml",
    "t052-formal-once.yml",
    "ttaf-feasibility.yml",
    "wide-search.yml",
    "workflow-lint.yml",
}

REQUIRED_FILES = (
    ROOT / "PROJECT_STATUS.md",
    ROOT / "docs" / "PROJECT_CONTEXT.md",
    ROOT / "docs" / "PROJECT_CONTEXT_INGESTION.md",
    ROOT / "docs" / "research_archaeology_2026_09_24.md",
    ROOT / "research" / "evidence" / "project_context.json",
    ROOT / "docs" / "CHAT_CONTEXT_2026_09_24.md",
    ROOT / "docs" / "PRE_CLEANUP_INVENTORY_2026_09_24.md",
    ROOT / "research" / "evidence" / "trial_ledger.json",
)


def fail(message: str) -> None:
    raise SystemExit(f"PROJECT INTEGRITY FAIL: {message}")




def _validate_q067_evidence_chain() -> None:
    """Reject impossible Q067 evidence/authorization states before publishing CI truth."""
    root = ROOT
    evidence = root / "research" / "evidence"
    authorizations = root / "research" / "authorizations"
    auth_path = authorizations / "q067_performance_2026_09_28.json"
    perf_result = evidence / "q067_performance_result.json"
    coverage_result = evidence / "q067_coverage_result.json"
    pit_result = evidence / "q067_pit_result.json"
    if not auth_path.exists():
        if perf_result.exists():
            fail("Q067 performance evidence exists without performance authorization")
        return

    try:
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Q067 performance authorization is unreadable: {exc}")
    for name, expected in (
        ("authorized", True),
        ("performance_execution_authorized", True),
        ("execution_scope", "Q067_FIXED_RULE_PERFORMANCE_ONLY"),
    ):
        if auth.get(name) != expected:
            fail(f"Q067 performance authorization contract invalid: {name}")
    if auth.get("safety") != {
        "PAPER_ONLY": True,
        "LIVE_TRADING_ENABLED": False,
        "ORDERS_ENABLED": False,
        "AUTOMATIC_PROMOTION": False,
    }:
        fail("Q067 performance authorization safety contract invalid")

    for path, trial_id, status in (
        (coverage_result, "T-2026-09-28-067-COVERAGE", "COVERAGE_PASSED"),
        (pit_result, "T-2026-09-28-067-PIT", "PIT_PASSED"),
    ):
        if not path.exists():
            fail(f"Q067 performance authorization exists without prerequisite: {path.relative_to(root)}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("trial_id") != trial_id or payload.get("status") != status:
            fail(f"Q067 prerequisite invalid: {path.relative_to(root)}")
        if payload.get("performance_trial_authorized") is not False:
            fail(f"Q067 prerequisite unexpectedly authorizes performance: {path.relative_to(root)}")
        if payload.get("selection_used") is not False:
            fail(f"Q067 prerequisite records selection: {path.relative_to(root)}")

    if perf_result.exists():
        payload = json.loads(perf_result.read_text(encoding="utf-8"))
        if payload.get("trial_id") != "T-2026-09-28-067-PERFORMANCE":
            fail("Q067 performance evidence trial identity mismatch")
        if payload.get("status") != "COMPLETED":
            fail("Q067 performance evidence is not completed")
        if payload.get("selection_used") is not False:
            fail("Q067 performance evidence records selection")
        if payload.get("holdout_used_for_selection") is not False:
            fail("Q067 performance evidence records holdout selection")


def main() -> None:
    workflow_dir = ROOT / ".github" / "workflows"
    active_workflows = {path.name for path in workflow_dir.glob("*.yml")}
    if active_workflows != ACTIVE_WORKFLOWS:
        fail(
            "unexpected active workflows: "
            + ", ".join(sorted(active_workflows - ACTIVE_WORKFLOWS))
        )
    _validate_q067_evidence_chain()

    for path in REQUIRED_FILES:
        if not path.exists():
            fail(f"missing required file: {path.relative_to(ROOT)}")

    status = (ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    for marker in (
        "docs/PROJECT_CONTEXT.md",
        "docs/PROJECT_CONTEXT_INGESTION.md",
        "docs/research_archaeology_2026_09_24.md",
        "research/evidence/project_context.json",
        "GitHub-",
        "technische Referenz",
    ):
        if marker not in status:
            fail(f"PROJECT_STATUS missing governance marker: {marker}")

    context = (ROOT / "research" / "evidence" / "project_context.json")
    index = json.loads(context.read_text(encoding="utf-8"))

    if index.get("repository") != "DWR-debug/trading-agent-public":
        fail("context index repository mismatch")

    safety = index.get("safety", {})
    if safety.get("paper_only") is not True:
        fail("paper_only invariant is not true in context index")
    if safety.get("live_trading_enabled") is not False:
        fail("live_trading_enabled invariant is not false in context index")
    if safety.get("orders_enabled") is not False:
        fail("orders_enabled invariant is not false in context index")

    documents = index.get("documents", {})
    for key, relpath in (
        ("project_context", "docs/PROJECT_CONTEXT.md"),
        ("chat_context_ingestion", "docs/PROJECT_CONTEXT_INGESTION.md"),
        ("research_archaeology", "docs/research_archaeology_2026_09_24.md"),
        ("chat_context", "docs/CHAT_CONTEXT_2026_09_24.md"),
        ("pre_cleanup_inventory", "docs/PRE_CLEANUP_INVENTORY_2026_09_24.md"),
    ):
        if documents.get(key) != relpath:
            fail(f"context index document mismatch: {key}")

    ledger = json.loads(
        (ROOT / "research" / "evidence" / "trial_ledger.json").read_text(
            encoding="utf-8"
        )
    )
    entries = ledger.get("trials", ledger.get("entries", ledger))
    if not isinstance(entries, list):
        fail("trial ledger is not a list")

    ids = [entry.get("trial_id") for entry in entries]
    if any(not trial_id for trial_id in ids):
        fail("ledger contains an entry without trial_id")
    if len(ids) != len(set(ids)):
        fail("duplicate trial_id in ledger")

    for entry in entries:
        status_value = entry.get("status")
        if status_value == "data_invalid":
            outcome = entry.get("outcome", {})
            if outcome.get("no_performance_claim") is False:
                fail(
                    f"{entry['trial_id']} is data_invalid but explicitly "
                    "declares a performance claim"
                )
            if outcome.get("validation_status") not in (None, "DATA_INVALID"):
                fail(
                    f"{entry['trial_id']} is data_invalid but has "
                    "non-DATA_INVALID validation status"
                )

    trial_docs = {
        path.name
        for path in (ROOT / "docs").glob("trial*.md")
    }
    for trial_id in ("T-2026-09-24-029", "T-2026-09-24-030",
                     "T-2026-09-24-031", "T-2026-09-24-032",
                     "T-2026-09-24-033"):
        suffix = trial_id.rsplit("-", 1)[-1]
        if not any(f"trial_{suffix}" in name for name in trial_docs):
            fail(f"recent formal trial has no discoverable trial doc: {trial_id}")

    print("PROJECT INTEGRITY OK")
    print(f"ledger_entries={len(entries)}")
    print("safety=paper_only")
    print("context_sources=technical/evidence/project-intent/work-state")


if __name__ == "__main__":
    main()
