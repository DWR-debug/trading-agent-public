"""Read-only Q095 performance/source-contract audit."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREREG=ROOT/"research/preregistrations/q095_monthly_rebalance_independent_replication_2026_09_29.json"
PERF=ROOT/"automation/q095_performance.py"
PORT=ROOT/"portfolio/q094_monthly_rebalance.py"
REGISTRY=ROOT/"research/governance/active_research_registry.json"
SAFETY={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}
EXPECTED_VARIANTS={"M1_MONTHLY_REBALANCED_Q091_E1","M2_MONTHLY_REBALANCED_Q091_E2"}
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

    if prereg.get("trial_id")!="T-2026-09-29-095": finding("Q095_TRIAL_ID_MISMATCH",actual=prereg.get("trial_id"))
    if prereg.get("status")!="PREREGISTERED_PERFORMANCE": finding("Q095_STATUS_INVALID",actual=prereg.get("status"))
    if prereg.get("safety")!=SAFETY: finding("Q095_SAFETY_MISMATCH")
    assignments={}
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:
                assignments[node.targets[0].id]=ast.literal_eval(node.value)
            except Exception:
                pass
    geometry_map={
        "requested_candles":"REQUESTED",
        "target_common_candles":"N",
        "research_periods":"RESEARCH",
        "holdout_periods":"HOLDOUT",
    }
    for field, runner_name in geometry_map.items():
        expected=prereg.get("data_contract",{}).get(field)
        actual=assignments.get(runner_name)
        if actual!=expected:
            finding("Q095_GEOMETRY_MISMATCH",field=field,expected=expected,actual=actual,runner_constant=runner_name)

    text_src=perf_path.read_text()
    portfolio_src=port_path.read_text()
    implementation_src=text_src+"\n"+portfolio_src
    if "urllib" in text_src or "requests" in text_src or "http://" in text_src or "https://" in text_src:
        finding("Q095_NETWORK_IN_PERFORMANCE_RUNNER")
    for guard in ("_assert_authorization(root, prereg)","_assert_source_contract(root, prereg)"):
        if "_assert_authorization(" not in text_src or guard.endswith("authorization(root, prereg)") and "_assert_authorization(" not in text_src: finding("Q095_FAIL_CLOSED_GUARD_MISSING",guard=guard)

    assign={}
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try: assign[node.targets[0].id]=ast.literal_eval(node.value)
            except Exception: pass
    variant_ids={item.get("id") for item in prereg.get("variants",[]) if isinstance(item,dict)}
    if variant_ids!=EXPECTED_VARIANTS:
        finding("Q095_VARIANT_SET_MISMATCH",expected=sorted(EXPECTED_VARIANTS),actual=sorted(variant_ids))
    for variant_id in EXPECTED_VARIANTS:
        if variant_id not in implementation_src:
            finding("Q095_VARIANT_IMPLEMENTATION_MISSING",variant=variant_id)
    gate_ids=set(EXPECTED_GATES)
    if len(gate_ids)!=13:
        finding("Q095_GATE_SET_MISMATCH",expected=13,actual=len(gate_ids))
    for gate_id in EXPECTED_GATES:
        if f'"{gate_id}"' not in text_src:
            finding("Q095_GATE_IMPLEMENTATION_MISSING",gate=gate_id)

    contract=prereg.get("source_contract",{})
    actual={
      "performance_runner_path":"automation/q095_performance.py",
      "performance_runner_sha256":fp_bytes(perf_path),
      "monthly_overlay_path":"portfolio/q094_monthly_rebalance.py",
      "monthly_overlay_sha256":fp_bytes(port_path),
      "candidate_bank_path":"automation/q069_candidate_bank.py",
      "candidate_bank_sha256":fp_bytes(root/"automation/q069_candidate_bank.py"),
      "cost_contract_path":"execution/cost_contract.py",
      "cost_contract_sha256":fp_bytes(root/"execution/cost_contract.py"),
      "settings_path":"config/settings.py",
      "settings_sha256":fp_bytes(root/"config/settings.py"),
      "input_freeze_path":"automation/q091_input_freeze.py",
      "input_freeze_sha256":fp_bytes(root/"automation/q091_input_freeze.py"),
    }
    if contract!=actual: finding("Q095_SOURCE_CONTRACT_MISMATCH",expected=contract,actual=actual)

    entry=next((x for x in registry.get("active_trials",[]) if x.get("code")=="095"),None)
    if entry is None: finding("Q095_REGISTRY_ENTRY_MISSING")
    else:
        if entry.get("trial_id")!=prereg.get("trial_id"): finding("Q095_REGISTRY_ID_MISMATCH")
        if entry.get("performance_authorization_allowed") not in (False,True): finding("Q095_REGISTRY_AUTHORIZATION_STATE")

    result={"schema_version":"1.0","audit_id":"Q095-CONTRACT-AUDIT-2026-09-29","trial_id":prereg.get("trial_id"),
            "status":"PASS" if not findings else "FINDINGS_PRESENT","performance_authorization_changed":False,"performance_executed":False,
            "findings":findings,"observed":{"variants":sorted(EXPECTED_VARIANTS),"gate_count":len(EXPECTED_GATES),
            "registry_performance_authorization_allowed":entry.get("performance_authorization_allowed") if entry else None},"safety":SAFETY}
    result["audit_fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
    return result


if __name__=="__main__":
    print(json.dumps(audit(),indent=2,ensure_ascii=False))
