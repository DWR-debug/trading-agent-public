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
    "ci.yml",
    "research-orchestrator.yml",
    "paper-30-day-experiment-harness.yml",
    "q014-resilient.yml",
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


def main() -> None:
    workflow_dir = ROOT / ".github" / "workflows"
    active_workflows = {path.name for path in workflow_dir.glob("*.yml")}
    if active_workflows != ACTIVE_WORKFLOWS:
        fail(
            "unexpected active workflows: "
            + ", ".join(sorted(active_workflows - ACTIVE_WORKFLOWS))
        )
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
    # Only check the recent formally documented trial IDs to avoid imposing
    # a filename convention on legacy artifacts.
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
