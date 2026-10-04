"""Ex-ante Research OS scheduler; performance and holdout data are forbidden inputs."""
from __future__ import annotations
import argparse,json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from automation.research_os_evidence_bus import ROOT,load_registry,source_index,fingerprint
QUALITY_POLICY_PATH = ROOT / "research/governance/critical_research_quality_control.json"
S10_PRESENCE_MAX_AGE = timedelta(hours=6)
TRACKS=[
{"id":"ROS-TRACK-C-SEC-FINRA-SHORT-FLOW","name":"SEC/FINRA short-flow convergence","source_ids":["SRC-SEC-FTD","SRC-FINRA-SI","SRC-FINRA-REGSHO"],"cheap_falsifiability":.92,"mechanism_novelty_distance":.90,"expected_reproducibility":.88,"resource_cost":.18,"lane":"deterministic_frontier","next_gate":"source_and_release_schedule_probe"},
{"id":"ROS-TRACK-D-MACRO-VINTAGE","name":"Macro-vintage regime layer","source_ids":["SRC-FRED-ALFRED","SRC-BLS","SRC-EIA","SRC-BIS","SRC-TREASURY"],"cheap_falsifiability":.84,"mechanism_novelty_distance":.86,"expected_reproducibility":.91,"resource_cost":.24,"lane":"deterministic_frontier","next_gate":"vintage_and_release_time_probe"},
{"id":"ROS-TRACK-E-RETAIL-ATTENTION","name":"Retail-attention shock lattice","source_ids":["SRC-NDAQ-RETAIL10","SRC-NDAQ-RTAT10","SRC-GDELT","SRC-SEC-EDGAR"],"cheap_falsifiability":.80,"mechanism_novelty_distance":.94,"expected_reproducibility":.70,"resource_cost":.28,"lane":"deterministic_frontier","next_gate":"publication_time_and_selection_bias_probe"},
{"id":"ROS-TRACK-F-AGENT-GOVERNANCE","name":"Agent governance fabric","source_ids":["SRC-OPENBB-ODP"],"cheap_falsifiability":.95,"mechanism_novelty_distance":.93,"expected_reproducibility":.89,"resource_cost":.12,"lane":"adversarial","next_gate":"contract_and_sandbox_audit"},
{"id":"ROS-TRACK-G-COMMUNITY-DISCOVERY","name":"Community-data discovery quarantine","source_ids":["SRC-HF-COMMUNITY"],"cheap_falsifiability":.76,"mechanism_novelty_distance":.98,"expected_reproducibility":.55,"resource_cost":.34,"lane":"adversarial","next_gate":"provenance_license_version_pit_audit"},
{"id":"ROS-TRACK-H-TREASURY-DEMAND-SHAPE","name":"Treasury auction demand-shape state","source_ids":["SRC-TREASURY"],"cheap_falsifiability":.91,"mechanism_novelty_distance":.87,"expected_reproducibility":.93,"resource_cost":.14,"lane":"deterministic_frontier","next_gate":"historical_archive_field_completeness_pit_probe"},{"id":"ROS-TRACK-I-CFTC-POSITIONING","name":"CFTC TFF institutional positioning divergence","source_ids":["SRC-CFTC-TFF"],"cheap_falsifiability":.88,"mechanism_novelty_distance":.84,"expected_reproducibility":.95,"resource_cost":.12,"lane":"deterministic_frontier","next_gate":"historical_archive_release_date_pit_probe"},{"id":"ROS-TRACK-Q194-THERAPEUTIC-SUBSTITUTION","name":"Therapeutic substitution pressure from drug shortages","source_ids":["SRC-FDA-SHORTAGES","SRC-FDA-ORANGEBOOK"],"cheap_falsifiability":0.95,"mechanism_novelty_distance":0.97,"expected_reproducibility":0.88,"resource_cost":0.22,"lane":"deterministic_frontier","next_gate":"historical_shortage_vintage_and_orange_book_vintage_probe"},
{"id":"ROS-TRACK-Q195-EPA-ESCALATION","name":"EPA inspection-to-enforcement escalation state","source_ids":["SRC-EPA-ECHO"],"cheap_falsifiability":0.92,"mechanism_novelty_distance":0.93,"expected_reproducibility":0.90,"resource_cost":0.20,"lane":"adversarial","next_gate":"historical_echo_vintage_and_facility_mapping_probe"},]
def pit_prior(v:str)->float:
    v=v.lower()
    if "very_high" in v:return 1.
    if "high" in v:return .90
    if "medium_high" in v:return .82
    if "medium" in v:return .68
    if "discovery_only" in v:return .35
    if "adapter" in v:return .55
    return .50
def quality(access:str,pit:str)->float:
    base=1. if access.startswith("public") else .90 if access.startswith("free") else .78
    return min(1.,.55*base+.45*pit_prior(pit))
def score(track:dict[str,Any],sources:dict[str,dict[str,Any]])->dict[str,Any]:
    items=[sources[s] for s in track["source_ids"]]
    pit=sum(pit_prior(str(x.get("pit_fit",""))) for x in items)/len(items)
    q=sum(quality(str(x.get("access","")),str(x.get("pit_fit",""))) for x in items)/len(items)
    benefit=(.24*track["cheap_falsifiability"]+.18*q+.16*pit+.24*track["mechanism_novelty_distance"]+.18*track["expected_reproducibility"])
    out=dict(track); out.update({"source_quality_prior":round(q,6),"pit_feasibility_prior":round(pit,6),"information_gain_per_compute_prior":round(benefit/(.10+track["resource_cost"]),6),"holdout_used":False,"performance_evaluated":False,"candidate_selected":False}); return out
S10_ACCEPTANCE_PATH = ROOT / "research/runs/self_hosted/autonomous/s10_acceptance_receipt.json"
S10_OS_STATUS_PATH = ROOT / "ops/s10_runtime_status.json"

def _s10_resource_state() -> dict[str, Any]:
    result = {
        "id": "S10",
        "agent_runtime_id": "AGENT-S10",
        "role": "adversarial_qa_only",
        "activation_gate": "S10_UTILITY_ACCEPTED",
        "eligible": False,
        "receipt_status": "NOT_PRESENT",
        "receipt_sha256": None,
        "formal_evidence_allowed": False,
        "performance_authorization": False,
        "candidate_selection": False,
        "candidate_ranking": False,
        "promotion": False,
        "presence_signal": "none",
        "presence_signal_fresh": False,
    }
    try:
        import hashlib
        source_path = S10_OS_STATUS_PATH if S10_OS_STATUS_PATH.is_file() else S10_ACCEPTANCE_PATH
        if not source_path.is_file():
            return result
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        result["receipt_status"] = str(payload.get("receipt_status", payload.get("status", "INVALID")))
        result["receipt_sha256"] = hashlib.sha256(source_path.read_bytes()).hexdigest()
        result["status_source"] = "canonical_os_status" if source_path == S10_OS_STATUS_PATH else "same_run_local_receipt"

        if source_path == S10_OS_STATUS_PATH:
            accepted = payload.get("eligible") is True and result["receipt_status"] == "S10_UTILITY_ACCEPTED"
            generated = payload.get("generated_at_utc") or payload.get("workflow_run_updated_at")
            try:
                observed = datetime.fromisoformat(str(generated).replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                fresh = now - observed <= S10_PRESENCE_MAX_AGE and observed <= now + timedelta(minutes=5)
            except (TypeError, ValueError):
                fresh = False
            result["presence_signal"] = "fresh_successful_s10_run" if fresh else "stale_or_unparseable_s10_run"
            result["presence_signal_fresh"] = fresh
            result["eligible"] = accepted and fresh
        else:
            result["presence_signal"] = "same_run_s10_receipt"
            result["presence_signal_fresh"] = True
            result["eligible"] = result["receipt_status"] == "S10_UTILITY_ACCEPTED"
    except (OSError, json.JSONDecodeError, TypeError, OverflowError):
        result["receipt_status"] = "INVALID"
        result["presence_signal"] = "invalid"
    return result

def build_plan(*,run_number:int|None=None)->dict[str,Any]:
    registry=load_registry(); sources=source_index(registry)
    # Reload governance policy for every scheduler invocation. This prevents a
    # long-lived interpreter/import cache from using a stale research policy.
    quality_policy = json.loads(QUALITY_POLICY_PATH.read_text(encoding="utf-8"))
    min_novelty = float(quality_policy["orthogonal_search"].get("minimum_scheduler_novelty_distance", 0.80))
    candidate_tracks = [
        t for t in TRACKS if float(t["mechanism_novelty_distance"]) >= min_novelty
    ]
    tracks = sorted(
        (score(t, sources) for t in candidate_tracks),
        key=lambda x: (-x["information_gain_per_compute_prior"], x["id"]),
    )
    assignments=[]; used=set()
    for lane in ("deterministic_frontier","adversarial"):
        c=[x for x in tracks if x["lane"]==lane and x["id"] not in used]
        if c:
            used.add(c[0]["id"]); assignments.append({"lane":lane,"track_id":c[0]["id"],"reason":"ex_ante_capability_prior","performance_authorized":False})
    s10 = _s10_resource_state()
    plan={"schema_version":1,"research_priority":"ORTHOGONAL_INFORMATION_FIRST_WITH_EARLY_ROBUSTNESS","research_os_version":registry["research_os_version"],"plan_type":"resource_schedule","run_number":run_number,"basis":"information_gain_per_compute_prior + cheap_falsifiability + source_quality + PIT_feasibility + novelty + reproducibility","forbidden_inputs":registry["resource_scheduler"]["forbidden_axes"],"tracks":tracks,"assignments":assignments,"agent_resources":[s10],"quality_controls":{"orthogonal_only":True,"minimum_scheduler_novelty_distance":min_novelty,"early_robustness_required_before_future_performance_authorization":True,"immediate_replication_required_after_full_formal_pass":True,"candidate_robustness_gate_required_before_any_formal_phase":quality_policy["candidate_robustness_gate"]["required_before_any_formal_phase"]},
    "resource_policy":{"paid_resources":False,"holdout_used":False,"automatic_promotion":False,"performance_authorization":False,"maximum_deterministic_lanes":2,"adversarial_lane_reserved":True}}
    plan["fingerprint"]=fingerprint(plan); return plan
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=Path("research/runs/self_hosted/research_os/resource_schedule.json")); p.add_argument("--run-number",type=int); a=p.parse_args()
    out=build_plan(run_number=a.run_number); path=a.output if a.output.is_absolute() else ROOT/a.output; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"assignments":out["assignments"],"fingerprint":out["fingerprint"]},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
