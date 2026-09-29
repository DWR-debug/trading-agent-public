"""Read-only Q089 preregistration/source-contract audit.

This audit never authorizes performance and never changes research state.
It detects provenance/contract mismatches before any one-shot performance
authorization can be considered.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research/preregistrations/q089_performance_2026_09_28.json"
PERF = ROOT / "automation/q089_performance.py"
COVERAGE = ROOT / "automation/q089_coverage_pit.py"
REGISTRY = ROOT / "research/governance/active_research_registry.json"

EXPECTED_SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


def _fp_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _literal_assignments(tree: ast.AST) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except Exception:
                    continue
    return values


def _find_result_literal(tree: ast.AST, key: str) -> Any:
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == key:
                    try:
                        return ast.literal_eval(v)
                    except Exception:
                        return None
    return None


def audit(root: Path = ROOT) -> dict[str, Any]:
    prereg = json.loads((root / PREREG.relative_to(ROOT)).read_text(encoding="utf-8"))
    perf_path = root / PERF.relative_to(ROOT)
    coverage_path = root / COVERAGE.relative_to(ROOT)
    registry = json.loads((root / REGISTRY.relative_to(ROOT)).read_text(encoding="utf-8"))

    perf_tree = ast.parse(perf_path.read_text(encoding="utf-8"))
    coverage_tree = ast.parse(coverage_path.read_text(encoding="utf-8"))
    perf_assign = _literal_assignments(perf_tree)
    coverage_assign = _literal_assignments(coverage_tree)

    findings: list[dict[str, Any]] = []

    def finding(code: str, severity: str, **payload: Any) -> None:
        findings.append({"code": code, "severity": severity, **payload})

    # Frozen trial geometry must agree with implementation constants.
    for name, expected_key in (
        ("N", "target_common_candles"),
        ("RESEARCH", "research_periods"),
        ("HOLDOUT", "holdout_periods"),
    ):
        actual = perf_assign.get(name)
        expected = prereg.get(expected_key)
        if actual != expected:
            finding("Q089_GEOMETRY_MISMATCH", "BLOCKING", field=name, expected=expected, actual=actual)

    # Coverage acquisition contract is separately frozen.
    for name, expected in (
        ("REQUESTED", prereg.get("requested_candles")),
        ("RAW", prereg.get("requested_candles")),
        ("TARGET", prereg.get("target_common_candles")),
    ):
        actual = coverage_assign.get(name)
        if actual != expected:
            finding(
                "Q089_COVERAGE_CONTRACT_MISMATCH",
                "BLOCKING",
                field=name,
                expected=expected,
                actual=actual,
            )

    run_fn = next((node for node in ast.walk(perf_tree) if isinstance(node, ast.FunctionDef) and node.name == "run"), None)
    run_calls = {
        node.func.id
        for node in ast.walk(run_fn)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    } if run_fn is not None else set()
    for required_guard in ("_assert_authorization", "_assert_source_contract"):
        if required_guard not in run_calls:
            finding(
                "Q089_FAIL_CLOSED_GUARD_MISSING",
                "BLOCKING",
                guard=required_guard,
            )

    reported_requested = _find_result_literal(perf_tree, "requested_candles")
    if reported_requested is None:
        reported_requested = perf_assign.get("REQUESTED_CANDLES")
    if reported_requested != prereg.get("requested_candles"):
        finding(
            "Q089_REPORT_REQUESTED_CANDLES_MISMATCH",
            "BLOCKING",
            field="performance_result.requested_candles",
            expected=prereg.get("requested_candles"),
            actual=reported_requested,
        )

    if prereg.get("safety") != EXPECTED_SAFETY:
        finding("Q089_PREREG_SAFETY_MISMATCH", "BLOCKING", expected=EXPECTED_SAFETY, actual=prereg.get("safety"))

    source_contract = prereg.get("source_contract", {})
    actual_contract = {
        "performance_runner_path": "automation/q089_performance.py",
        "performance_runner_sha256": _fp_bytes(perf_path),
        "candidate_bank_path": "automation/q069_candidate_bank.py",
        "candidate_bank_sha256": _fp_bytes(root / "automation/q069_candidate_bank.py"),
        "cost_contract_path": "execution/cost_contract.py",
        "cost_contract_sha256": _fp_bytes(root / "execution/cost_contract.py"),
        "settings_path": "config/settings.py",
        "settings_sha256": _fp_bytes(root / "config/settings.py"),
    }
    if source_contract != actual_contract:
        finding(
            "Q089_SOURCE_CONTRACT_MISMATCH",
            "BLOCKING",
            expected=source_contract,
            actual=actual_contract,
        )

    entry = next((x for x in registry.get("active_trials", []) if x.get("code") == "089"), None)
    if entry is None:
        finding("Q089_REGISTRY_ENTRY_MISSING", "BLOCKING")
    else:
        if entry.get("trial_id") != prereg.get("trial_id"):
            finding(
                "Q089_REGISTRY_ID_MISMATCH",
                "BLOCKING",
                expected=prereg.get("trial_id"),
                actual=entry.get("trial_id"),
            )
        if entry.get("performance_authorization_allowed") is not False:
            finding(
                "Q089_REGISTRY_AUTHORIZATION_STATE",
                "BLOCKING",
                expected=False,
                actual=entry.get("performance_authorization_allowed"),
            )

    result = {
        "schema_version": "1.0",
        "audit_id": "Q089-CONTRACT-AUDIT-2026-09-29",
        "trial_id": prereg.get("trial_id"),
        "status": "PASS" if not findings else "FINDINGS_PRESENT",
        "performance_authorization_changed": False,
        "performance_executed": False,
        "findings": findings,
        "observed": {
            "prereg_requested_candles": prereg.get("requested_candles"),
            "performance_result_requested_candles": reported_requested,
            "performance_constants": {
                "N": perf_assign.get("N"),
                "RESEARCH": perf_assign.get("RESEARCH"),
                "HOLDOUT": perf_assign.get("HOLDOUT"),
            },
            "coverage_constants": {
                "REQUESTED": coverage_assign.get("REQUESTED"),
                "RAW": coverage_assign.get("RAW"),
                "TARGET": coverage_assign.get("TARGET"),
            },
            "registry_performance_authorization_allowed": (
                entry.get("performance_authorization_allowed") if entry else None
            ),
        },
        "safety": EXPECTED_SAFETY,
    }
    result["audit_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return result


def main() -> int:
    result = audit()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
