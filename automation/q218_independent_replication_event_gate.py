"""Derive the predeclared Q218 fresh-symbol event population.

This wrapper executes the unchanged Q218 deterministic SEC pairing algorithm with
only the four symbols declared in the frozen replication contract. It reads no
market outcomes and does not inspect the primary performance values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation import q218_sec_event_pair_lineage_gate as base_gate

CONTRACT = ROOT / "research/governance/q218_independent_replication_contract_2026_10_08.json"
REPLICATION_TRIAL_ID = "T-2026-10-08-Q218-REPLICATION-01"


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def build(output: Path) -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("status") != "FROZEN_INDEPENDENT_REPLICATION_CONTRACT":
        raise RuntimeError("Q218 replication contract is not frozen")
    issuers = {str(k): str(v) for k, v in contract["universe"]["issuers"].items()}
    if list(issuers) != ["GOOGL", "META", "ORCL", "PFE"]:
        raise RuntimeError("Q218 replication issuer order/set drifted")

    old_issuers, old_start, old_end = base_gate.ISSUERS, base_gate.START, base_gate.END
    try:
        base_gate.ISSUERS = issuers
        base_gate.START = contract["fixed_window"]["start"]
        base_gate.END = contract["fixed_window"]["end"]
        temp = output.with_name(output.name + ".base")
        base = base_gate.run(temp)
        temp.unlink(missing_ok=True)
    finally:
        base_gate.ISSUERS, base_gate.START, base_gate.END = old_issuers, old_start, old_end

    if base.get("candidate_id") != "Q218" or base.get("all_pairing_valid") is not True:
        raise RuntimeError("Q218 replication event gate is not positive")
    if base.get("scientific_evidence") is not False:
        raise RuntimeError("Replication event gate crossed scientific boundary")
    if base.get("performance_authorization") is not False or base.get("live_execution") is not False:
        raise RuntimeError("Replication event gate crossed authorization boundary")

    result = {
        "schema_version":"1.0",
        "record_type":"q218_independent_replication_event_pair_gate",
        "candidate_id":"Q218",
        "source_trial_id":"T-2026-10-08-Q218-PERFORMANCE-01",
        "replication_trial_id":REPLICATION_TRIAL_ID,
        "contract_path":str(CONTRACT.relative_to(ROOT)).replace("\","/"),
        "contract_sha256":hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "fixed_window":contract["fixed_window"],
        "issuer_set":issuers,
        "pairing_rule":base["pairing_rule"],
        "issuer_results":base["issuer_results"],
        "issuer_count":base["issuer_count"],
        "total_event_pairs":sum(v["event_pair_count"] for v in base["issuer_results"].values()),
        "all_pairing_valid":base["all_pairing_valid"],
        "primary_performance_read":False,
        "scientific_evidence":False,
        "performance_authorization":False,
        "holdout_selection":False,
        "ranking":False,
        "tuning":False,
        "promotion":False,
        "live_execution":False,
        "safety":contract["safety"],
        "next_gate":"INDEPENDENT_REPLICATION_INPUT_FREEZE",
    }
    result["receipt_fingerprint"]=fingerprint(result)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"
",encoding="utf-8")
    return result


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=build(args.output)
    print(json.dumps({"status":"PASS","total_event_pairs":result["total_event_pairs"],"receipt_fingerprint":result["receipt_fingerprint"]},sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
