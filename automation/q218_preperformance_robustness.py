"""Pre-performance robustness screen for the frozen Q218 executor and input bundle.

The screen is descriptive only. It does not calculate investment outcomes and
cannot mutate the frozen contract. Mutation probes must fail closed.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.q218_deterministic_performance_executor import (
    ROOT,
    TRIAL_ID,
    _verify_bundle,
    file_sha256,
    fp,
    validate_bundle_sources,
)

CONTRACT = ROOT / "research/governance/q218_performance_contract_2026_10_08.json"
EXECUTOR = ROOT / "automation/q218_deterministic_performance_executor.py"


def expect_failure(label: str, fn) -> dict[str, Any]:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - robustness probe records fail-closed exception class.
        return {"label": label, "rejected": True, "exception": type(exc).__name__}
    return {"label": label, "rejected": False, "exception": None}


def write_bundle(root: Path, bundle: dict[str, Any]) -> Path:
    path = root / "input_bundle_manifest.json"
    path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def resign(bundle: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(bundle)
    payload.pop("bundle_fingerprint", None)
    payload["bundle_fingerprint"] = fp(payload)
    return payload


def run(bundle_path: Path, output: Path) -> dict[str, Any]:
    bundle = _verify_bundle(bundle_path)
    validate_bundle_sources(bundle, bundle_path.parent)

    executor_sha = file_sha256(EXECUTOR)
    contract_sha = file_sha256(CONTRACT)

    probes: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="q218-robustness-") as td:
        work = Path(td)

        def mutated(mutator, label: str) -> None:
            case = work / label
            shutil.copytree(bundle_path.parent, case)
            path = case / "input_bundle_manifest.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            mutator(data, case)
            path.write_text(json.dumps(resign(data), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            probes.append(expect_failure(label, lambda: validate_bundle_sources(_verify_bundle(path), case)))

        mutated(
            lambda data, _case: data.update({"contract_sha256": "0" * 64}),
            "contract_fingerprint_mismatch",
        )

        def alter_document(data: dict[str, Any], case: Path) -> None:
            doc = data["documents"][0]
            path = case / str(doc["path"])
            path.write_bytes(path.read_bytes() + b"\nMUTATION")
        mutated(alter_document, "document_bytes_mismatch")

        mutated(
            lambda data, _case: data["market_bars"][0].update({"session": "2099-01-01"}),
            "future_market_bar_rejected",
        )
        mutated(
            lambda data, _case: data["documents"][1].update({"form": "8-K/A"}),
            "amendment_form_rejected",
        )
        mutated(
            lambda data, _case: data["events"].append(copy.deepcopy(data["events"][0])),
            "duplicate_event_identity_rejected",
        )
        mutated(
            lambda data, _case: data["documents"][0].update({"path": "../escape.html"}),
            "path_escape_rejected",
        )

    result = {
        "schema_version": "1.0",
        "record_type": "q218_pre_performance_robustness",
        "candidate_id": "Q218",
        "trial_id": TRIAL_ID,
        "status": "PRE_PERFORMANCE_ROBUSTNESS_COMPLETED",
        "bundle_fingerprint": bundle["bundle_fingerprint"],
        "contract_sha256": contract_sha,
        "executor_sha256": executor_sha,
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
        result["status"] = "PRE_PERFORMANCE_ROBUSTNESS_FAILED"
        raise RuntimeError("Q218 robustness mutation probe failed")
    result["receipt_fingerprint"] = fp(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.bundle, args.output)
    print(json.dumps({"trial_id": result["trial_id"], "status": result["status"], "receipt_fingerprint": result["receipt_fingerprint"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
