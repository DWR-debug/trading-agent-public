"""Pre-performance structural robustness for the fixed Q218 replication bundle."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.q218_deterministic_performance_executor import validate_bundle_sources

TRIAL_ID = "T-2026-10-08-Q218-REPLICATION-01"


def fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def verify_bundle(bundle_path: Path, contract_path: Path) -> dict:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if bundle.get("trial_id") != TRIAL_ID or contract.get("replication_trial_id") != TRIAL_ID:
        raise RuntimeError("Q218 replication trial identity mismatch")
    expected = bundle.get("bundle_fingerprint")
    unsigned = dict(bundle)
    unsigned.pop("bundle_fingerprint", None)
    if not expected or fp(unsigned) != expected:
        raise RuntimeError("Q218 replication bundle self-fingerprint mismatch")
    effective = bundle_path.parent / "q218_effective_replication_contract.json"
    if not effective.is_file():
        raise RuntimeError("Q218 effective replication contract missing")
    effective_sha = hashlib.sha256(effective.read_bytes()).hexdigest()
    if bundle.get("contract_sha256") != effective_sha:
        raise RuntimeError("Q218 effective replication contract fingerprint mismatch")
    if bundle.get("executor_network_access") is not False:
        raise RuntimeError("Q218 replication robustness requires network-free executor boundary")
    for key in (
        "selection_used",
        "holdout_selection_used",
        "parameter_search",
        "threshold_search",
        "horizon_search",
        "asset_search",
        "variant_search",
    ):
        if bundle.get(key) is not False:
            raise RuntimeError(f"Q218 replication selection boundary invalid: {key}")
    from automation.q218_deterministic_performance_executor import validate_bundle_sources
    validate_bundle_sources(bundle, bundle_path.parent)
    return bundle


def expect_failure(label, fn):
    try:
        fn()
    except Exception as exc:
        return {"label": label, "rejected": True, "exception": type(exc).__name__}
    return {"label": label, "rejected": False, "exception": None}


def run(bundle_path: Path, contract_path: Path, output: Path) -> dict:
    bundle = verify_bundle(bundle_path, contract_path)
    probes = []
    with tempfile.TemporaryDirectory(prefix="q218-repl-robustness-") as td:
        work = Path(td)

        def mutated(mutator, label):
            case = work / label
            shutil.copytree(bundle_path.parent, case)
            p = case / "input_bundle_manifest.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            mutator(data, case)
            data["bundle_fingerprint"] = fp({k: v for k, v in data.items() if k != "bundle_fingerprint"})
            p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            probes.append(expect_failure(label, lambda: verify_bundle(p, contract_path)))

        mutated(lambda d, _: d.update({"contract_sha256": "0" * 64}), "contract_fingerprint_mismatch")

        def alter_doc(d, c):
            doc = d["documents"][0]
            path = c / str(doc["path"])
            path.write_bytes(path.read_bytes() + b"\nMUTATION")

        mutated(alter_doc, "document_bytes_mismatch")
        mutated(lambda d, _: d["market_bars"][0].update({"session": "2099-01-01"}), "future_market_bar_rejected")
        mutated(lambda d, _: d["documents"][1].update({"form": "8-K/A"}), "amendment_form_rejected")
        mutated(lambda d, _: d["events"].append(copy.deepcopy(d["events"][0])), "duplicate_event_identity_rejected")
        mutated(lambda d, _: d["documents"][0].update({"path": "../escape.html"}), "path_escape_rejected")

    result = {
        "schema_version": "1.0",
        "record_type": "q218_independent_replication_robustness",
        "candidate_id": "Q218",
        "trial_id": TRIAL_ID,
        "status": "PRE_PERFORMANCE_REPLICATION_ROBUSTNESS_COMPLETED",
        "bundle_fingerprint": bundle["bundle_fingerprint"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "research_only": True,
        "screen_is_descriptive_only": True,
        "no_post_hoc_tuning": True,
        "mutation_probes": probes,
        "all_mutations_rejected": all(p["rejected"] for p in probes),
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "parameter_search": False,
        "threshold_search": False,
        "horizon_search": False,
        "asset_search": False,
        "variant_search": False,
        "family_ranking": False,
        "promotion_decision": False,
        "performance_authorized": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    if not result["all_mutations_rejected"]:
        raise RuntimeError("Q218 replication mutation gate failed")
    result["receipt_fingerprint"] = fp(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = run(args.bundle, args.contract, args.output)
    print(json.dumps({
        "status": result["status"],
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
