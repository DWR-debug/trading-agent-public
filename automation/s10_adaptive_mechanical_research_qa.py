"""Adaptive deterministic QA for the dedicated S10/Termux worker.

This lane rotates through mechanical repository checks. It never invokes an LLM
and never produces scientific evidence or authorization.
"""
from __future__ import annotations
import argparse, hashlib, json, os
from pathlib import Path

MODES = ("PROVENANCE_STATUS","FRONTIER_GOVERNANCE","PIT_CLOCK_LINEAGE","CAPACITY_DISPATCH","NEGATIVE_EVIDENCE_DEDUP")
FORBIDDEN = {"performance","performance_authorized","performance_authorization_allowed","holdout_selection","holdout_selection_allowed","ranking","family_ranking_allowed","parameter_search_allowed","asset_search_allowed","threshold_search_allowed","horizon_search_allowed","variant_search_allowed","promotion","automatic_promotion","live_execution","live_trading_enabled","orders_enabled"}
SAFETY = {"PAPER_ONLY": True, "LIVE_TRADING_ENABLED": False, "ORDERS_ENABLED": False, "AUTOMATIC_PROMOTION": False}
CORE = ("docs/CURRENT_STATUS.md","research/evidence/current_operational_state.json","research/governance/active_research_registry.json","research/governance/persistent_research_acceleration_contract.json","research/governance/critical_research_quality_control.json","research/governance/literature_research_policy.json","research/run_requests/rolling_capacity_window_2026-10-05.json")

def load(p: Path): return json.loads(p.read_text(encoding="utf-8"))
def sha(p: Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values(): yield from walk(x)
    elif isinstance(v,list):
        for x in v: yield from walk(x)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    root=a.repo_root.resolve()
    run_no=int(os.environ.get("GITHUB_RUN_NUMBER","0") or 0)
    mode=MODES[run_no % len(MODES)]
    failures=[]; findings=[]
    for rel in CORE:
        p=root/rel
        if not p.is_file(): failures.append("missing:"+rel)
        else: findings.append({"path":rel,"sha256":sha(p),"bytes":p.stat().st_size})
    try:
        status=load(root/"research/evidence/current_operational_state.json")
        registry=load(root/"research/governance/active_research_registry.json")
        accel=load(root/"research/governance/persistent_research_acceleration_contract.json")
        critical=load(root/"research/governance/critical_research_quality_control.json")
        literature=load(root/"research/governance/literature_research_policy.json")
        lease=load(root/"research/run_requests/rolling_capacity_window_2026-10-05.json")
    except Exception as exc:
        failures.append(f"core_json:{type(exc).__name__}:{exc}")
        status=registry=accel=critical=literature=lease={}
    if accel.get("status")!="ACTIVE": failures.append("acceleration_contract_not_active")
    if critical.get("status")!="ACTIVE": failures.append("critical_quality_control_not_active")
    safety=critical.get("safety",{})
    for k,v in {"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}.items():
        if safety.get(k) is not v: failures.append(f"critical_safety:{k}")
    for k,v in {"performance":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False}.items():
        if lease.get("safety",{}).get(k) is not v: failures.append(f"lease_safety:{k}")
    findings.append({"run_sha":os.environ.get("GITHUB_SHA"),"status_source_sha":status.get("source_master_sha"),"mode":mode})
    if mode=="FRONTIER_GOVERNANCE":
        for rel in CORE:
            p=root/rel
            if not p.exists() or not rel.endswith(".json"): continue
            try: obj=load(p)
            except Exception: continue
            for node in walk(obj):
                for k in FORBIDDEN:
                    if node.get(k) is True: failures.append(f"forbidden_true:{rel}:{k}")
    elif mode=="PIT_CLOCK_LINEAGE":
        frontier=list((root/"research/frontier").glob("*.json"))
        checked=0
        for p in frontier[:80]:
            try: obj=load(p)
            except Exception: continue
            s=json.dumps(obj,ensure_ascii=False).lower()
            if any(x in s for x in ("pit","clock","public","filing","vintage")):
                checked+=1
                if not any(x in s for x in ("revision","amendment","lineage")):
                    findings.append({"path":str(p.relative_to(root)),"lineage_marker":False})
        findings.append({"frontier_json_checked":checked})
    elif mode=="CAPACITY_DISPATCH":
        phases=lease.get("phases",[])
        seen={}
        for phase in phases:
            pid=str(phase.get("id","")); seen.setdefault(pid,set())
            for wf in phase.get("workflows",[]):
                if wf in seen[pid]: failures.append(f"duplicate:{pid}:{wf}")
                seen[pid].add(wf)
                if not (root/".github/workflows"/wf).is_file(): failures.append(f"missing_workflow:{wf}")
        findings.append({"capacity_phases":[p.get("id") for p in phases]})
    elif mode=="NEGATIVE_EVIDENCE_DEDUP":
        taxonomy = {"PRUNED", "UNVERIFIED", "DATA_INSUFFICIENT"}
        evidence_text = json.dumps({
            "critical_quality_control": critical,
            "literature_policy": literature,
            "current_status": status,
            "active_registry": registry,
        }, ensure_ascii=False).upper()
        missing = sorted(k for k in taxonomy if k not in evidence_text)
        if missing:
            failures.append("negative_evidence_taxonomy_incomplete:" + ",".join(missing))
        findings.append({
            "negative_evidence_taxonomy_required": sorted(taxonomy),
            "missing_taxonomy_markers": missing,
        })
    else:
        if status.get("repository")!="DWR-debug/trading-agent-public": failures.append("status_repository_mismatch")
        if status.get("safety",{}).get("status")!="SAFE": findings.append({"status_safety":"not_explicitly_marked_safe"})
        h=root/"research/evidence/trading_agent_chat_handoff.json"
        if h.is_file():
            try: findings.append({"handoff_source_sha":load(h).get("source_master_sha")})
            except Exception as exc: failures.append(f"handoff_json:{type(exc).__name__}")
    receipt={"schema_version":"1.0","receipt_type":"s10_adaptive_mechanical_research_qa","source_commit":os.environ.get("GITHUB_SHA"),"runner_name":os.environ.get("RUNNER_NAME"),"runner_arch":os.environ.get("RUNNER_ARCH"),"run_number":run_no,"mode":mode,"status":"S10_ADAPTIVE_QA_PASSED" if not failures else "S10_ADAPTIVE_QA_FAILED","findings":findings,"failures":failures,"scientific_boundary":{"performance":False,"holdout_selection":False,"ranking":False,"selection":False,"parameter_search":False,"promotion":False,"live_execution":False},"safety":SAFETY}
    receipt["receipt_fingerprint"]=hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(receipt,ensure_ascii=False,sort_keys=True))
    return 0 if not failures else 1
if __name__=="__main__": raise SystemExit(main())
