"""Create the predeclared independent-replication trigger after a full formal pass.

This tool is deliberately narrow: it never invents a replication plan, never
changes a passed candidate, never selects a candidate, and never authorizes
promotion. Missing contracts fail closed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "research/governance/active_research_registry.json"
LEDGER_PATH = ROOT / "research/evidence/trial_ledger.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.repo_root
    registry = load(root / REGISTRY_PATH.relative_to(ROOT))
    ledger = load(root / LEDGER_PATH.relative_to(ROOT))
    entries = ledger.get("trials", ledger.get("entries", ledger))
    created: list[str] = []

    for trial in entries:
        if trial.get("status") != "performance_completed_arm_passed_all_13_gates":
            continue
        trial_id = trial.get("trial_id")
        reg = next((x for x in registry.get("active_trials", []) if x.get("trial_id") == trial_id), None)
        if not reg:
            raise RuntimeError(f"Passed trial {trial_id} is absent from active registry")

        prereg_rel = reg.get("preregistration_path")
        if not prereg_rel:
            raise RuntimeError(f"{trial_id}: missing preregistration path")
        prereg = load(root / prereg_rel)
        replication = prereg.get("independent_replication")
        required = ("trial_id", "preregistration_path", "trigger_path", "fresh_symbol_disjoint", "no_post_pass_optimization")
        if not isinstance(replication, dict) or any(k not in replication for k in required):
            raise RuntimeError(f"{trial_id}: missing predeclared independent replication contract")
        if replication["fresh_symbol_disjoint"] is not True or replication["no_post_pass_optimization"] is not True:
            raise RuntimeError(f"{trial_id}: replication contract is not independent/fixed")
        trigger_rel = replication["trigger_path"]
        if not trigger_rel.startswith("research/run_requests/"):
            raise RuntimeError(f"{trial_id}: invalid replication trigger path")
        trigger = root / trigger_rel
        if trigger.exists():
            continue
        trigger.parent.mkdir(parents=True, exist_ok=True)
        trigger.write_text(
            f"RUN_INDEPENDENT_REPLICATION=true\n"
            f"SOURCE_TRIAL_ID={trial_id}\n"
            f"REPLICATION_TRIAL_ID={replication['trial_id']}\n"
            f"ONE_SHOT=true\n",
            encoding="utf-8",
        )
        created.append(trigger_rel)

    print(json.dumps({"status": "PASS", "triggers_created": sorted(created)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
