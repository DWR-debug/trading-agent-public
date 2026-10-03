"""Synthetic structural validator for the candidate-composition contract.

No market returns, holdout observations, performance metrics, or candidate
selection inputs are accepted. The compiler validates only component contracts
and deterministic composition semantics.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

REQUIRED = {
    "candidate_id",
    "decision_timestamp",
    "public_timestamp",
    "decision_session",
    "value",
    "source_fingerprint",
    "universe_fingerprint",
    "missing",
    "direction",
    "version",
    "family_lineage",
}

def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)

def fingerprint(obj: Any) -> str:
    return hashlib.sha256(_canonical(obj).encode()).hexdigest()

def validate_component(component: dict[str, Any], common: dict[str, Any]) -> None:
    missing = REQUIRED - set(component)
    if missing:
        raise RuntimeError(f"COMPONENT_MISSING_FIELDS:{sorted(missing)}")
    if component["missing"] not in (True, False):
        raise RuntimeError("COMPONENT_MISSINGNESS_INVALID")
    if component["direction"] not in ("LONG", "SHORT", "NEUTRAL"):
        raise RuntimeError("COMPONENT_DIRECTION_INVALID")
    if str(component["version"]) == "":
        raise RuntimeError("COMPONENT_VERSION_EMPTY")
    if component["universe_fingerprint"] != common["universe_fingerprint"]:
        raise RuntimeError("ENTITY_ALIGNMENT_FAIL")
    if component["decision_session"] != common["decision_session"]:
        raise RuntimeError("SESSION_ALIGNMENT_FAIL")
    if str(component["public_timestamp"]) > str(component["decision_timestamp"]):
        raise RuntimeError("PIT_ALIGNMENT_FAIL")
    for forbidden in ("holdout_return", "holdout_drawdown", "performance", "pnl", "future_return"):
        if forbidden in component:
            raise RuntimeError(f"PERFORMANCE_FIELD_PRESENT:{forbidden}")

def validate_bundle(components: list[dict[str, Any]], common: dict[str, Any]) -> dict[str, Any]:
    if not components:
        raise RuntimeError("EMPTY_COMPONENT_BUNDLE")
    for c in components:
        validate_component(c, common)
    lineages=[str(c["family_lineage"]) for c in components]
    if len(lineages) != len(set(lineages)):
        raise RuntimeError("DUPLICATE_FAMILY_LINEAGE")
    ids=[str(c["candidate_id"]) for c in components]
    if len(ids) != len(set(ids)):
        raise RuntimeError("DUPLICATE_COMPONENT_ID")
    return {
        "status":"COMPOSITION_COMPATIBLE",
        "component_ids":ids,
        "component_fingerprints":[str(c["source_fingerprint"]) for c in components],
        "family_lineages":lineages,
        "bundle_fingerprint":fingerprint({
            "components":sorted(
                [{"candidate_id":c["candidate_id"],"source_fingerprint":c["source_fingerprint"],"family_lineage":c["family_lineage"],"value":c["value"],"direction":c["direction"],"missing":c["missing"]} for c in components],
                key=lambda x:(x["candidate_id"],x["source_fingerprint"]),
            ),
            "decision_session":common["decision_session"],
            "universe_fingerprint":common["universe_fingerprint"],
        }),
        "governance":{"performance":False,"holdout":False,"selection":False,"ranking":False},
    }

def compose_sign_consensus(components: list[dict[str, Any]]) -> dict[str, Any]:
    if not components:
        raise RuntimeError("EMPTY_COMPONENT_BUNDLE")
    counts={d:0 for d in ("LONG","SHORT","NEUTRAL")}
    for c in components:
        counts[c["direction"]]+=1
    if counts["LONG"]>counts["SHORT"]:
        state="LONG_CONSENSUS"
    elif counts["SHORT"]>counts["LONG"]:
        state="SHORT_CONSENSUS"
    else:
        state="NO_CONSENSUS"
    return {"state":state,"counts":counts,"component_count":len(components)}

def compose_equal_weight_score(components: list[dict[str, Any]]) -> dict[str, Any]:
    usable=[float(c["value"]) for c in components if not c["missing"]]
    score=sum(usable)/len(usable) if usable else 0.0
    return {"score":score,"usable_component_count":len(usable),"total_component_count":len(components)}

def run_synthetic() -> dict[str, Any]:
    common={"decision_timestamp":"2026-10-02T12:00:00Z","decision_session":"2026-10-02","universe_fingerprint":"U-SYN-01"}
    components=[
        {"candidate_id":"SEC-13F","decision_timestamp":common["decision_timestamp"],"public_timestamp":"2026-10-02T10:00:00Z","decision_session":common["decision_session"],"value":1.0,"source_fingerprint":"FP-SEC","universe_fingerprint":common["universe_fingerprint"],"missing":False,"direction":"LONG","version":"v1","family_lineage":"13F"},
        {"candidate_id":"TREASURY","decision_timestamp":common["decision_timestamp"],"public_timestamp":"2026-10-02T11:00:00Z","decision_session":common["decision_session"],"value":-1.0,"source_fingerprint":"FP-TSY","universe_fingerprint":common["universe_fingerprint"],"missing":False,"direction":"SHORT","version":"v1","family_lineage":"TREASURY"},
        {"candidate_id":"CFTC-TFF","decision_timestamp":common["decision_timestamp"],"public_timestamp":"2026-10-02T09:00:00Z","decision_session":common["decision_session"],"value":0.0,"source_fingerprint":"FP-CFTC","universe_fingerprint":common["universe_fingerprint"],"missing":False,"direction":"NEUTRAL","version":"v1","family_lineage":"CFTC-TFF"},
    ]
    base=validate_bundle(components,common)
    reversed_bundle=validate_bundle(list(reversed(components)),common)
    return {
        "schema_version":"1.0",
        "task_id":"Q-2026-10-03-118-COMPOSITION-STRUCTURAL",
        "status":"COMPOSITION_STRUCTURAL_VALIDATION_COMPLETED" if base["bundle_fingerprint"]==reversed_bundle["bundle_fingerprint"] else "COMPOSITION_STRUCTURAL_VALIDATION_FAILED",
        "base":base,
        "order_invariance":base["bundle_fingerprint"]==reversed_bundle["bundle_fingerprint"],
        "consensus":compose_sign_consensus(components),
        "equal_weight":compose_equal_weight_score(components),
        "governance":{"performance":False,"holdout":False,"selection":False,"ranking":False,"parameter_search":False,"threshold_search":False,"horizon_search":False,"asset_search":False,"automatic_promotion":False},
        "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
    }

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    result=run_synthetic()
    result["receipt_fingerprint"]=fingerprint(result)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"receipt_fingerprint":result["receipt_fingerprint"]}))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
