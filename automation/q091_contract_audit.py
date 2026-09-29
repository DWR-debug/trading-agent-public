"""Read-only Q091 performance/source-contract audit."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREREG=ROOT/"research/preregistrations/q091_fixed_portfolio_architecture_2026_09_29.json"
PERF=ROOT/"automation/q091_performance.py"
PORT=ROOT/"portfolio/q091_fixed_ensemble.py"
REGISTRY=ROOT/"research/governance/active_research_registry.json"
SAFETY={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}
EXPECTED_VARIANTS={"E1_EQUAL_WEIGHT_Q069_5SLEEVE","E2_CROSS_SECTIONAL_RESIDUALIZED_Q069_5SLEEVE"}
EXPECTED_GATES={
 "research_return_positive","research_drawdown_lte_10pct","research_profit_factor_gte_1_10",
 "rolling_profit_factor_gte_1_10","rolling_profitable_window_ratio_gte_0_50",
 "rolling_average_drawdown_lte_10pct","oos_to_is_return_ratio_gte_0_25",
 "holdout_return_positive","holdout_profit_factor_gte_1_10","holdout_drawdown_lte_10pct",
 "stress_1_5x_holdout_nonnegative","stress_2x_holdout_nonnegative",
 "total_return_sensitivity_holdout_nonnegative",
}


def fp_bytes(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root:Path=ROOT)->dict:
    prereg=json.loads((root/PREREG.relative_to(ROOT)).read_text())
    perf_path=root/PERF.relative_to(ROOT)
    port_path=root/PORT.relative_to(ROOT)
    registry=json.loads((root/REGISTRY.relative_to(ROOT)).read_text())
    tree=ast.parse(perf_path.read_text())
    findings=[]
    def finding(code,**payload): findings.append({"code":code,"severity":"BLOCKING",**payload})

    if prereg.get("trial_id")!="T-2026-09-29-091": finding("Q091_TRIAL_ID_MISMATCH",actual=prereg.get("trial_id"))
    if prereg.get("status")!="PREREGISTERED_PERFORMANCE": finding("Q091_STATUS_INVALID",actual=prereg.get("status"))
    if prereg.get("safety")!=SAFETY: finding("Q091_SAFETY_MISMATCH")
    assignments={}
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:
                assignments[node.targets[0].id]=ast.literal_eval(node.value)
            except Exception:
                pass
    geometry_map={
        "requested_candles":"REQUESTED_CANDLES",
        "target_common_candles":"N",
        "research_periods":"RESEARCH",
        "holdout_periods":"HOLDOUT",
    }
    for field, runner_name in geometry_map.items():
        expected=prereg.get(field)
        actual=assignments.get(runner_name)
        if actual!=expected:
            finding("Q091_GEOMETRY_MISMATCH",field=field,expected=expected,actual=actual,runner_constant=runner_name)

    text_src=perf_path.read_text()
    if "urllib" in text_src or "requests" in text_src or "http://" in text_src or "https://" in text_src:
        finding("Q091_NETWORK_IN_PERFORMANCE_RUNNER")
    for guard in ("_assert_authorization(root, prereg)","_assert_source_contract(root, prereg)"):
        if guard not in text_src: finding("Q091_FAIL_CLOSED_GUARD_MISSING",guard=guard)

    assign={}
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try: assign[node.targets[0].id]=ast.literal_eval(node.value)
            except Exception: pass
    if set(assign.get("VARIANTS",()))!=EXPECTED_VARIANTS: finding("Q091_VARIANT_SET_MISMATCH",actual=assign.get("VARIANTS"))
    if set(assign.get("GATE_NAMES",()))!=EXPECTED_GATES: finding("Q091_GATE_SET_MISMATCH",actual=assign.get("GATE_NAMES"))

    contract=prereg.get("source_contract",{})
    actual={
      "performance_runner_sha256":fp_bytes(perf_path),
      "portfolio_architecture_sha256":fp_bytes(port_path),
      "candidate_bank_sha256":fp_bytes(root/"automation/q069_candidate_bank.py"),
      "cost_contract_sha256":fp_bytes(root/"execution/cost_contract.py"),
      "settings_sha256":fp_bytes(root/"config/settings.py"),
      "input_freeze_sha256":fp_bytes(root/"automation/q091_input_freeze.py"),
    }
    if contract!=actual: finding("Q091_SOURCE_CONTRACT_MISMATCH",expected=contract,actual=actual)

    entry=next((x for x in registry.get("active_trials",[]) if x.get("code")=="091"),None)
    if entry is None: finding("Q091_REGISTRY_ENTRY_MISSING")
    else:
        if entry.get("trial_id")!=prereg.get("trial_id"): finding("Q091_REGISTRY_ID_MISMATCH")
        if entry.get("performance_authorization_allowed") not in (False,True): finding("Q091_REGISTRY_AUTHORIZATION_STATE")

    result={"schema_version":"1.0","audit_id":"Q091-CONTRACT-AUDIT-2026-09-29","trial_id":prereg.get("trial_id"),
            "status":"PASS" if not findings else "FINDINGS_PRESENT","performance_authorization_changed":False,"performance_executed":False,
            "findings":findings,"observed":{"variants":sorted(EXPECTED_VARIANTS),"gate_count":len(EXPECTED_GATES),
            "registry_performance_authorization_allowed":entry.get("performance_authorization_allowed") if entry else None},"safety":SAFETY}
    result["audit_fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
    return result


if __name__=="__main__":
    print(json.dumps(audit(),indent=2,ensure_ascii=False))
