"""Freeze Q218 replication SEC/market inputs using the unchanged primary freezer engine.

Only the frozen contract, issuer universe, and derived replication event population
are substituted. The primary Q218 freezer itself is not modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation import q218_performance_input_freeze as base_freeze

CONTRACT = ROOT / "research/governance/q218_independent_replication_contract_2026_10_08.json"
EVENT_GATE = ROOT / "research/evidence/q218_independent_replication_event_pair_latest.json"
TRIAL_ID = "T-2026-10-08-Q218-REPLICATION-01"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def make_effective_contract(work: Path) -> tuple[Path, str, dict]:
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    gate=json.loads(EVENT_GATE.read_text(encoding="utf-8"))
    if gate.get("all_pairing_valid") is not True:
        raise RuntimeError("Replication event gate not positive")
    pairs=[]
    for issuer,row in gate["issuer_results"].items():
        for pair in row["event_pairs"]:
            pairs.append([
                issuer,
                pair["ten_k_accession"],
                pair["item_2_02_8k_accession"],
                pair["ten_k_acceptance_datetime"],
                pair["item_2_02_8k_acceptance_datetime"],
            ])
    effective={
        "schema_version":"1.0",
        "record_type":"q218_effective_replication_contract",
        "candidate_id":"Q218",
        "trial_id":TRIAL_ID,
        "revision":1,
        "status":"FROZEN_EFFECTIVE_REPLICATION_CONTRACT",
        "upstream":{
            "independent_replication_contract_sha256":sha256_bytes(CONTRACT.read_bytes()),
            "event_gate_receipt_fingerprint":gate["receipt_fingerprint"],
            "fixed_window":contract["fixed_window"],
            "future_cutoff_utc":contract["future_cutoff_utc"],
        },
        "universe":{"issuers":contract["universe"]["issuers"]},
        "event_pair_population":pairs,
        "event_pair_rules":{
            "ten_k":"as-filed non-amended Form 10-K",
            "voluntary":"non-amended Form 8-K with Item 2.02",
            "pair_closure_clock":"max(ten_k_acceptance_datetime,item_2_02_8k_acceptance_datetime)",
            "future_data":"Any SEC document, market observation or metadata timestamp after 2026-10-05T23:59:59Z is rejected.",
        },
        "feature_construction":{
            "topic_hash_buckets":64,
            "features":[
                "topic_coverage_gap_mandatory_vs_voluntary",
                "omission_asymmetry_by_topic",
                "secondary_framing_gap"
            ],
            "learned_vocabulary":False,
            "parameter_tuning":False,
            "threshold_search":False,
            "horizon_search":False,
            "variant_search":False,
        },
        "upstream_primary_contract_sha256":"fd25e236d9c279ca8087ce022dee61a1ebcf7e37",
        "input_bundle":{"executor_network_access":False},
        "governance":{
            "selection_used":False,
            "holdout_selection_used":False,
            "parameter_search":False,
            "threshold_search":False,
            "horizon_search":False,
            "asset_search":False,
            "variant_search":False,
            "family_ranking":False,
            "promotion_decision":False,
            "performance_authorized":False,
        },
        "safety":contract["safety"],
    }
    path=work/"q218_effective_replication_contract.json"
    path.write_text(json.dumps(effective,indent=2,ensure_ascii=False)+"
",encoding="utf-8")
    return path,sha256_bytes(path.read_bytes()),effective


def freeze(output_root: Path, receipt_path: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="q218-repl-contract-") as td:
        effective_path, effective_sha, effective=make_effective_contract(Path(td))
        output_root.mkdir(parents=True, exist_ok=True)
        committed_effective = output_root / "q218_effective_replication_contract.json"
        committed_effective.write_bytes(effective_path.read_bytes())
        old_contract, old_trial_id = base_freeze.CONTRACT, base_freeze.TRIAL_ID
        try:
            base_freeze.CONTRACT=effective_path
            base_freeze.TRIAL_ID=TRIAL_ID
            receipt=base_freeze.freeze(output_root, output_root/"_base_receipt.json")
        finally:
            base_freeze.CONTRACT, base_freeze.TRIAL_ID = old_contract, old_trial_id
    if receipt["status"]!="INPUT_BUNDLE_FROZEN" or receipt["performance_authorized"] is not False:
        raise RuntimeError("Q218 replication input freeze failed boundary")
    result={
        "schema_version":"1.0",
        "record_type":"q218_independent_replication_input_bundle",
        "candidate_id":"Q218",
        "source_trial_id":"T-2026-10-08-Q218-PERFORMANCE-01",
        "replication_trial_id":TRIAL_ID,
        "status":"INPUT_BUNDLE_FROZEN",
        "base_contract_sha256":"fd25e236d9c279ca8087ce022dee61a1ebcf7e37",
        "replication_contract_sha256":sha256_bytes(CONTRACT.read_bytes()),
        "effective_contract_sha256":effective_sha,
        "event_gate_receipt_fingerprint":json.loads(EVENT_GATE.read_text(encoding="utf-8"))["receipt_fingerprint"],
        "bundle_fingerprint":receipt["bundle_fingerprint"],
        "event_count":receipt["event_count"],
        "document_count":receipt["document_count"],
        "market_bar_count":receipt["market_bar_count"],
        "source_response_count":receipt["source_response_count"],
        "bundle_manifest":"input_bundle_manifest.json",
        "selection_used":False,
        "holdout_evaluation":False,
        "performance_evaluation":False,
        "performance_authorized":False,
        "safety":json.loads(CONTRACT.read_text(encoding="utf-8"))["safety"],
    }
    receipt_path.parent.mkdir(parents=True,exist_ok=True)
    receipt_path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"
",encoding="utf-8")
    return result


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--output-root",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    args=p.parse_args()
    result=freeze(args.output_root,args.receipt)
    print(json.dumps({"status":result["status"],"bundle_fingerprint":result["bundle_fingerprint"],"event_count":result["event_count"]},sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
