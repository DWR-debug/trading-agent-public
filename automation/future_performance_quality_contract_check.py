"""Fail-closed pre-performance quality contract validator.

Future performance authorizations must carry an explicit early-robustness
measurement contract and an independent replication contract. Historical
completed trials are left untouched.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "research/governance/critical_research_quality_control.json"
REGISTRY_PATH = ROOT / "research/governance/active_research_registry.json"


AUTHORIZED_STATES = {
    "PERFORMANCE_AUTHORIZED",
    "PREREGISTERED_PERFORMANCE",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> dict:
    policy = load(POLICY_PATH)
    registry = load(REGISTRY_PATH)
    required_robustness = set(policy["early_robustness"]["required_dimensions"])
    violations: list[str] = []

    for entry in registry.get("active_trials", []):
        state = str(entry.get("state", ""))
        if entry.get("performance_authorization_allowed") is not True and state not in AUTHORIZED_STATES:
            continue

        prereg_path = ROOT / entry["preregistration_path"]
        if not prereg_path.is_file():
            violations.append(f"{entry.get('code')}: missing preregistration")
            continue

        prereg = load(prereg_path)
        robustness = prereg.get("robustness_contract")
        if not isinstance(robustness, dict):
            violations.append(f"{entry.get('code')}: missing robustness_contract")
        else:
            declared = set(robustness.get("required_dimensions", []))
            if not required_robustness.issubset(declared):
                violations.append(f"{entry.get('code')}: incomplete robustness dimensions")
            if robustness.get("research_only_before_formal_pass") is not True:
                violations.append(f"{entry.get('code')}: robustness contract is not research-only")

        replication = prereg.get("independent_replication")
        if not isinstance(replication, dict):
            violations.append(f"{entry.get('code')}: missing independent_replication")
            continue
        for field in (
            "trial_id",
            "preregistration_path",
            "trigger_path",
            "fresh_symbol_disjoint",
            "no_post_pass_optimization",
        ):
            if field not in replication:
                violations.append(f"{entry.get('code')}: replication contract missing {field}")
        if replication.get("fresh_symbol_disjoint") is not True:
            violations.append(f"{entry.get('code')}: replication is not explicitly independent")
        if replication.get("no_post_pass_optimization") is not True:
            violations.append(f"{entry.get('code')}: post-pass optimization is not forbidden")
        trigger = replication.get("trigger_path")
        if isinstance(trigger, str) and not trigger.startswith("research/run_requests/"):
            violations.append(f"{entry.get('code')}: replication trigger path is outside run_requests")

    if violations:
        raise RuntimeError("CRITICAL RESEARCH QUALITY CONTRACT FAIL: " + "; ".join(violations))

    return {
        "status": "PASS",
        "authorized_entries_checked": sum(
            1
            for x in registry.get("active_trials", [])
            if x.get("performance_authorization_allowed") is True
            or str(x.get("state", "")) in AUTHORIZED_STATES
        ),
        "required_robustness_dimensions": sorted(required_robustness),
        "immediate_replication_required": policy["immediate_replication"]["required_for_any_future_full_formal_pass"],
    }


def main() -> int:
    result = validate()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
