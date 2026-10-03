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


def validate(root: Path = ROOT) -> dict:
    root = root.resolve()
    policy_path = root / "research" / "governance" / "critical_research_quality_control.json"
    registry_path = root / "research" / "governance" / "active_research_registry.json"
    policy = load(policy_path)
    registry = load(registry_path)
    required_robustness = set(policy["early_robustness"]["required_dimensions"])
    violations: list[str] = []

    for entry in registry.get("active_trials", []):
        state = str(entry.get("state", ""))
        if entry.get("performance_authorization_allowed") is not True and state not in AUTHORIZED_STATES:
            continue

        prereg_path = root / entry["preregistration_path"]
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

        robustness_receipt = prereg.get("pre_performance_robustness")
        if not isinstance(robustness_receipt, dict):
            violations.append(f"{entry.get('code')}: missing pre_performance_robustness receipt")
        else:
            required_receipt_fields = (
                "trial_id",
                "status",
                "artifact_path",
                "artifact_sha256",
                "research_only",
                "screen_is_descriptive_only",
                "no_post_hoc_tuning",
            )
            for field in required_receipt_fields:
                if field not in robustness_receipt:
                    violations.append(f"{entry.get('code')}: robustness receipt missing {field}")
            if robustness_receipt.get("trial_id") != entry.get("trial_id"):
                violations.append(f"{entry.get('code')}: robustness receipt trial_id mismatch")
            if robustness_receipt.get("status") != "PRE_PERFORMANCE_ROBUSTNESS_COMPLETED":
                violations.append(f"{entry.get('code')}: robustness receipt status invalid")
            if robustness_receipt.get("research_only") is not True:
                violations.append(f"{entry.get('code')}: robustness receipt is not research-only")
            if robustness_receipt.get("screen_is_descriptive_only") is not True:
                violations.append(f"{entry.get('code')}: robustness screen is not descriptive-only")
            if robustness_receipt.get("no_post_hoc_tuning") is not True:
                violations.append(f"{entry.get('code')}: robustness receipt permits post-hoc tuning")

            artifact_path = robustness_receipt.get("artifact_path")
            artifact_sha256 = robustness_receipt.get("artifact_sha256")
            if isinstance(artifact_path, str) and artifact_path:
                artifact = root / artifact_path
                if not artifact.is_file():
                    violations.append(f"{entry.get('code')}: robustness artifact missing: {artifact_path}")
                elif isinstance(artifact_sha256, str) and artifact_sha256:
                    actual_sha = __import__("hashlib").sha256(artifact.read_bytes()).hexdigest()
                    if actual_sha != artifact_sha256:
                        violations.append(f"{entry.get('code')}: robustness artifact sha256 mismatch")
                try:
                    payload = load(artifact) if artifact.is_file() else {}
                except Exception as exc:
                    violations.append(f"{entry.get('code')}: robustness artifact unreadable: {exc}")
                    payload = {}
                if isinstance(payload, dict):
                    if payload.get("trial_id") != entry.get("trial_id"):
                        violations.append(f"{entry.get('code')}: robustness artifact trial_id mismatch")
                    if payload.get("status") != "PRE_PERFORMANCE_ROBUSTNESS_COMPLETED":
                        violations.append(f"{entry.get('code')}: robustness artifact status invalid")
                    metrics = payload.get("metrics")
                    if not isinstance(metrics, dict):
                        violations.append(f"{entry.get('code')}: robustness artifact missing metrics object")
                    else:
                        missing_metrics = sorted(required_robustness - set(metrics))
                        if missing_metrics:
                            violations.append(
                                f"{entry.get('code')}: robustness artifact missing metrics: {missing_metrics}"
                            )
                    governance = payload.get("governance")
                    if not isinstance(governance, dict) or any(
                        governance.get(key) is not False
                        for key in (
                            "holdout_selection",
                            "parameter_search",
                            "asset_search",
                            "threshold_search",
                            "horizon_search",
                            "variant_search",
                            "family_ranking",
                            "promotion_decision",
                            "performance_authorization",
                        )
                    ):
                        violations.append(f"{entry.get('code')}: robustness artifact governance boundary invalid")

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
